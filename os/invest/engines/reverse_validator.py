#!/usr/bin/env python3
"""
Invest OS - Reverse Validation Engine
投资OS - 反向验证引擎

专门找反面证据，对抗确认偏误

Author: Nia OS Team
Version: 1.0.0
Created: 2026-08-18
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class EvidenceType(Enum):
    """证据类型"""
    FINANCIAL = "financial"  # 财务数据
    COMPETITIVE = "competitive"  # 竞争格局
    MARKET = "market"  # 市场趋势
    MANAGEMENT = "management"  # 管理层行为
    REGULATORY = "regulatory"  # 监管政策
    TECHNICAL = "technical"  # 技术趋势


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class InvestmentThesis:
    """投资逻辑"""
    thesis_id: str
    symbol: str
    company_name: str
    core_logic: str  # 核心逻辑
    key_assumptions: List[str]  # 关键假设
    expected_catalysts: List[str]  # 预期催化剂
    target_return: float  # 目标收益率
    time_horizon: str  # 投资期限
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


@dataclass
class CounterEvidence:
    """反面证据"""
    evidence_id: str
    thesis_id: str
    counter_to: str  # 反驳哪个假设
    evidence_type: EvidenceType
    description: str
    data_source: str
    severity: float  # 反驳强度 0-1
    confidence: float  # 证据可信度 0-1
    human_reviewed: bool = False
    human_assessment: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class DevilsAdvocateReport:
    """反向验证报告"""
    report_id: str
    thesis: InvestmentThesis
    counter_evidences: List[CounterEvidence]
    risk_score: float  # 综合风险评分 0-1
    risk_level: RiskLevel
    ai_summary: str
    recommendation: str  # hold/reduce/exit
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ReverseValidator:
    """反向验证器"""

    def __init__(self, base_path: Path, db_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)

        # 初始化数据库
        self._init_database()

        # 反面证据搜索关键词
        self.negative_keywords = {
            EvidenceType.FINANCIAL: [
                "下降", "减少", "放缓", "恶化", "亏损",
                "应收增加", "库存积压", "现金流紧张"
            ],
            EvidenceType.COMPETITIVE: [
                "竞争加剧", "价格战", "市场份额下降",
                "新进入者", "替代品", "客户流失"
            ],
            EvidenceType.MARKET: [
                "需求疲软", "增长放缓", "市场饱和",
                "周期下行", "政策收紧"
            ],
            EvidenceType.MANAGEMENT: [
                "高管离职", "违规", "减持", "承诺未兑现",
                "信息披露不完整"
            ]
        }

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 投资逻辑表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS investment_theses (
            thesis_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            company_name TEXT NOT NULL,
            core_logic TEXT NOT NULL,
            key_assumptions TEXT,
            expected_catalysts TEXT,
            target_return REAL,
            time_horizon TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)

        # 反面证据表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS counter_evidences (
            evidence_id TEXT PRIMARY KEY,
            thesis_id TEXT NOT NULL,
            counter_to TEXT,
            evidence_type TEXT,
            description TEXT,
            data_source TEXT,
            severity REAL,
            confidence REAL,
            human_reviewed BOOLEAN DEFAULT 0,
            human_assessment TEXT,
            created_at TEXT,
            FOREIGN KEY (thesis_id) REFERENCES investment_theses(thesis_id)
        )
        """)

        # 反向验证报告表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devils_advocate_reports (
            report_id TEXT PRIMARY KEY,
            thesis_id TEXT NOT NULL,
            risk_score REAL,
            risk_level TEXT,
            ai_summary TEXT,
            recommendation TEXT,
            created_at TEXT,
            FOREIGN KEY (thesis_id) REFERENCES investment_theses(thesis_id)
        )
        """)

        conn.commit()
        conn.close()

    def create_thesis(
        self,
        symbol: str,
        company_name: str,
        core_logic: str,
        key_assumptions: List[str],
        expected_catalysts: List[str],
        target_return: float = 0.20,
        time_horizon: str = "1年"
    ) -> InvestmentThesis:
        """创建投资逻辑"""
        thesis_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        thesis = InvestmentThesis(
            thesis_id=thesis_id,
            symbol=symbol,
            company_name=company_name,
            core_logic=core_logic,
            key_assumptions=key_assumptions,
            expected_catalysts=expected_catalysts,
            target_return=target_return,
            time_horizon=time_horizon
        )

        self.save_thesis(thesis)
        return thesis

    def save_thesis(self, thesis: InvestmentThesis):
        """保存投资逻辑到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO investment_theses
        (thesis_id, symbol, company_name, core_logic, key_assumptions,
         expected_catalysts, target_return, time_horizon, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            thesis.thesis_id,
            thesis.symbol,
            thesis.company_name,
            thesis.core_logic,
            json.dumps(thesis.key_assumptions, ensure_ascii=False),
            json.dumps(thesis.expected_catalysts, ensure_ascii=False),
            thesis.target_return,
            thesis.time_horizon,
            thesis.created_at,
            thesis.updated_at
        ))

        conn.commit()
        conn.close()

    def find_counter_evidences(
        self,
        thesis: InvestmentThesis,
        financial_data: Optional[Dict] = None,
        market_data: Optional[Dict] = None,
        competitor_data: Optional[Dict] = None
    ) -> List[CounterEvidence]:
        """
        寻找反面证据

        Args:
            thesis: 投资逻辑
            financial_data: 财务数据
            market_data: 市场数据
            competitor_data: 竞争对手数据

        Returns:
            反面证据列表
        """
        evidences: List[CounterEvidence] = []

        # 针对每个假设寻找反面证据
        for assumption in thesis.key_assumptions:
            # 从财务数据找反面证据
            if financial_data:
                financial_evidences = self._find_financial_counter_evidence(
                    thesis_id=thesis.thesis_id,
                    assumption=assumption,
                    data=financial_data
                )
                evidences.extend(financial_evidences)

            # 从市场数据找反面证据
            if market_data:
                market_evidences = self._find_market_counter_evidence(
                    thesis_id=thesis.thesis_id,
                    assumption=assumption,
                    data=market_data
                )
                evidences.extend(market_evidences)

            # 从竞争数据找反面证据
            if competitor_data:
                competitive_evidences = self._find_competitive_counter_evidence(
                    thesis_id=thesis.thesis_id,
                    assumption=assumption,
                    data=competitor_data
                )
                evidences.extend(competitive_evidences)

        return evidences

    def _find_financial_counter_evidence(
        self,
        thesis_id: str,
        assumption: str,
        data: Dict
    ) -> List[CounterEvidence]:
        """从财务数据中找反面证据"""
        evidences: List[CounterEvidence] = []

        # 检查关键财务指标
        checks = [
            ("revenue_growth", "收入增长", 0.10, "收入增长放缓"),
            ("profit_margin", "利润率", 0.15, "利润率下降"),
            ("roa", "ROA", 0.08, "资产回报率低"),
            ("debt_ratio", "负债率", 0.60, "负债率过高"),
            ("cashflow_ratio", "现金流/利润", 0.80, "现金流质量差")
        ]

        for metric_key, metric_name, threshold, warning in checks:
            value = data.get(metric_key, 0.0)

            # 针对不同指标判断是否异常
            is_anomaly = False
            if metric_key in ["revenue_growth", "profit_margin", "roa", "cashflow_ratio"]:
                is_anomaly = value < threshold
            elif metric_key == "debt_ratio":
                is_anomaly = value > threshold

            if is_anomaly:
                # 计算反驳强度
                if metric_key == "debt_ratio":
                    severity = min(1.0, (value - threshold) / threshold)
                else:
                    severity = min(1.0, (threshold - value) / threshold)

                evidence = CounterEvidence(
                    evidence_id=f"{thesis_id}_{metric_key}_{datetime.now().strftime('%Y%m%d')}",
                    thesis_id=thesis_id,
                    counter_to=assumption,
                    evidence_type=EvidenceType.FINANCIAL,
                    description=f"{warning}：{metric_name}为{value:.2%}，低于/高于预期{threshold:.2%}",
                    data_source="财务报表",
                    severity=severity,
                    confidence=0.9  # 财务数据可信度高
                )

                evidences.append(evidence)

        return evidences

    def _find_market_counter_evidence(
        self,
        thesis_id: str,
        assumption: str,
        data: Dict
    ) -> List[CounterEvidence]:
        """从市场数据中找反面证据"""
        evidences: List[CounterEvidence] = []

        # 市场趋势检查
        market_growth = data.get("market_growth", 0.0)
        market_saturation = data.get("saturation_level", 0.0)
        demand_trend = data.get("demand_trend", "stable")

        if market_growth < 0.05:
            evidence = CounterEvidence(
                evidence_id=f"{thesis_id}_market_growth_{datetime.now().strftime('%Y%m%d')}",
                thesis_id=thesis_id,
                counter_to=assumption,
                evidence_type=EvidenceType.MARKET,
                description=f"市场增长放缓：行业整体增速仅{market_growth:.1%}，低于预期",
                data_source="行业报告",
                severity=0.6,
                confidence=0.7
            )
            evidences.append(evidence)

        if market_saturation > 0.80:
            evidence = CounterEvidence(
                evidence_id=f"{thesis_id}_saturation_{datetime.now().strftime('%Y%m%d')}",
                thesis_id=thesis_id,
                counter_to=assumption,
                evidence_type=EvidenceType.MARKET,
                description=f"市场接近饱和：渗透率已达{market_saturation:.1%}，增长空间有限",
                data_source="行业分析",
                severity=0.7,
                confidence=0.6
            )
            evidences.append(evidence)

        if demand_trend == "declining":
            evidence = CounterEvidence(
                evidence_id=f"{thesis_id}_demand_{datetime.now().strftime('%Y%m%d')}",
                thesis_id=thesis_id,
                counter_to=assumption,
                evidence_type=EvidenceType.MARKET,
                description="需求下降趋势：下游客户采购意愿减弱",
                data_source="产业链调研",
                severity=0.8,
                confidence=0.7
            )
            evidences.append(evidence)

        return evidences

    def _find_competitive_counter_evidence(
        self,
        thesis_id: str,
        assumption: str,
        data: Dict
    ) -> List[CounterEvidence]:
        """从竞争数据中找反面证据"""
        evidences: List[CounterEvidence] = []

        # 竞争格局检查
        market_share = data.get("market_share", 0.0)
        market_share_change = data.get("market_share_change", 0.0)
        new_entrants = data.get("new_entrants", 0)
        price_war = data.get("price_war_intensity", 0.0)

        if market_share_change < -0.02:
            evidence = CounterEvidence(
                evidence_id=f"{thesis_id}_share_loss_{datetime.now().strftime('%Y%m%d')}",
                thesis_id=thesis_id,
                counter_to=assumption,
                evidence_type=EvidenceType.COMPETITIVE,
                description=f"市场份额流失：份额下降{abs(market_share_change):.1%}，竞争力减弱",
                data_source="市场调研",
                severity=0.7,
                confidence=0.8
            )
            evidences.append(evidence)

        if new_entrants > 3:
            evidence = CounterEvidence(
                evidence_id=f"{thesis_id}_new_entrants_{datetime.now().strftime('%Y%m%d')}",
                thesis_id=thesis_id,
                counter_to=assumption,
                evidence_type=EvidenceType.COMPETITIVE,
                description=f"新进入者增多：{new_entrants}家新公司进入市场，竞争加剧",
                data_source="行业跟踪",
                severity=0.6,
                confidence=0.7
            )
            evidences.append(evidence)

        if price_war > 0.5:
            evidence = CounterEvidence(
                evidence_id=f"{thesis_id}_price_war_{datetime.now().strftime('%Y%m%d')}",
                thesis_id=thesis_id,
                counter_to=assumption,
                evidence_type=EvidenceType.COMPETITIVE,
                description="价格战激烈：行业整体降价抢市场，利润率承压",
                data_source="竞品分析",
                severity=0.8,
                confidence=0.8
            )
            evidences.append(evidence)

        return evidences

    def calculate_risk_score(
        self,
        evidences: List[CounterEvidence]
    ) -> Tuple[float, RiskLevel]:
        """计算综合风险评分"""
        if not evidences:
            return 0.0, RiskLevel.LOW

        # 加权计算风险评分
        total_weight = 0.0
        weighted_score = 0.0

        for evidence in evidences:
            weight = evidence.severity * evidence.confidence
            total_weight += weight
            weighted_score += weight * evidence.severity

        risk_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # 确定风险等级
        if risk_score >= 0.75:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.50:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return risk_score, risk_level

    def generate_recommendation(
        self,
        risk_score: float,
        risk_level: RiskLevel
    ) -> str:
        """生成操作建议"""
        if risk_level == RiskLevel.CRITICAL:
            return "exit - 建议立即退出，风险过高"
        elif risk_level == RiskLevel.HIGH:
            return "reduce - 建议减仓50%以上，控制风险"
        elif risk_level == RiskLevel.MEDIUM:
            return "reduce - 建议减仓20-30%，密切关注"
        else:
            return "hold - 可继续持有，保持关注"

    def generate_report(
        self,
        thesis: InvestmentThesis,
        evidences: List[CounterEvidence]
    ) -> DevilsAdvocateReport:
        """生成反向验证报告"""
        risk_score, risk_level = self.calculate_risk_score(evidences)
        recommendation = self.generate_recommendation(risk_score, risk_level)

        # 生成 AI 摘要
        ai_summary = self._generate_ai_summary(thesis, evidences, risk_score)

        report_id = f"report_{thesis.thesis_id}_{datetime.now().strftime('%Y%m%d')}"

        report = DevilsAdvocateReport(
            report_id=report_id,
            thesis=thesis,
            counter_evidences=evidences,
            risk_score=risk_score,
            risk_level=risk_level,
            ai_summary=ai_summary,
            recommendation=recommendation
        )

        return report

    def _generate_ai_summary(
        self,
        thesis: InvestmentThesis,
        evidences: List[CounterEvidence],
        risk_score: float
    ) -> str:
        """生成 AI 摘要"""
        if not evidences:
            return f"针对{thesis.company_name}的投资逻辑，未发现显著反面证据，可继续持有。"

        summary = f"针对{thesis.company_name}的投资逻辑，发现{len(evidences)}条反面证据，"
        summary += f"综合风险评分{risk_score:.2f}。"

        # 按严重性排序
        sorted_evidences = sorted(evidences, key=lambda e: e.severity * e.confidence, reverse=True)

        summary += "主要风险包括："
        for evidence in sorted_evidences[:3]:  # 列出前3条
            summary += f"{evidence.evidence_type.value}方面（{evidence.description}）；"

        return summary

    def save_report(self, report: DevilsAdvocateReport):
        """保存报告到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 保存报告
        cursor.execute("""
        INSERT OR REPLACE INTO devils_advocate_reports
        (report_id, thesis_id, risk_score, risk_level, ai_summary,
         recommendation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            report.report_id,
            report.thesis.thesis_id,
            report.risk_score,
            report.risk_level.value,
            report.ai_summary,
            report.recommendation,
            report.created_at
        ))

        # 保存证据
        for evidence in report.counter_evidences:
            cursor.execute("""
            INSERT OR REPLACE INTO counter_evidences
            (evidence_id, thesis_id, counter_to, evidence_type, description,
             data_source, severity, confidence, human_reviewed,
             human_assessment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence.evidence_id,
                evidence.thesis_id,
                evidence.counter_to,
                evidence.evidence_type.value,
                evidence.description,
                evidence.data_source,
                evidence.severity,
                evidence.confidence,
                evidence.human_reviewed,
                evidence.human_assessment,
                evidence.created_at
            ))

        conn.commit()
        conn.close()

    def format_report_markdown(self, report: DevilsAdvocateReport) -> str:
        """生成 Markdown 格式报告"""
        md = f"# 反向验证报告 - {report.thesis.company_name} ({report.thesis.symbol})\n\n"
        md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**风险评分**: {report.risk_score:.2f}/1.00\n"
        md += f"**风险等级**: {report.risk_level.value}\n"
        md += f"**操作建议**: {report.recommendation}\n\n"
        md += f"**AI摘要**: {report.ai_summary}\n\n"
        md += "---\n\n"

        md += "## 📋 投资逻辑回顾\n\n"
        md += f"**核心逻辑**: {report.thesis.core_logic}\n\n"
        md += "**关键假设**:\n"
        for i, assumption in enumerate(report.thesis.key_assumptions, 1):
            md += f"{i}. {assumption}\n"
        md += "\n"

        if not report.counter_evidences:
            md += "## ✅ 未发现反面证据\n\n"
            return md

        md += "## ⚠️ 反面证据清单\n\n"

        # 按证据类型分组
        by_type: Dict[EvidenceType, List[CounterEvidence]] = {}
        for evidence in report.counter_evidences:
            if evidence.evidence_type not in by_type:
                by_type[evidence.evidence_type] = []
            by_type[evidence.evidence_type].append(evidence)

        type_names = {
            EvidenceType.FINANCIAL: "财务数据",
            EvidenceType.COMPETITIVE: "竞争格局",
            EvidenceType.MARKET: "市场趋势",
            EvidenceType.MANAGEMENT: "管理层行为",
            EvidenceType.REGULATORY: "监管政策",
            EvidenceType.TECHNICAL: "技术趋势"
        }

        for evidence_type, evidences in by_type.items():
            md += f"### {type_names.get(evidence_type, evidence_type.value)}\n\n"

            for evidence in sorted(evidences, key=lambda e: e.severity, reverse=True):
                severity_emoji = "🚨" if evidence.severity > 0.7 else "⚠️" if evidence.severity > 0.4 else "🔍"
                md += f"{severity_emoji} **{evidence.description}**\n\n"
                md += f"- **反驳假设**: {evidence.counter_to}\n"
                md += f"- **严重程度**: {evidence.severity:.2f}\n"
                md += f"- **可信度**: {evidence.confidence:.2f}\n"
                md += f"- **数据来源**: {evidence.data_source}\n"

                if evidence.human_reviewed:
                    md += f"- **人工评估**: {evidence.human_assessment}\n"

                md += "\n"

        md += "---\n\n"
        md += "## 🎯 后续行动\n\n"
        md += "- [ ] 针对高风险证据进行深度调研\n"
        md += "- [ ] 更新投资逻辑或调整仓位\n"
        md += "- [ ] 设置风险监控指标\n"

        return md


def main():
    """测试代码"""
    base_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation")
    db_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation/reverse_validation.db")

    validator = ReverseValidator(base_path, db_path)

    # 创建投资逻辑
    thesis = validator.create_thesis(
        symbol="000001",
        company_name="测试公司",
        core_logic="AI芯片需求爆发，公司技术领先，未来3年收入复合增长50%+",
        key_assumptions=[
            "AI市场持续高增长",
            "公司技术保持领先",
            "产能瓶颈能够解决",
            "毛利率维持在60%以上"
        ],
        expected_catalysts=[
            "新产品发布",
            "大客户订单落地",
            "行业政策支持"
        ],
        target_return=0.50,
        time_horizon="2年"
    )

    print(f"创建投资逻辑: {thesis.thesis_id}")

    # 模拟数据
    financial_data = {
        "revenue_growth": 0.08,  # 收入增长8%，低于预期
        "profit_margin": 0.12,  # 利润率12%，低于阈值
        "debt_ratio": 0.55,
        "cashflow_ratio": 0.65  # 现金流质量差
    }

    market_data = {
        "market_growth": 0.15,
        "saturation_level": 0.30,
        "demand_trend": "stable"
    }

    competitor_data = {
        "market_share": 0.18,
        "market_share_change": -0.03,  # 份额下降
        "new_entrants": 5,  # 新进入者多
        "price_war_intensity": 0.6  # 价格战激烈
    }

    # 查找反面证据
    evidences = validator.find_counter_evidences(
        thesis=thesis,
        financial_data=financial_data,
        market_data=market_data,
        competitor_data=competitor_data
    )

    print(f"\n发现 {len(evidences)} 条反面证据")

    # 生成报告
    report = validator.generate_report(thesis, evidences)
    print(f"风险评分: {report.risk_score:.2f}")
    print(f"风险等级: {report.risk_level.value}")
    print(f"建议: {report.recommendation}")

    # 生成 Markdown 报告
    md_report = validator.format_report_markdown(report)
    print("\n" + "="*60)
    print(md_report)

    # 保存到数据库
    validator.save_report(report)
    print("\n已保存到数据库")


if __name__ == "__main__":
    main()
