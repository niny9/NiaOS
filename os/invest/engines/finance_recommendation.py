#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from claw_runtime import ensure_dir, write_json


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPORT_DIR = Path("/Users/niny/Downloads/ExportBlock-b7301589-de8e-4342-b95e-e620402d4bd5-Part-1/投资")

ALLOWED_A_PREFIXES = (
    "000",
    "001",
    "002",
    "003",
    "300",
    "301",
    "600",
    "601",
    "603",
    "605",
    "688",
    "689",
    "159",
    "510",
    "511",
    "512",
    "513",
    "515",
    "516",
    "518",
    "560",
    "561",
    "562",
    "563",
)

SH_A_MAINBOARD_PREFIXES = ("600", "601", "603", "605")


def _normalize_a_symbol(raw: Any) -> str:
    s = str(raw or "").strip().upper()
    if not s:
        return ""
    s = s.replace(".SH", "").replace(".SZ", "").replace(".BJ", "").replace(".HK", "").replace(".US", "")
    if not (s.isdigit() and len(s) == 6):
        return ""
    if not s.startswith(ALLOWED_A_PREFIXES):
        return ""
    return s


def _is_etf_symbol_name(symbol: Any, name: Any) -> bool:
    s = _normalize_a_symbol(symbol)
    n = str(name or "").upper()
    return (
        "ETF" in n
        or s.startswith(("159", "510", "511", "512", "513", "515", "516", "518", "560", "561", "562", "563"))
    )


def _is_sh_a_mainboard_symbol(symbol: Any) -> bool:
    s = _normalize_a_symbol(symbol)
    return bool(s and s.startswith(SH_A_MAINBOARD_PREFIXES))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _read_holdings_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = _read_json(path)
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        arr = raw.get("holdings")
        if isinstance(arr, list):
            return [x for x in arr if isinstance(x, dict)]
    return []


def _to_float(v: str | None, default: float = 0.0) -> float:
    if not v:
        return default
    s = str(v).strip().replace(",", "").replace("¥", "").replace("%", "")
    if not s:
        return default
    try:
        return float(s)
    except Exception:
        return default


