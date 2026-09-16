#!/usr/bin/env python3
"""Generate weekly investment report (Mon-Fri) and send Feishu summary."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import json
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_notifier import FeishuNotifier
from src.optimization.regime_detector import RegimeDetector
from src.utils.date_utils import generate_date_range
from src.utils.logger import setup_logger


def _week_range_monday_friday(anchor: date | None = None) -> tuple[str, str, str]:
    d = anchor or datetime.now().date()
    monday = d - timedelta(days=d.weekday())
    friday = monday + timedelta(days=4)
    end_day = min(friday, d)
    week_label = f"第{monday.isocalendar().week}周"
    return monday.isoformat(), end_day.isoformat(), week_label


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _signal_cn(signal: str) -> str:
    mapping = {"short_term": "短线策略", "swing": "波段策略", "stable": "稳健策略"}
    return mapping.get(signal, signal)


def _signal_returns(db: DatabaseManager, start_date: str, end_date: str) -> list[dict[str, Any]]:
    rows = db.fetch_all(
        """
        SELECT s.date, s.code, s.signal, s.score, s.reason,
               d0.close AS entry_close,
               (
                 SELECT b1.close
                 FROM stock_daily_bar b1
                 WHERE b1.code = s.code AND b1.date > s.date AND b1.date <= ?
                 ORDER BY b1.date ASC
                 LIMIT 1
               ) AS next_close,
               (
                 SELECT b2.close
                 FROM stock_daily_bar b2
                 WHERE b2.code = s.code AND b2.date >= s.date AND b2.date <= ?
                 ORDER BY b2.date DESC
                 LIMIT 1
               ) AS week_last_close
        FROM daily_signals s
        LEFT JOIN stock_daily_bar d0 ON d0.code = s.code AND d0.date = s.date
        WHERE s.date BETWEEN ? AND ?
        ORDER BY s.date, s.signal, s.score DESC
        """,
        (end_date, end_date, start_date, end_date),
    )

    out: list[dict[str, Any]] = []
    for r in rows:
        entry = r.get("entry_close")
        if entry is None:
            continue
        entry_f = _safe_float(entry)
        if entry_f <= 0:
            continue
        exit_price = r.get("next_close") if r.get("next_close") is not None else r.get("week_last_close")
        if exit_price is None:
            continue
        ret = (_safe_float(exit_price) - entry_f) / entry_f
        out.append({**r, "return_pct": ret})
    return out


def _strategy_stats(signal_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {"short_term": [], "swing": [], "stable": []}
    for r in signal_rows:
        grouped.setdefault(str(r.get("signal")), []).append(r)

    stats: dict[str, dict[str, Any]] = {}
    for signal, rows in grouped.items():
        if not rows:
            stats[signal] = {
                "count": 0,
                "up": 0,
                "win_rate": 0.0,
                "avg_return": 0.0,
                "best": None,
                "worst": None,
            }
            continue

        sorted_rows = sorted(rows, key=lambda x: _safe_float(x.get("return_pct")))
        best = sorted_rows[-1]
        worst = sorted_rows[0]
        up = len([r for r in rows if _safe_float(r.get("return_pct")) > 0])
        avg = sum(_safe_float(r.get("return_pct")) for r in rows) / len(rows)
        stats[signal] = {
            "count": len(rows),
            "up": up,
            "win_rate": up / len(rows),
            "avg_return": avg,
            "best": best,
            "worst": worst,
        }
    return stats


def _factor_insight(signal_rows: list[dict[str, Any]]) -> dict[str, str]:
    buckets = {
        "新闻因子": ["新闻", "舆情", "情绪"],
        "基本面因子": ["基本面", "业绩", "估值", "盈利"],
        "行业因子": ["行业", "景气", "产业", "赛道"],
    }
    ret_values: dict[str, list[float]] = {k: [] for k in buckets}

    for r in signal_rows:
        reason = str(r.get("reason") or "")
        ret = _safe_float(r.get("return_pct"))
        for name, keywords in buckets.items():
            if any(k in reason for k in keywords):
                ret_values[name].append(ret)

    insight: dict[str, str] = {}
    for name, values in ret_values.items():
        if not values:
            insight[name] = "数据不足"
            continue
        avg = sum(values) / len(values)
        insight[name] = "表现良好" if avg >= 0 else "需改进"
    return insight


def _trade_stats(db: DatabaseManager, start_date: str, end_date: str) -> dict[str, Any]:
    trades = db.fetch_all(
        """
        SELECT trade_date, code, name, side, quantity, price, amount, fee,
               executed_by_model, deviation_reason, strategy_tag
        FROM real_trades
        WHERE trade_date BETWEEN ? AND ? AND COALESCE(status, 'active')='active'
        ORDER BY trade_date, trade_id
        """,
        (start_date, end_date),
    )

    buys = [t for t in trades if str(t.get("side", "")).lower() == "buy"]
    sells = [t for t in trades if str(t.get("side", "")).lower() == "sell"]

    def _amt(row: dict[str, Any]) -> float:
        amount = _safe_float(row.get("amount"))
        if amount > 0:
            return amount
        return _safe_float(row.get("price")) * _safe_float(row.get("quantity"))

    buy_cash = sum(_amt(t) + _safe_float(t.get("fee")) for t in buys)
    sell_cash = sum(_amt(t) - _safe_float(t.get("fee")) for t in sells)
    weekly_pnl = sell_cash - buy_cash

    return {
        "trades": trades,
        "trade_count": len(trades),
        "buy_count": len(buys),
        "sell_count": len(sells),
        "weekly_pnl": weekly_pnl,
    }


def _position_stats(db: DatabaseManager) -> tuple[list[dict[str, Any]], dict[str, float]]:
    positions = db.fetch_all(
        """
        SELECT code, name, quantity, cost_price, market_price,
               (quantity * cost_price) AS cost,
               (quantity * market_price) AS market_value,
               (quantity * market_price - quantity * cost_price) AS profit
        FROM real_positions
        WHERE status='active'
        ORDER BY code
        """
    )

    total_cost = sum(_safe_float(p.get("cost")) for p in positions)
    total_market = sum(_safe_float(p.get("market_value")) for p in positions)
    total_profit = total_market - total_cost
    cumulative_return_pct = (total_profit / total_cost * 100.0) if total_cost > 0 else 0.0

    return positions, {
        "total_cost": total_cost,
        "total_market": total_market,
        "total_profit": total_profit,
        "cumulative_return_pct": cumulative_return_pct,
    }


def _weekly_return_from_equity(db: DatabaseManager, start_date: str, end_date: str) -> float:
    def _equity(on_date: str) -> float:
        row = db.fetch_one(
            """
            SELECT SUM(p.quantity * b.close) AS v
            FROM real_positions p
            LEFT JOIN stock_daily_bar b ON b.code=p.code AND b.date=?
            WHERE p.status='active'
            """,
            (on_date,),
        )
        return _safe_float((row or {}).get("v"))

    v1 = _equity(start_date)
    v2 = _equity(end_date)
    if v1 <= 0:
        return 0.0
    return (v2 / v1 - 1.0) * 100.0


def _execution_analysis(db: DatabaseManager, start_date: str, end_date: str, trades: list[dict[str, Any]]) -> dict[str, Any]:
    rec_codes = {
        r["code"]
        for r in db.fetch_all("SELECT DISTINCT code FROM daily_signals WHERE date BETWEEN ? AND ?", (start_date, end_date))
    }
    buy_trades = [t for t in trades if str(t.get("side", "")).lower() == "buy"]
    by_rec = [t for t in buy_trades if t.get("code") in rec_codes]
    by_manual = [t for t in buy_trades if t.get("code") not in rec_codes]
    execution_rate = len(by_rec) / len(buy_trades) if buy_trades else 0.0
    return {
        "recommended_exec": len(by_rec),
        "manual_exec": len(by_manual),
        "execution_rate": execution_rate,
    }


def _market_overview(db: DatabaseManager, start_date: str, end_date: str) -> tuple[str, str]:
    start = db.fetch_one(
        """
        SELECT close
        FROM stock_daily_bar
        WHERE code IN ('INDEX:sh000001', 'INDEX:000001') AND date=?
        ORDER BY CASE code WHEN 'INDEX:sh000001' THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (start_date,),
    )
    end = db.fetch_one(
        """
        SELECT close
        FROM stock_daily_bar
        WHERE code IN ('INDEX:sh000001', 'INDEX:000001') AND date=?
        ORDER BY CASE code WHEN 'INDEX:sh000001' THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (end_date,),
    )
    if not start or not end:
        return "数据缺失", "震荡市"

    s = _safe_float(start.get("close"))
    e = _safe_float(end.get("close"))
    if s <= 0:
        return "数据缺失", "震荡市"
    pct = (e / s - 1.0) * 100.0
    if pct >= 2.0:
        regime = "牛市"
    elif pct <= -2.0:
        regime = "熊市"
    else:
        regime = "震荡市"
    return f"{pct:+.2f}% ({s:.2f} → {e:.2f})", regime


def _build_report(
    week_label: str,
    start_date: str,
    end_date: str,
    signal_rows: list[dict[str, Any]],
    strategy_stats: dict[str, dict[str, Any]],
    top5: list[dict[str, Any]],
    factor_insight: dict[str, str],
    trade_stats: dict[str, Any],
    execution: dict[str, Any],
    positions: list[dict[str, Any]],
    position_summary: dict[str, float],
    weekly_return_pct: float,
    market_perf: str,
    market_regime: str,
    market_suggestion: str,
    optimize_done: bool,
    optimize_text: str,
) -> str:
    lines: list[str] = [
        f"# 投资周报 - {week_label} ({start_date} ~ {end_date})",
        "",
        "## 📊 本周市场概况",
        f"- 上证指数涨跌幅: {market_perf}",
        f"- 市场制度: {market_regime}",
        "",
        "## 🎯 量化决策复盘",
        "",
        "### 策略推荐表现",
        "| 策略类型 | 推荐数量 | 上涨数量 | 胜率 | 平均收益 | 最佳/最差 |",
        "|---------|---------|---------|------|---------|----------|",
    ]

    for signal in ["short_term", "swing", "stable"]:
        s = strategy_stats[signal]
        best = s["best"]
        worst = s["worst"]
        if best and worst:
            best_text = f"{best['code']} {(_safe_float(best['return_pct']) * 100):+.2f}%"
            worst_text = f"{worst['code']} {(_safe_float(worst['return_pct']) * 100):+.2f}%"
        else:
            best_text, worst_text = "-", "-"
        lines.append(
            f"| {_signal_cn(signal)} | {s['count']} | {s['up']} | {s['win_rate'] * 100:.1f}% | {s['avg_return'] * 100:+.2f}% | {best_text} / {worst_text} |"
        )

    lines.extend(["", "### Top 5 推荐股票"])
    if top5:
        for i, r in enumerate(top5, 1):
            lines.append(
                f"{i}. {r['code']} - 推荐分数{_safe_float(r.get('score')):.1f}，实际涨幅{_safe_float(r.get('avg_ret')) * 100:+.2f}%"
            )
    else:
        lines.append("1. 本周无可用推荐数据")

    lines.extend([
        "",
        "### 因子表现分析",
        f"- 新闻因子：{factor_insight.get('新闻因子', '数据不足')}",
        f"- 基本面因子：{factor_insight.get('基本面因子', '数据不足')}",
        f"- 行业因子：{factor_insight.get('行业因子', '数据不足')}",
        "",
        "## 💼 个人操作复盘",
        "",
        "### 交易统计",
        f"- 本周交易次数：{trade_stats['trade_count']}次（买入{trade_stats['buy_count']}次，卖出{trade_stats['sell_count']}次）",
        f"- 本周盈亏：{trade_stats['weekly_pnl']:+,.2f}元",
        f"- 本周收益率：{weekly_return_pct:+.2f}%",
        f"- 累计收益率：{position_summary['cumulative_return_pct']:+.2f}%",
        "",
        "### 交易明细",
        "| 日期 | 股票 | 操作 | 价格 | 数量 | 盈亏 |",
        "|------|------|------|------|------|------|",
    ])

    if trade_stats["trades"]:
        for t in trade_stats["trades"]:
            pnl_text = "-"
            if str(t.get("side", "")).lower() == "sell":
                pnl_text = f"+{_safe_float(t.get('amount')) - _safe_float(t.get('fee')):,.2f}"
            elif str(t.get("side", "")).lower() == "buy":
                pnl_text = f"-{_safe_float(t.get('amount')) + _safe_float(t.get('fee')):,.2f}"
            lines.append(
                f"| {t.get('trade_date', '')} | {t.get('code', '')} {t.get('name', '') or ''} | {t.get('side', '')} | {_safe_float(t.get('price')):.2f} | {_safe_float(t.get('quantity')):.0f} | {pnl_text} |"
            )
    else:
        lines.append("| - | - | - | - | - | - |")

    lines.extend([
        "",
        "### 执行分析",
        f"- 按推荐操作：{execution['recommended_exec']}次",
        f"- 自主决策：{execution['manual_exec']}次",
        f"- 执行率：{execution['execution_rate'] * 100:.1f}%",
        "",
        "### 当前持仓",
        "| 股票 | 成本价 | 现价 | 持仓量 | 盈亏 | 收益率 |",
        "|------|--------|------|--------|------|--------|",
    ])

    for p in positions:
        cost = _safe_float(p.get("cost"))
        profit = _safe_float(p.get("profit"))
        ret = (profit / cost * 100.0) if cost > 0 else 0.0
        lines.append(
            f"| {p.get('code', '')} {p.get('name', '')} | {_safe_float(p.get('cost_price')):.2f} | {_safe_float(p.get('market_price')):.2f} | {_safe_float(p.get('quantity')):.0f} | {profit:+,.2f} | {ret:+.2f}% |"
        )

    lines.extend([
        "",
        "## 💡 下周策略建议",
        f"- 市场研判：{market_regime}，建议按{market_suggestion}进行仓位管理",
        "- 操作建议：优先执行模型高分信号，减少盘中临时追涨交易",
        "- 风险提示：单票仓位控制在20%以内，亏损接近止损位时严格执行纪律",
        "",
        "## 📈 参数优化记录",
        f"- 本周是否进行了参数优化：{'是' if optimize_done else '否'}",
        f"- 优化结果：{optimize_text}",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    settings = load_app_settings()
    logger = setup_logger("weekly_report", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    notifier = FeishuNotifier(db=db, log_level=settings.log_level)

    start_date, end_date, week_label = _week_range_monday_friday()

    # Keep Monday-Friday only.
    weekdays = generate_date_range(start_date, end_date, trading_days_only=True)
    if weekdays:
        start_date, end_date = weekdays[0], weekdays[-1]

    signal_rows = _signal_returns(db, start_date, end_date)
    signal_days = db.fetch_all(
        "SELECT date, COUNT(1) AS cnt FROM daily_signals WHERE date BETWEEN ? AND ? GROUP BY date ORDER BY date",
        (start_date, end_date),
    )
    strategy_stats = _strategy_stats(signal_rows)

    by_code: dict[str, dict[str, Any]] = {}
    for r in signal_rows:
        code = str(r.get("code"))
        by_code.setdefault(code, {"code": code, "score_sum": 0.0, "cnt": 0, "ret_sum": 0.0})
        by_code[code]["score_sum"] += _safe_float(r.get("score"))
        by_code[code]["ret_sum"] += _safe_float(r.get("return_pct"))
        by_code[code]["cnt"] += 1

    top5 = []
    for v in by_code.values():
        cnt = max(int(v["cnt"]), 1)
        top5.append({"code": v["code"], "score": v["score_sum"] / cnt, "avg_ret": v["ret_sum"] / cnt})
    top5.sort(key=lambda x: x["avg_ret"], reverse=True)
    top5 = top5[:5]

    factor_insight = _factor_insight(signal_rows)
    trade_stats = _trade_stats(db, start_date, end_date)
    positions, position_summary = _position_stats(db)
    weekly_return_pct = _weekly_return_from_equity(db, start_date, end_date)
    execution = _execution_analysis(db, start_date, end_date, trade_stats["trades"])
    market_perf, market_regime = _market_overview(db, start_date, end_date)
    market_suggestion = RegimeDetector(db).detect_current_regime().description

    opt = db.fetch_one(
        """
        SELECT optimization_date, strategy_type, best_score
        FROM optimization_history
        WHERE optimization_date BETWEEN ? AND ?
        ORDER BY optimization_date DESC, id DESC
        LIMIT 1
        """,
        (start_date, end_date),
    )
    optimize_done = opt is not None
    optimize_text = (
        f"{opt['optimization_date']} 执行，策略={opt['strategy_type']}，best_score={_safe_float(opt['best_score']):.4f}"
        if opt
        else "本周未执行参数优化"
    )

    markdown = _build_report(
        week_label=week_label,
        start_date=start_date,
        end_date=end_date,
        signal_rows=signal_rows,
        strategy_stats=strategy_stats,
        top5=top5,
        factor_insight=factor_insight,
        trade_stats=trade_stats,
        execution=execution,
        positions=positions,
        position_summary=position_summary,
        weekly_return_pct=weekly_return_pct,
        market_perf=market_perf,
        market_regime=market_regime,
        market_suggestion=market_suggestion,
        optimize_done=optimize_done,
        optimize_text=optimize_text,
    )

    out_dir = PROJECT_ROOT / "obsidian" / "02_周报"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{datetime.now().year}-{datetime.now().isocalendar().week:02d}_投资周报.md"
    report_path.write_text(markdown, encoding="utf-8")

    win = sum(1 for r in signal_rows if _safe_float(r.get("return_pct")) > 0)
    signal_win_rate = (win / len(signal_rows)) if signal_rows else 0.0
    metrics = {
        "signal_count": len(signal_rows),
        "signal_win_rate": signal_win_rate,
        "trade_count": trade_stats["trade_count"],
        "buy_count": trade_stats["buy_count"],
        "sell_count": trade_stats["sell_count"],
        "weekly_return_pct": weekly_return_pct,
        "cumulative_return_pct": position_summary["cumulative_return_pct"],
        "execution_rate": execution["execution_rate"],
    }

    notify_ok = notifier.send_weekly_report(
        week_label=week_label,
        start_date=start_date,
        end_date=end_date,
        report_path=str(report_path),
        metrics=metrics,
    )

    summary = {
        "week_label": week_label,
        "start_date": start_date,
        "end_date": end_date,
        "report_path": str(report_path),
        "metrics": metrics,
        "signal_days": signal_days,
        "feishu_sent": notify_ok,
    }

    out = PROJECT_ROOT / "logs" / f"weekly_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Weekly report generated: %s", summary)
    print(f"周报已生成: {report_path}")


if __name__ == "__main__":
    main()
