#!/usr/bin/env python3
"""
Invest OS - Enhanced Earnings Analyzer
投资OS - 财报异常定位增强模块

AI粗筛变化点 + 人工精读确认，异常项自动标注

Author: Nia OS Team
Version: 1.0.0
Created: 2026-08-18
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class AnomalyCategory(Enum):
    """异常类别"""
    REVENUE = "revenue"  # 收入
    PROFIT = "profit"  # 利润
    RECEIVABLE = "receivable"  # 应收账款
    INVENTORY = "inventory"  # 库存
    CASHFLOW = "cashflow"  # 现金流
    MARGIN = "margin"  # 毛利率/净利率
    EXPENSE = "expense"  # 费用
    OTHER = "other"


class AnomalySeverity(Enum):
    """异常严重性"""
    LOW = "low"  # 轻微
    MEDIUM = "medium"  # 中等
    HIGH = "high"  # 严重
    CRITICAL = "critical"  # 极严重


@dataclass
class EarningsAnomaly:
    """财报异常"""
    anomaly_id: str
    company_symbol: str
    company_name: str
    quarter: str
    category: AnomalyCategory
    metric_name: str
    current_value: float
    previous_value: float
    yoy_value: float  # 去年同期
    qoq_change_pct: float  # 环比变化
    yoy_change_pct: float  # 同比变化
    severity: AnomalySeverity
    ai_explanation: str
    source_location: str  # 财报页码/章节
    needs_human_review: bool = True
    human_reviewed: bool = False
    human_notes: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class EarningsComparison:
    """财报对比"""
    comparison_id: str
    symbol: str
    company_name: str
    current_quarter: str
    previous_quarter: str
    yoy_quarter: str
    anomalies: List[EarningsAnomaly]
    key_metrics: Dict[str, Dict[str, float]]  # metric_name -> {current, previous, yoy}
    quality_score: float  # 收入质量评分 0-1
    ai_summary: str
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class EarningsAnalyzer:
    """财报异常分析器"""

    def __init__(self, base_path: Path, db_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)

        # 初始化数据库
        self._init_database()

        # 异常检测阈值
        self.thresholds = {
            "qoq_change": 0.20,  # 环比变化超过20%
            "yoy_change": 0.30,  # 同比变化超过30%
            "receivable_revenue_ratio": 0.15,  # 应收/收入比超过15%
            "inventory_cogs_ratio": 0.20,  # 库存/成本比超过20%
            "cashflow_profit_ratio": 0.80,  # 现金流/利润比低于80%
        }

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 财报异常表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS earnings_anomalies (
            anomaly_id TEXT PRIMARY KEY,
            company_symbol TEXT NOT NULL,
            company_name TEXT NOT NULL,
            quarter TEXT NOT NULL,
            category TEXT,
            metric_name TEXT,
            current_value REAL,
            previous_value REAL,
            yoy_value REAL,
            qoq_change_pct REAL,
            yoy_change_pct REAL,
            severity TEXT,
            ai_explanation TEXT,
            source_location TEXT,
            needs_human_review BOOLEAN DEFAULT 1,
            human_reviewed BOOLEAN DEFAULT 0,
            human_notes TEXT,
            created_at TEXT
        )
        """)

        # 财报对比表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS earnings_comparisons (
            comparison_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            company_name TEXT NOT NULL,
            current_quarter TEXT NOT NULL,
            previous_quarter TEXT,
            yoy_quarter TEXT,
            key_metrics TEXT,
            quality_score REAL,
            ai_summary TEXT,
            created_at TEXT
        )
        """)

        conn.commit()
        conn.close()

    def analyze_earnings(
        self,
        company_symbol: str,
        company_name: str,
        current_data: Dict[str, float],
        previous_data: Optional[Dict[str, float]],
        yoy_data: Optional[Dict[str, float]],
        current_quarter: str
    ) -> EarningsComparison:
        """
        分析财报数据，检测异常

        Args:
            company_symbol: 股票代码
            company_name: 公司名称
            current_data: 当前季度数据
            previous_data: 上季度数据
            yoy_data: 去年同期数据
            current_quarter: 当前季度 (如 "2024Q1")

        Returns:
            财报对比结果
        """
        anomalies: List[EarningsAnomaly] = []

        # 计算关键指标
        key_metrics: Dict[str, Dict[str, float]] = {}

        for metric_name in current_data.keys():
            current_value = current_data[metric_name]
            previous_value = previous_data.get(metric_name, 0.0) if previous_data else 0.0
            yoy_value = yoy_data.get(metric_name, 0.0) if yoy_data else 0.0

            key_metrics[metric_name] = {
                "current": current_value,
                "previous": previous_value,
                "yoy": yoy_value
            }

            # 计算变化率
            qoq_change = self._calculate_change_pct(current_value, previous_value)
            yoy_change = self._calculate_change_pct(current_value, yoy_value)

            # 检测异常
            anomaly = self._detect_anomaly(
                company_symbol=company_symbol,
                company_name=company_name,
                quarter=current_quarter,
                metric_name=metric_name,
                current_value=current_value,
                previous_value=previous_value,
                yoy_value=yoy_value,
                qoq_change=qoq_change,
                yoy_change=yoy_change
            )

            if anomaly:
                anomalies.append(anomaly)

        # 检测关联异常（收入质量）
        quality_anomalies = self._detect_quality_issues(
            company_symbol=company_symbol,
            company_name=company_name,
            current_quarter=current_quarter,
            current_data=current_data,
            previous_data=previous_data
        )
        anomalies.extend(quality_anomalies)

        # 计算收入质量评分
        quality_score = self._calculate_quality_score(current_data)

        # 生成 AI 摘要
        ai_summary = self._generate_summary(anomalies, quality_score)

        # 创建对比结果
        comparison = EarningsComparison(
            comparison_id=f"{company_symbol}_{current_quarter}",
            symbol=company_symbol,
            company_name=company_name,
            current_quarter=current_quarter,
            previous_quarter=self._get_previous_quarter(current_quarter),
            yoy_quarter=self._get_yoy_quarter(current_quarter),
            anomalies=anomalies,
            key_metrics=key_metrics,
            quality_score=quality_score,
            ai_summary=ai_summary
        )

        return comparison

    def _calculate_change_pct(self, current: float, previous: float) -> float:
        """计算变化率"""
        if previous == 0:
            return 0.0 if current == 0 else 1.0
        return (current - previous) / abs(previous)

    def _detect_anomaly(
        self,
        company_symbol: str,
        company_name: str,
        quarter: str,
        metric_name: str,
        current_value: float,
        previous_value: float,
        yoy_value: float,
        qoq_change: float,
        yoy_change: float
    ) -> Optional[EarningsAnomaly]:
        """检测单个指标的异常"""

        # 判断是否超过阈值
        is_qoq_anomaly = abs(qoq_change) > self.thresholds["qoq_change"]
        is_yoy_anomaly = abs(yoy_change) > self.thresholds["yoy_change"]

        if not (is_qoq_anomaly or is_yoy_anomaly):
            return None

        # 确定类别
        category = self._categorize_metric(metric_name)

        # 评估严重性
        severity = self._assess_severity(qoq_change, yoy_change, category)

        # 生成解释
        explanation = self._generate_explanation(
            metric_name=metric_name,
            qoq_change=qoq_change,
            yoy_change=yoy_change,
            category=category
        )

        anomaly_id = f"{company_symbol}_{quarter}_{metric_name}"

        return EarningsAnomaly(
            anomaly_id=anomaly_id,
            company_symbol=company_symbol,
            company_name=company_name,
            quarter=quarter,
            category=category,
            metric_name=metric_name,
            current_value=current_value,
            previous_value=previous_value,
            yoy_value=yoy_value,
            qoq_change_pct=qoq_change,
            yoy_change_pct=yoy_change,
            severity=severity,
            ai_explanation=explanation,
            source_location="财务报表主表"
        )

    def _categorize_metric(self, metric_name: str) -> AnomalyCategory:
        """对指标分类"""
        metric_lower = metric_name.lower()

        if any(kw in metric_lower for kw in ["revenue", "收入", "营收"]):
            return AnomalyCategory.REVENUE
        elif any(kw in metric_lower for kw in ["profit", "利润", "净利"]):
            return AnomalyCategory.PROFIT
        elif any(kw in metric_lower for kw in ["receivable", "应收"]):
            return AnomalyCategory.RECEIVABLE
        elif any(kw in metric_lower for kw in ["inventory", "库存", "存货"]):
            return AnomalyCategory.INVENTORY
        elif any(kw in metric_lower for kw in ["cashflow", "现金流", "经营现金"]):
            return AnomalyCategory.CASHFLOW
        elif any(kw in metric_lower for kw in ["margin", "毛利率", "净利率"]):
            return AnomalyCategory.MARGIN
        elif any(kw in metric_lower for kw in ["expense", "费用", "成本"]):
            return AnomalyCategory.EXPENSE
        else:
            return AnomalyCategory.OTHER

    def _assess_severity(
        self,
        qoq_change: float,
        yoy_change: float,
        category: AnomalyCategory
    ) -> AnomalySeverity:
        """评估异常严重性"""
        max_change = max(abs(qoq_change), abs(yoy_change))

        # 关键指标的阈值更严格
        critical_categories = [
            AnomalyCategory.CASHFLOW,
            AnomalyCategory.RECEIVABLE,
            AnomalyCategory.PROFIT
        ]

        if category in critical_categories:
            if max_change > 0.50:
                return AnomalySeverity.CRITICAL
            elif max_change > 0.35:
                return AnomalySeverity.HIGH
            elif max_change > 0.20:
                return AnomalySeverity.MEDIUM
            else:
                return AnomalySeverity.LOW
        else:
            if max_change > 0.60:
                return AnomalySeverity.CRITICAL
            elif max_change > 0.45:
                return AnomalySeverity.HIGH
            elif max_change > 0.30:
                return AnomalySeverity.MEDIUM
            else:
                return AnomalySeverity.LOW

    def _generate_explanation(
        self,
        metric_name: str,
        qoq_change: float,
        yoy_change: float,
        category: AnomalyCategory
    ) -> str:
        """生成异常解释"""
        direction_qoq = "增长" if qoq_change > 0 else "下降"
        direction_yoy = "增长" if yoy_change > 0 else "下降"

        explanation = f"{metric_name}环比{direction_qoq}{abs(qoq_change)*100:.1f}%，"
        explanation += f"同比{direction_yoy}{abs(yoy_change)*100:.1f}%。"

        # 根据类别添加关注点
        if category == AnomalyCategory.RECEIVABLE:
            explanation += "需关注应收账款回收情况和坏账风险。"
        elif category == AnomalyCategory.INVENTORY:
            explanation += "需关注库存周转率和存货跌价风险。"
        elif category == AnomalyCategory.CASHFLOW:
            explanation += "需关注经营性现金流与利润的匹配度。"
        elif category == AnomalyCategory.MARGIN:
            explanation += "需关注成本控制和产品定价能力。"

        return explanation

    def _detect_quality_issues(
        self,
        company_symbol: str,
        company_name: str,
        current_quarter: str,
        current_data: Dict[str, float],
        previous_data: Optional[Dict[str, float]]
    ) -> List[EarningsAnomaly]:
        """检测收入质量问题"""
        quality_anomalies: List[EarningsAnomaly] = []

        revenue = current_data.get("revenue", 0.0)
        receivable = current_data.get("receivable", 0.0)
        cashflow = current_data.get("operating_cashflow", 0.0)
        profit = current_data.get("net_profit", 0.0)

        # 应收/收入比异常
        if revenue > 0:
            receivable_ratio = receivable / revenue
            if receivable_ratio > self.thresholds["receivable_revenue_ratio"]:
                anomaly = EarningsAnomaly(
                    anomaly_id=f"{company_symbol}_{current_quarter}_receivable_ratio",
                    company_symbol=company_symbol,
                    company_name=company_name,
                    quarter=current_quarter,
                    category=AnomalyCategory.RECEIVABLE,
                    metric_name="应收账款/收入比",
                    current_value=receivable_ratio,
                    previous_value=0.0,
                    yoy_value=0.0,
                    qoq_change_pct=0.0,
                    yoy_change_pct=0.0,
                    severity=AnomalySeverity.HIGH,
                    ai_explanation=f"应收账款占收入比例为{receivable_ratio*100:.1f}%，远超正常水平，收入质量存疑。",
                    source_location="资产负债表、利润表"
                )
                quality_anomalies.append(anomaly)

        # 现金流/利润比异常
        if profit > 0:
            cashflow_ratio = cashflow / profit
            if cashflow_ratio < self.thresholds["cashflow_profit_ratio"]:
                severity = AnomalySeverity.CRITICAL if cashflow_ratio < 0.5 else AnomalySeverity.HIGH

                anomaly = EarningsAnomaly(
                    anomaly_id=f"{company_symbol}_{current_quarter}_cashflow_ratio",
                    company_symbol=company_symbol,
                    company_name=company_name,
                    quarter=current_quarter,
                    category=AnomalyCategory.CASHFLOW,
                    metric_name="经营现金流/净利润比",
                    current_value=cashflow_ratio,
                    previous_value=0.0,
                    yoy_value=0.0,
                    qoq_change_pct=0.0,
                    yoy_change_pct=0.0,
                    severity=severity,
                    ai_explanation=f"经营现金流仅为净利润的{cashflow_ratio*100:.1f}%，利润质量较差，可能存在大量应收或非现金收入。",
                    source_location="现金流量表、利润表"
                )
                quality_anomalies.append(anomaly)

        return quality_anomalies

    def _calculate_quality_score(self, data: Dict[str, float]) -> float:
        """计算收入质量评分 (0-1)"""
        score = 1.0

        revenue = data.get("revenue", 0.0)
        receivable = data.get("receivable", 0.0)
        cashflow = data.get("operating_cashflow", 0.0)
        profit = data.get("net_profit", 0.0)

        # 应收账款占比扣分
        if revenue > 0:
            receivable_ratio = receivable / revenue
            if receivable_ratio > 0.15:
                score -= min(0.3, (receivable_ratio - 0.15) * 2)

        # 现金流质量扣分
        if profit > 0:
            cashflow_ratio = cashflow / profit
            if cashflow_ratio < 0.8:
                score -= min(0.4, (0.8 - cashflow_ratio) * 2)

        return max(0.0, score)

    def _generate_summary(
        self,
        anomalies: List[EarningsAnomaly],
        quality_score: float
    ) -> str:
        """生成 AI 摘要"""
        if not anomalies:
            return f"本季度财报数据正常，未发现显著异常。收入质量评分：{quality_score:.2f}"

        critical_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL)
        high_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.HIGH)

        summary = f"发现{len(anomalies)}项异常，其中极严重{critical_count}项，严重{high_count}项。"
        summary += f"收入质量评分：{quality_score:.2f}。"

        # 列出关键异常
        critical_anomalies = [a for a in anomalies if a.severity == AnomalySeverity.CRITICAL]
        if critical_anomalies:
            summary += "关键关注："
            for a in critical_anomalies[:3]:  # 最多列3个
                summary += f"{a.metric_name}（{a.ai_explanation[:30]}...）；"

        return summary

    def _get_previous_quarter(self, quarter: str) -> str:
        """获取上一季度"""
        year = int(quarter[:4])
        q = int(quarter[-1])

        if q == 1:
            return f"{year-1}Q4"
        else:
            return f"{year}Q{q-1}"

    def _get_yoy_quarter(self, quarter: str) -> str:
        """获取去年同期"""
        year = int(quarter[:4])
        q = quarter[-2:]
        return f"{year-1}{q}"

    def save_comparison(self, comparison: EarningsComparison):
        """保存对比结果到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 保存对比记录
        cursor.execute("""
        INSERT OR REPLACE INTO earnings_comparisons
        (comparison_id, symbol, company_name, current_quarter, previous_quarter,
         yoy_quarter, key_metrics, quality_score, ai_summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comparison.comparison_id,
            comparison.symbol,
            comparison.company_name,
            comparison.current_quarter,
            comparison.previous_quarter,
            comparison.yoy_quarter,
            json.dumps(comparison.key_metrics, ensure_ascii=False),
            comparison.quality_score,
            comparison.ai_summary,
            comparison.created_at
        ))

        # 保存异常记录
        for anomaly in comparison.anomalies:
            cursor.execute("""
            INSERT OR REPLACE INTO earnings_anomalies
            (anomaly_id, company_symbol, company_name, quarter, category,
             metric_name, current_value, previous_value, yoy_value,
             qoq_change_pct, yoy_change_pct, severity, ai_explanation,
             source_location, needs_human_review, human_reviewed,
             human_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                anomaly.anomaly_id,
                anomaly.company_symbol,
                anomaly.company_name,
                anomaly.quarter,
                anomaly.category.value,
                anomaly.metric_name,
                anomaly.current_value,
                anomaly.previous_value,
                anomaly.yoy_value,
                anomaly.qoq_change_pct,
                anomaly.yoy_change_pct,
                anomaly.severity.value,
                anomaly.ai_explanation,
                anomaly.source_location,
                anomaly.needs_human_review,
                anomaly.human_reviewed,
                anomaly.human_notes,
                anomaly.created_at
            ))

        conn.commit()
        conn.close()

    def generate_report(self, comparison: EarningsComparison) -> str:
        """生成财报异常分析报告（Markdown格式）"""
        report = f"# 财报异常分析报告 - {comparison.company_name} ({comparison.symbol})\n\n"
        report += f"**分析季度**: {comparison.current_quarter}\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**收入质量评分**: {comparison.quality_score:.2f}/1.00\n\n"
        report += f"**AI摘要**: {comparison.ai_summary}\n\n"
        report += "---\n\n"

        if not comparison.anomalies:
            report += "## ✅ 未发现显著异常\n\n"
            report += "本季度财报数据在正常范围内，未发现需要特别关注的异常项。\n"
            return report

        # 按严重性分组
        critical = [a for a in comparison.anomalies if a.severity == AnomalySeverity.CRITICAL]
        high = [a for a in comparison.anomalies if a.severity == AnomalySeverity.HIGH]
        medium = [a for a in comparison.anomalies if a.severity == AnomalySeverity.MEDIUM]

        if critical:
            report += "## 🚨 极严重异常（需立即关注）\n\n"
            for anomaly in critical:
                report += self._format_anomaly(anomaly)

        if high:
            report += "## ⚠️ 严重异常（需重点关注）\n\n"
            for anomaly in high:
                report += self._format_anomaly(anomaly)

        if medium:
            report += "## 🔍 中等异常（建议关注）\n\n"
            for anomaly in medium:
                report += self._format_anomaly(anomaly)

        report += "---\n\n"
        report += "## 📊 关键指标对比\n\n"
        report += "| 指标 | 当前值 | 上季度 | 去年同期 | 环比 | 同比 |\n"
        report += "|------|--------|--------|----------|------|------|\n"

        for metric_name, values in comparison.key_metrics.items():
            current = values["current"]
            previous = values["previous"]
            yoy = values["yoy"]

            qoq_pct = self._calculate_change_pct(current, previous) * 100
            yoy_pct = self._calculate_change_pct(current, yoy) * 100

            report += f"| {metric_name} | {current:.2f} | {previous:.2f} | {yoy:.2f} | "
            report += f"{qoq_pct:+.1f}% | {yoy_pct:+.1f}% |\n"

        report += "\n---\n\n"
        report += "## 🎯 人工审核建议\n\n"

        for anomaly in comparison.anomalies:
            if anomaly.needs_human_review and not anomaly.human_reviewed:
                report += f"- [ ] 核实 **{anomaly.metric_name}** 的{anomaly.ai_explanation}\n"

        return report

    def _format_anomaly(self, anomaly: EarningsAnomaly) -> str:
        """格式化异常输出"""
        output = f"### {anomaly.metric_name}\n\n"
        output += f"- **类别**: {anomaly.category.value}\n"
        output += f"- **当前值**: {anomaly.current_value:.2f}\n"
        output += f"- **环比变化**: {anomaly.qoq_change_pct*100:+.1f}%\n"
        output += f"- **同比变化**: {anomaly.yoy_change_pct*100:+.1f}%\n"
        output += f"- **AI分析**: {anomaly.ai_explanation}\n"
        output += f"- **数据来源**: {anomaly.source_location}\n"

        if anomaly.human_reviewed:
            output += f"- **人工批注**: {anomaly.human_notes}\n"
        else:
            output += f"- **待人工确认**: ✅\n"

        output += "\n"
        return output