def _extract_stop_loss(script_text: str) -> float | None:
    if not script_text:
        return None
    m = re.search(r"止损[¥￥]?\s*([0-9]+(?:\.[0-9]+)?)", script_text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _extract_discipline(skills_rows: list[dict[str, str]]) -> dict[str, Any]:
    text_blob = "\n".join(
        [
            " ".join(
                [
                    str(r.get("Skill", "")),
                    str(r.get("Prompt（复制即用）", "")),
                    str(r.get("安全边界", "")),
                    str(r.get("结果指标/验收", "")),
                    str(r.get("步骤", "")),
                ]
            )
            for r in (skills_rows or [])
        ]
    )
    text_blob = text_blob.replace("≤", "<=").replace("–", "-")
    lower = text_blob.lower()

    position_cap = 0.20
    m = re.search(r"单票\s*[<≤=]+\s*([0-9]+)\s*%?", text_blob)
    if m:
        try:
            position_cap = max(0.05, min(0.5, float(m.group(1)) / 100.0))
        except Exception:
            position_cap = 0.20

    pool_min, pool_max = 3, 10
    m2 = re.search(r"候选池.*?([0-9]+)\s*[-~到]\s*([0-9]+)", text_blob)
    if m2:
        try:
            pool_min = int(m2.group(1))
            pool_max = int(m2.group(2))
        except Exception:
            pool_min, pool_max = 3, 10

    trading_windows: list[str] = []
    if ("开盘" in text_blob and "收盘" in text_blob) or "开盘/收盘" in text_blob:
        trading_windows = ["open", "close"]

    annual_target = "10%-15%"
    m3 = re.search(r"年化\s*([0-9]+(?:\.[0-9]+)?)\s*[-~到]\s*([0-9]+(?:\.[0-9]+)?)", text_blob)
    if m3:
        annual_target = f"{m3.group(1)}%-{m3.group(2)}%"

    return {
        "single_position_cap": position_cap,
        "must_stop_loss": ("触发止损必须执行" in text_blob) or ("止损必须执行" in text_blob),
        "ban_unconditional_averaging_down": ("禁止无条件摊平" in text_blob) or ("无条件摊平" in text_blob),
        "candidate_pool_range": [pool_min, pool_max],
        "trading_windows": trading_windows,
        "style_preference": "稳健+低频" if ("稳健" in text_blob and ("低频" in text_blob or "低频盯盘" in text_blob)) else "稳健",
        "annual_target_return": annual_target,
        "source": "invest_skills_db",
    }


def _ensure_quant_outputs(data_source: str, out_dir: Path) -> None:
    cmd = [
        "python3",
        str(ROOT / "scripts/run_finance_claw_quant_pipeline.py"),
        "--data-source",
        data_source,
        "--out-dir",
        str(out_dir),
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def _market_regime(quotes: list[dict[str, Any]]) -> dict[str, Any]:
    if not quotes:
        return {"regime": "unknown", "up_ratio": 0.0, "volatility_mean": 0.0}
    up = sum(1 for x in quotes if float(x.get("pct_chg", 0.0)) > 0)
    up_ratio = up / max(len(quotes), 1)
    vol_mean = sum(float(x.get("amplitude", 0.0)) for x in quotes) / len(quotes)
    if up_ratio >= 0.6 and vol_mean <= 5.0:
        reg = "risk_on"
    elif up_ratio <= 0.4 and vol_mean >= 6.0:
        reg = "risk_off"
    else:
        reg = "neutral"
    return {"regime": reg, "up_ratio": round(up_ratio, 4), "volatility_mean": round(vol_mean, 4)}


def _build_hybrid_recommendation(
    quant_report: dict[str, Any],
    factor_table: list[dict[str, Any]],
    holdings_stock: list[dict[str, str]],
    skills_rows: list[dict[str, str]],
    holdings_struct: list[dict[str, Any]] | None = None,
    market_regime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    factor_table = [x for x in factor_table if _normalize_a_symbol(x.get("symbol", ""))]
    symbol_to_factor: dict[str, dict[str, Any]] = {}
    for x in factor_table:
        sym = _normalize_a_symbol(x.get("symbol", ""))
        if sym:
            symbol_to_factor[sym] = x
    factor_table = [x for x in factor_table if _is_sh_a_mainboard_symbol(x.get("symbol", ""))]
    steady = [x for x in quant_report.get("steady_account_top", []) if _is_sh_a_mainboard_symbol(x.get("symbol", ""))][:3]
    short = [x for x in quant_report.get("short_account_top", []) if _is_sh_a_mainboard_symbol(x.get("symbol", ""))][:3]
    swing = [x for x in quant_report.get("swing_account_top", []) if _is_sh_a_mainboard_symbol(x.get("symbol", ""))][:3]

    def _is_good_name(v: Any) -> bool:
        s = str(v or "").strip()
        if not s:
            return False
        if s.startswith("SYM_"):
            return False
        if s in {"未知标的", "未知"}:
            return False
        if s.isdigit():
            return False
        return True

    def _extract_symbol_and_name_from_label(label: Any) -> tuple[str, str]:
        text = str(label or "").strip()
        if not text:
            return "", ""
        m = re.search(r"([0-9]{6})", text)
        sym = _normalize_a_symbol(m.group(1) if m else "")
        if not sym:
            return "", text
        # 例: "立讯精密(002475)" / "002475 立讯精密"
        name = text.replace(sym, "")
        name = re.sub(r"[\(\)（）\[\]\-_/]+", " ", name).strip()
        if not _is_good_name(name):
            name = ""
        return sym, name

    symbol_name_map: dict[str, str] = {}
    symbol_price_map: dict[str, float] = {}

    def _collect(sym: Any, name: Any) -> None:
        s = _normalize_a_symbol(sym)
        if not s:
            return
        if _is_good_name(name):
            symbol_name_map[s] = str(name).strip()

    def _collect_price(sym: Any, price: Any) -> None:
        s = _normalize_a_symbol(sym)
        if not s:
            return
        p = float(price or 0.0)
        if p > 0:
            symbol_price_map[s] = p

    for row in factor_table:
        _collect(row.get("symbol"), row.get("name"))
        _collect_price(row.get("symbol"), row.get("last"))
    for row in steady + short + swing:
        _collect(row.get("symbol"), row.get("name"))
        _collect_price(row.get("symbol"), row.get("price"))
    for row in holdings_struct or []:
        _collect(row.get("symbol"), row.get("name"))
        _collect_price(row.get("symbol"), row.get("last"))
    for row in holdings_stock or []:
        raw = row.get("标的", "")
        sym, name = _extract_symbol_and_name_from_label(raw)
        if sym and name:
            symbol_name_map[sym] = name

    # 从你的技能库提炼最核心主观约束
    discipline = _extract_discipline(skills_rows)
    risk_rules = {
        "no_unexplainable_trade": True,
        "execute_stop_loss": bool(discipline.get("must_stop_loss", True)),
        "no_unconditional_averaging_down": bool(discipline.get("ban_unconditional_averaging_down", True)),
        "single_position_cap": float(discipline.get("single_position_cap", 0.20)),
        "trading_windows": discipline.get("trading_windows", []),
        "candidate_pool_range": discipline.get("candidate_pool_range", [3, 10]),
        "annual_target_return": discipline.get("annual_target_return", "10%-15%"),
        "style_preference": discipline.get("style_preference", "稳健"),
    }

    # 持仓侧（主观研判与风控剧本）
    holding_risk_checks: list[dict[str, Any]] = []
    for row in holdings_stock[:100]:
        script = str(row.get("交易剧本（买入/加减仓/卖出）", ""))
        stop = _extract_stop_loss(script)
        pnl = _to_float(row.get("盈亏", "0"))
        holding_risk_checks.append(
            {
                "symbol_or_name": row.get("标的", ""),
                "current_amount": _to_float(row.get("当前持仓金额", "0")),
                "stop_loss": stop,
                "pnl": pnl,
                "action_hint": "严格执行止损" if stop is not None else "补全止损规则",
            }
        )

    regime_name = str((market_regime or {}).get("regime", "unknown") or "unknown")

    def _round_px(v: float) -> float:
        return round(float(v), 2)

    def _price_plan(
        price: float,
        account: str,
        momentum: float,
        vol: float,
        pct_chg: float,
        board_hit_prob: float,
        time_cycle: float,
        regime: str,
        history_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # 三层定价：先看市场环境，再看个股势能，最后落到分档执行价位。
        if price <= 0:
            return {
                "entry_price": 0.0,
                "entry_price_1": 0.0,
                "entry_price_2": 0.0,
                "take_profit_price": 0.0,
                "take_profit_price_1": 0.0,
                "take_profit_price_2": 0.0,
                "stop_loss_price": 0.0,
                "hard_stop_price": 0.0,
                "price_framework": "",
                "trend_label": "unknown",
                "invalidation_rule": "",
            }
        history_metrics = history_metrics or {}
        vol_proxy = max(0.012, min(0.12, max(vol, abs(pct_chg) / 100.0)))
        trend_strength = max(0.0, min(1.5, momentum))
        hit_prob = max(0.35, min(0.95, board_hit_prob or 0.55))
        cycle = max(0.3, min(0.9, time_cycle or 0.5))
        regime_bias = 0.0
        if regime == "risk_on":
            regime_bias = 1.0
        elif regime == "risk_off":
            regime_bias = -1.0
        atr14 = float(history_metrics.get("atr14", 0.0) or 0.0)
        high_10 = float(history_metrics.get("high_10", 0.0) or 0.0)
        low_10 = float(history_metrics.get("low_10", 0.0) or 0.0)
        high_20 = float(history_metrics.get("high_20", 0.0) or 0.0)
        low_20 = float(history_metrics.get("low_20", 0.0) or 0.0)
        close_slope_10 = float(history_metrics.get("close_slope_10", 0.0) or 0.0)
        range_20_pct = float(history_metrics.get("range_20_pct", 0.0) or 0.0)
        atr = atr14 if atr14 > 0 else price * max(0.015, vol_proxy * 0.85)
        if account == "short":
            entry_atr_mult_1, entry_atr_mult_2 = (0.55, 1.05)
            tp_atr_mult_1, tp_atr_mult_2 = (1.30, 2.10)
            stop_atr_mult = 0.95
        elif account == "swing":
            entry_atr_mult_1, entry_atr_mult_2 = (0.85, 1.55)
            tp_atr_mult_1, tp_atr_mult_2 = (1.80, 3.00)
            stop_atr_mult = 1.25
        else:
            entry_atr_mult_1, entry_atr_mult_2 = (0.70, 1.30)
            tp_atr_mult_1, tp_atr_mult_2 = (1.55, 2.55)
            stop_atr_mult = 1.10
        if regime == "risk_on":
            tp_atr_mult_1 += 0.18
            tp_atr_mult_2 += 0.28
            stop_atr_mult += 0.05
        elif regime == "risk_off":
            entry_atr_mult_1 += 0.12
            entry_atr_mult_2 += 0.22
            tp_atr_mult_1 -= 0.12
            tp_atr_mult_2 -= 0.18
            stop_atr_mult -= 0.08
        resistance_near = high_10 if high_10 > 0 else price + atr * tp_atr_mult_1
        resistance_far = high_20 if high_20 > 0 else price + atr * tp_atr_mult_2
        support_near = low_10 if low_10 > 0 else price - atr * entry_atr_mult_1
        support_far = low_20 if low_20 > 0 else price - atr * entry_atr_mult_2
        atr_pct = atr / price if price > 0 else 0.0
        if support_near >= price:
            support_near = price - atr * max(0.4, entry_atr_mult_1)
        if support_far >= support_near:
            support_far = support_near - atr * max(0.45, entry_atr_mult_2 - entry_atr_mult_1)
        entry_price_1 = _round_px(min(price - atr * 0.18, support_near + atr * 0.22))
        entry_price_2 = _round_px(min(entry_price_1 - atr * 0.25, support_far + atr * 0.12))
        take_profit_price_1 = _round_px(max(price + atr * tp_atr_mult_1, resistance_near - atr * 0.18))
        take_profit_price_2 = _round_px(max(take_profit_price_1 + atr * 0.45, resistance_far - atr * 0.10))
        stop_loss_price = _round_px(min(entry_price_2 - atr * 0.40, support_far - atr * stop_atr_mult * 0.35))
        if stop_loss_price >= entry_price_2:
            stop_loss_price = _round_px(entry_price_2 - atr * 0.55)
        if take_profit_price_1 <= price:
            take_profit_price_1 = _round_px(price + atr * max(1.0, tp_atr_mult_1))
        if take_profit_price_2 <= take_profit_price_1:
            take_profit_price_2 = _round_px(take_profit_price_1 + atr * 0.8)
        trend_label = "强势"
        if trend_strength < 0.18:
            trend_label = "弱修复"
        elif trend_strength < 0.45:
            trend_label = "中性偏强"
        if close_slope_10 < -0.03:
            trend_label = "下压修复"
        framework = (
            f"市场={regime}；势能={trend_label}；ATR14={atr:.2f}({atr_pct:.2%})；"
            f"10日支撑/压力={support_near:.2f}/{resistance_near:.2f}；20日支撑/压力={support_far:.2f}/{resistance_far:.2f}"
        )
        invalidation_rule = (
            f"若跌破 ¥{stop_loss_price:.2f} 或次日放量转弱，则判定当前交易逻辑失效"
        )
        return {
            "entry_price": entry_price_1,
            "entry_price_1": entry_price_1,
            "entry_price_2": entry_price_2,
            "take_profit_price": take_profit_price_1,
            "take_profit_price_1": take_profit_price_1,
            "take_profit_price_2": take_profit_price_2,
            "stop_loss_price": stop_loss_price,
            "hard_stop_price": stop_loss_price,
            "atr14": _round_px(atr),
            "atr14_pct": round(atr / price if price > 0 else 0.0, 4),
            "support_10": _round_px(support_near),
            "support_20": _round_px(support_far),
            "resistance_10": _round_px(resistance_near),
            "resistance_20": _round_px(resistance_far),
            "price_framework": framework,
            "trend_label": trend_label,
            "invalidation_rule": invalidation_rule,
        }

    def _enrich_pick(pick: dict[str, Any], account: str) -> dict[str, Any]:
        symbol = str(pick.get("symbol", ""))
        symbol = _normalize_a_symbol(symbol)
        if not symbol:
            return {}
        if not _is_sh_a_mainboard_symbol(symbol):
            return {}
        if account == "short" and _is_etf_symbol_name(symbol, pick.get("name", "")):
            return {}
        f = symbol_to_factor.get(symbol, {})
        factors = f.get("factors", {})
        price = float(f.get("last", 0.0) or 0.0)
        if price <= 0:
            price = float(symbol_price_map.get(symbol, 0.0) or 0.0)
        if price <= 0:
            # 回退：若行情缺失，尝试用预算/股数近似当前价，至少给出数值价位。
            alloc = float(pick.get("budget_alloc", 0.0) or 0.0)
            shares = float(pick.get("affordable_shares", 0.0) or 0.0)
            if alloc > 0 and shares > 0:
                price = alloc / shares
        momentum = float(factors.get("momentum", 0.0))
        vol = float(factors.get("volatility", 0.0))
        pct_chg = float(f.get("pct_chg", 0.0) or 0.0)
        board_hit_prob = float(factors.get("board_hit_prob", 0.0) or 0.0)
        time_cycle = float(factors.get("time_cycle", 0.0) or 0.0)
        history_metrics = f.get("history_metrics", {}) if isinstance(f.get("history_metrics", {}), dict) else {}
        px = _price_plan(price, account, momentum, vol, pct_chg, board_hit_prob, time_cycle, regime_name, history_metrics)
        if account == "short":
            tp_pct = (px["take_profit_price"] / price - 1.0) if price > 0 else 0.0
            if tp_pct < 0.05:
                return {}
        entry = (
            f"优先看第一买点≈{px['entry_price_1']:.2f}，若盘中回撤加深再看第二买点≈{px['entry_price_2']:.2f}"
        )
        exit_rule = (
            f"第一止盈≈{px['take_profit_price_1']:.2f}；第二止盈≈{px['take_profit_price_2']:.2f}；硬止损≈{px['stop_loss_price']:.2f}"
        )
        if account == "steady":
            exit_rule = (
                f"稳健：第一止盈≈{px['take_profit_price_1']:.2f}；第二止盈≈{px['take_profit_price_2']:.2f}；硬止损≈{px['stop_loss_price']:.2f}"
            )
        elif account == "swing":
            exit_rule = (
                f"波段：第一止盈≈{px['take_profit_price_1']:.2f}；第二止盈≈{px['take_profit_price_2']:.2f}；硬止损≈{px['stop_loss_price']:.2f}"
            )
        else:
            exit_rule = (
                f"T+1：第一止盈≈{px['take_profit_price_1']:.2f}；第二止盈≈{px['take_profit_price_2']:.2f}；硬止损≈{px['stop_loss_price']:.2f}"
            )
        pick_name = pick.get("name")
        resolved_name = symbol_name_map.get(symbol) or (str(pick_name).strip() if _is_good_name(pick_name) else "")
        return {
            "symbol": symbol,
            "name": resolved_name or f"SYM_{symbol}",
            "weight": pick.get("weight", 0.0),
            "price": _round_px(price),
            "entry_price": px["entry_price"],
            "entry_price_1": px["entry_price_1"],
            "entry_price_2": px["entry_price_2"],
            "take_profit_price": px["take_profit_price"],
            "take_profit_price_1": px["take_profit_price_1"],
            "take_profit_price_2": px["take_profit_price_2"],
            "stop_loss_price": px["stop_loss_price"],
            "hard_stop_price": px["hard_stop_price"],
            "atr14": px["atr14"],
            "atr14_pct": px["atr14_pct"],
            "support_10": px["support_10"],
            "support_20": px["support_20"],
            "resistance_10": px["resistance_10"],
            "resistance_20": px["resistance_20"],
            "entry_rule": entry,
            "exit_rule": exit_rule,
            "reason_quant": pick.get("reason", ""),
            "reason_subjective": "可解释、可跟踪、可执行（市场环境 + 个股势能 + 执行纪律）",
            "risk_flag": "high_vol" if vol > 0.9 else "normal",
            "momentum": round(momentum, 4),
            "pct_chg": round(pct_chg, 2),
            "trend_label": px["trend_label"],
            "market_regime": regime_name,
            "price_framework": px["price_framework"],
            "invalidation_rule": px["invalidation_rule"],
            "history_metrics": history_metrics,
            "holding_cycle_days": 1 if account == "short" else 20,
        }

    steady_recs = [x for x in (_enrich_pick(y, "steady") for y in steady) if x]
    short_recs = [x for x in (_enrich_pick(y, "short") for y in short) if x]
    swing_recs = [x for x in (_enrich_pick(y, "swing") for y in swing) if x]
    short_symbols = {str(x.get("symbol", "")) for x in short_recs if isinstance(x, dict)}
    steady_symbols = {str(x.get("symbol", "")) for x in steady_recs if isinstance(x, dict)}
    swing_symbols = {str(x.get("symbol", "")) for x in swing_recs if isinstance(x, dict)}

    holding_action_plan: list[dict[str, Any]] = []
    hs = holdings_struct or []
    if hs:
        total_mv = sum(float(x.get("market_value", 0.0) or 0.0) for x in hs)
        total_mv = total_mv if total_mv > 0 else 1.0
        target_map: dict[str, float] = {}

        def _bucket_cap(bucket_name: str, single_cap: float) -> float:
            if bucket_name == "short":
                return min(single_cap, 0.12)
            if bucket_name == "swing":
                return min(single_cap, 0.18)
            return min(single_cap, 0.2)

        def _score_bundle(sym: str) -> dict[str, float]:
            row = symbol_to_factor.get(sym, {}) if sym else {}
            scores = row.get("scores", {}) if isinstance(row, dict) else {}
            steady_score = float(scores.get("steady_score", 0.0) or 0.0)
            short_score = float(scores.get("short_score", 0.0) or 0.0)
            swing_score = 0.6 * steady_score + 0.4 * short_score
            return {
                "steady_score": steady_score,
                "short_score": short_score,
                "swing_score": swing_score,
                "max_score": max(steady_score, short_score, swing_score),
            }

        def _portfolio_weight(rec: dict[str, Any], bucket_name: str, single_cap: float) -> float:
            account_share = 0.4 if bucket_name == "steady" else (0.33 if bucket_name == "short" else 0.27)
            raw = float(rec.get("weight", 0.0) or 0.0) * account_share
            return max(0.0, min(_bucket_cap(bucket_name, single_cap), raw))

        cap = min(0.2, float(risk_rules.get("single_position_cap", 0.2)))
        for bucket_name, recs in (("steady", steady_recs), ("short", short_recs), ("swing", swing_recs)):
            for x in recs:
                sym = str(x.get("symbol", "")).strip()
                if not sym:
                    continue
                target_map[sym] = max(float(target_map.get(sym, 0.0)), _portfolio_weight(x, bucket_name, cap))

        def _fallback_target_weight(
            sym: str,
            bucket_name: str,
            current_w: float,
            pnl_pct: float,
            single_cap: float,
        ) -> tuple[float, str, float]:
            scores = _score_bundle(sym)
            if bucket_name == "short":
                signal = scores["short_score"]
                preserve_floor = 0.0
            elif bucket_name == "swing":
                signal = scores["swing_score"]
                preserve_floor = 0.025
            else:
                signal = scores["steady_score"]
                preserve_floor = 0.03
            signal_ratio = max(0.0, min(1.0, signal / 0.45))
            keep_ratio = 0.2 + 0.65 * signal_ratio
            target = min(_bucket_cap(bucket_name, single_cap), current_w * keep_ratio)
            if pnl_pct <= -0.2:
                target *= 0.35
            elif pnl_pct <= -0.12:
                target *= 0.55
            elif pnl_pct >= 0.2:
                target *= 0.85
            if signal_ratio >= 0.35 and current_w > 0:
                target = max(target, min(current_w, preserve_floor + signal_ratio * 0.035))
            if signal_ratio < 0.18 and pnl_pct <= -0.18:
                target = 0.0
            basis = "score_retention"
            if target <= 0:
                basis = "exit_on_weak_signal"
            return round(max(0.0, min(_bucket_cap(bucket_name, single_cap), target)), 4), basis, round(signal, 4)

        def _expected_result_text(action: str, current_w: float, target_w: float, pnl_pct: float) -> str:
            delta_pp = round((target_w - current_w) * 100, 1)
            if action in {"减仓", "止盈"}:
                return f"执行后仓位预计回落到 {target_w * 100:.1f}% 左右，释放 {abs(delta_pp):.1f}pct 资金占用并降低回撤风险"
            if action == "加仓":
                return f"执行后仓位预计提升到 {target_w * 100:.1f}% 左右，增加 {abs(delta_pp):.1f}pct 暴露以换取更明确的收益弹性"
            if pnl_pct <= -0.1:
                return f"执行后先把仓位稳定在 {target_w * 100:.1f}% 左右，等待止跌确认再做下一步"
            return f"执行后维持 {target_w * 100:.1f}% 左右目标仓位，组合风险与收益预期基本匹配"

        for row in hs:
            sym = str(row.get("symbol", "")).strip()
            sym = _normalize_a_symbol(sym)
            if not sym:
                continue
            name = str(row.get("name", sym))
            pnl_pct = float(row.get("pnl_pct", 0.0) or 0.0)
            bucket = str(row.get("bucket", "") or "unknown")
            current_w = float(row.get("market_value", 0.0) or 0.0) / total_mv
            suggested_bucket = "short" if sym in short_symbols else ("steady" if sym in steady_symbols else ("swing" if sym in swing_symbols else bucket))
            raw_target = float(target_map.get(sym, 0.0))
            target_basis = "candidate_pool"
            factor_signal = 0.0
            if raw_target > 0:
                target_w = raw_target
                factor_signal = _score_bundle(sym)["max_score"]
            else:
                target_w, target_basis, factor_signal = _fallback_target_weight(sym, suggested_bucket, current_w, pnl_pct, cap)

            action = "观察"
            reason = "未命中明确规则"
            if target_w <= 0.0001:
                if current_w >= 0.06:
                    action = "减仓"
                    reason = "不在当前目标池且占用资金，建议分批收缩仓位"
                elif pnl_pct <= -0.18:
                    action = "减仓"
                    reason = "不在当前目标池且回撤较大，优先收缩风险敞口"
                elif pnl_pct >= 0.2:
                    action = "止盈"
                    reason = "不在当前目标池且已有较大盈利，可分批锁盈"
            else:
                gap = target_w - current_w
                if current_w > max(target_w, cap) + 0.05:
                    action = "减仓"
                    reason = "当前仓位明显高于目标/上限，先降风险再观察"
                elif pnl_pct <= -0.23:
                    action = "减仓"
                    reason = "命中目标池但回撤过深，先降仓等待二次确认"
                elif pnl_pct <= -0.12:
                    action = "减仓"
                    reason = "命中目标池但回撤偏大，按纪律先降仓位"
                elif gap >= 0.035 and pnl_pct > -0.08 and factor_signal >= 0.22:
                    action = "加仓"
                    reason = "当前仓位明显低于目标，且信号强度仍在可执行区间"
                elif pnl_pct >= 0.25 and current_w > target_w + 0.03:
                    action = "止盈"
                    reason = "盈利显著且仓位高于目标，建议分批锁盈"
                else:
                    action = "持有"
                    reason = "符合当前目标池与风险预算，按纪律持有"
                if suggested_bucket == "short" and action == "持有":
                    reason = "短线票采用T+1管理，次日不及预期先减仓"
                if abs(target_w - current_w) < 0.01 and action in {"减仓", "加仓"}:
                    action = "持有"
                    reason = "当前仓位已接近目标仓位，先按纪律跟踪，不做多余操作"

            holding_action_plan.append(
                {
                    "symbol": sym,
                    "name": name,
                    "bucket": suggested_bucket,
                    "pnl_pct": round(pnl_pct, 4),
                    "target_weight": round(target_w, 4),
                    "current_weight": round(current_w, 4),
                    "delta_weight": round(target_w - current_w, 4),
                    "factor_signal": factor_signal,
                    "target_basis": target_basis,
                    "action": action,
                    "reason": reason,
                    "expected_result": _expected_result_text(action, current_w, target_w, pnl_pct),
                }
            )

    holding_agg_cost = 0.0
    holding_agg_value = 0.0
    hold_count = len(holdings_stock)
    if holdings_stock:
        for row in holdings_stock:
            pos = _to_float(row.get("当前持仓金额", "0"))
            pnl = _to_float(row.get("盈亏", "0"))
            holding_agg_value += max(0.0, pos)
            holding_agg_cost += max(0.0, pos - pnl)

    pnl_total = holding_agg_value - holding_agg_cost if holding_agg_cost > 0 else 0.0
    pnl_pct = (pnl_total / holding_agg_cost) if holding_agg_cost > 0 else 0.0

    strategy_system = {
        "steady_strategy": {
            "goal": "稳健账户：控制回撤，优先流动性与风险预算",
            "entry": "分批建仓，首次不超过目标仓位50%",
            "exit": "跌破止损线或波动显著放大时降仓",
            "max_holding_days": 30,
            "position_cap": risk_rules["single_position_cap"],
            "focus": "价值+质量+流动性核心票",
        },
        "short_strategy": {
            "goal": "极短线账户：次日管理，严格纪律",
            "entry": "仅在动量与成交确认后小仓位试错",
            "exit": "次日不及预期先减仓，触发止损立即退出",
            "max_holding_days": 1,
            "sell_deadline": "next_trade_day_close",
            "position_cap": min(0.25, risk_rules["single_position_cap"]),
            "focus": "强动量题材票，T+1风控优先",
        },
        "swing_strategy": {
            "goal": "波段账户：5-20交易日滚动管理，兼顾收益和回撤",
            "entry": "趋势确认后分批建仓，不追高",
            "exit": "触发止损线或达到阶段目标收益后分批止盈",
            "max_holding_days": 20,
            "position_cap": min(0.2, risk_rules["single_position_cap"]),
            "focus": "中等波动、流动性较好标的",
        },
    }

    return {
        "risk_rules": risk_rules,
        "steady_recommendations": steady_recs,
        "short_recommendations": short_recs,
        "swing_recommendations": swing_recs,
        "holding_risk_checks": holding_risk_checks[:20],
        "holding_action_plan": holding_action_plan[:30],
        "holding_snapshot_stats": {
            "holding_count": hold_count,
            "estimated_cost": round(holding_agg_cost, 2),
            "estimated_value": round(holding_agg_value, 2),
            "estimated_pnl": round(pnl_total, 2),
            "estimated_pnl_pct": round(pnl_pct, 4),
        },
        "discipline_profile": discipline,
        "strategy_system": strategy_system,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run daily hybrid recommendation (subjective + quant).")
    p.add_argument("--data-source", choices=["auto", "eastmoney", "tencent", "tonghuashun", "qveris"], default="qveris")
    p.add_argument("--skip-quant-refresh", action="store_true", help="Use existing quant outputs; do not rerun quant pipeline.")
    p.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR))
    p.add_argument("--holdings-json", default="", help="Optional holdings snapshot json extracted from broker screenshots.")
    p.add_argument("--quant-out-dir", default="tmp/system_runs/latest/finance_claw")
    p.add_argument("--out-dir", default="tmp/system_runs/latest/finance_claw")
    args = p.parse_args()

    quant_out_dir = ensure_dir(Path(args.quant_out_dir).expanduser().resolve())
    out_dir = ensure_dir(Path(args.out_dir).expanduser().resolve())
    export_dir = Path(args.export_dir).expanduser().resolve()

    if not args.skip_quant_refresh:
        _ensure_quant_outputs(args.data_source, quant_out_dir)
    quant_report = _read_json(quant_out_dir / "quant_report.json")
    factor_table = _read_json(quant_out_dir / "factor_table.json")
    quotes = _read_json(quant_out_dir / "quotes_snapshot.json")
    if isinstance(factor_table, list):
        factor_table = [x for x in factor_table if _normalize_a_symbol(x.get("symbol", ""))]
    if isinstance(quotes, list):
        quotes = [x for x in quotes if _normalize_a_symbol(x.get("symbol", ""))]

    stock_rows = _read_csv(export_dir / "持仓｜股票库 2b9738d4c19f4636a97ed751ad5088a1.csv")
    skills_rows = _read_csv(export_dir / "Invest Skills DB a517524d2f6c466284f0f7b858b111d5.csv")
    holdings_struct: list[dict[str, Any]] = []
    if args.holdings_json:
        hj = Path(args.holdings_json).expanduser().resolve()
        rows = _read_holdings_json(hj)
        if rows:
            holdings_struct = rows
            stock_rows = []
            for row in rows:
                name = str(row.get("name", row.get("symbol", "")))
                sym = _normalize_a_symbol(row.get("symbol", ""))
                if not sym:
                    continue
                mv = float(row.get("market_value", 0.0) or 0.0)
                pnl = float(row.get("pnl", 0.0) or 0.0)
                stop_loss = row.get("stop_loss", "")
                script = f"标的{name}；止损{stop_loss}" if stop_loss else f"标的{name}；补全止损规则"
                stock_rows.append(
                    {
                        "标的": name,
                        "代码": sym,
                        "当前持仓金额": str(mv),
                        "盈亏": str(pnl),
                        "交易剧本（买入/加减仓/卖出）": script,
                    }
                )

    regime = _market_regime(quotes if isinstance(quotes, list) else [])
    hybrid = _build_hybrid_recommendation(
        quant_report if isinstance(quant_report, dict) else {},
        factor_table if isinstance(factor_table, list) else [],
        stock_rows,
        skills_rows,
        holdings_struct=holdings_struct,
        market_regime=regime,
    )

    out = {
        "status": "ok",
        "scope": {"now": ["沪A主板"], "future": ["深市主板", "HK", "US"]},
        "data_source": quant_report.get("data_meta", {}).get("source", "unknown"),
        "realtime_connected": quant_report.get("data_meta", {}).get("realtime_connected", False),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "quote_count": len(quotes) if isinstance(quotes, list) else 0,
        "market_regime": regime,
        "hybrid_selection": hybrid,
        "strategy_references": {},
        "target": "在纪律约束下争取跑赢大盘",
        "warning": "不构成投资建议；需结合你账户实际风控与交易规则。",
    }
    stack_path = ROOT / "platform/domain_claws/finance_claw/integrations/open_source_quant_stack.yaml"
    if stack_path.exists():
        try:
            stack = yaml.safe_load(stack_path.read_text(encoding="utf-8")) or {}
            out["strategy_references"] = {
                "github_frameworks": stack.get("github_frameworks", []),
                "clawhub_skills": stack.get("clawhub_skills", []),
                "factor_validity_policy": stack.get("factor_validity_policy", []),
            }
        except Exception:
            out["strategy_references"] = {}

    write_json(out_dir / "daily_hybrid_recommendation.json", out)
    print(f"[OK] finance daily recommendation -> {out_dir / 'daily_hybrid_recommendation.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