def main():
    """测试代码"""
    base_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation")
    db_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation/earnings.db")

    analyzer = EarningsAnalyzer(base_path, db_path)

    # 示例数据
    current = {
        "revenue": 1000.0,
        "net_profit": 100.0,
        "receivable": 200.0,  # 应收/收入=20%，超标
        "operating_cashflow": 60.0,  # 现金流/利润=60%，低于标准
        "inventory": 150.0
    }

    previous = {
        "revenue": 900.0,
        "net_profit": 90.0,
        "receivable": 140.0,
        "operating_cashflow": 80.0,
        "inventory": 130.0
    }

    yoy = {
        "revenue": 750.0,
        "net_profit": 75.0,
        "receivable": 120.0,
        "operating_cashflow": 70.0,
        "inventory": 110.0
    }

    comparison = analyzer.analyze_earnings(
        company_symbol="000001",
        company_name="测试公司",
        current_data=current,
        previous_data=previous,
        yoy_data=yoy,
        current_quarter="2024Q1"
    )

    print(f"发现 {len(comparison.anomalies)} 项异常")
    print(f"收入质量评分: {comparison.quality_score:.2f}")
    print(f"\nAI摘要: {comparison.ai_summary}")

    # 生成报告
    report = analyzer.generate_report(comparison)
    print("\n" + "="*60)
    print(report)

    # 保存到数据库
    analyzer.save_comparison(comparison)
    print("\n已保存到数据库")


if __name__ == "__main__":
    main()
