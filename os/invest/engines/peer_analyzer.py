#!/usr/bin/env python3
"""
Invest OS - Peer Cross-Check Analyzer
投资OS - 同行交叉验证模块

上下游公司财报对比，发现"特殊"表述

Author: Nia OS Team
Version: 1.0.0
Created: 2026-08-18
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Sentiment(Enum):
    """情绪"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class WarningLevel(Enum):
    """警告级别"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PeerStatement:
    """公司表述"""
    company_symbol: str
    company_name: str
    quarter: str
    topic: str
    statement: str
    sentiment: Sentiment
    key_metrics: Dict[str, float]
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class CrossValidation:
    """交叉验证结果"""
    validation_id: str
    topic: str
    quarter: str
    target_company: PeerStatement
    peer_statements: List[PeerStatement]
    upstream_statements: List[PeerStatement]
    downstream_statements: List[PeerStatement]
    consensus_view: str
    outliers: List[str]
    ai_analysis: str
    warning_level: WarningLevel
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class PeerAnalyzer:
    """同行分析器"""

    def __init__(self, base_path: Path, db_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS peer_statements (
            statement_id TEXT PRIMARY KEY,
            company_symbol TEXT,
            company_name TEXT,
            quarter TEXT,
            topic TEXT,
            statement TEXT,
            sentiment TEXT,
            key_metrics TEXT,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cross_validations (
            validation_id TEXT PRIMARY KEY,
            topic TEXT,
            quarter TEXT,
            target_company TEXT,
            consensus_view TEXT,
            outliers TEXT,
            ai_analysis TEXT,
            warning_level TEXT,
            created_at TEXT
        )
        """)

        conn.commit()
        conn.close()

    def analyze_topic(
        self,
        topic: str,
        quarter: str,
        target: PeerStatement,
        peers: List[PeerStatement],
        upstream: List[PeerStatement] = [],
        downstream: List[PeerStatement] = []
    ) -> CrossValidation:
        """分析某个主题的一致性"""
        
        all_statements = [target] + peers + upstream + downstream
        
        # 情绪统计
        sentiments = [s.sentiment for s in all_statements]
        positive_count = sentiments.count(Sentiment.POSITIVE)
        negative_count = sentiments.count(Sentiment.NEGATIVE)
        
        # 确定共识
        if positive_count > len(all_statements) * 0.6:
            consensus = "行业整体乐观"
        elif negative_count > len(all_statements) * 0.6:
            consensus = "行业整体悲观"
        else:
            consensus = "行业观点分歧"
        
        # 识别异常
        outliers: List[str] = []
        if target.sentiment == Sentiment.POSITIVE and negative_count > positive_count:
            outliers.append(f"{target.company_name}过于乐观")
        elif target.sentiment == Sentiment.NEGATIVE and positive_count > negative_count:
            outliers.append(f"{target.company_name}过于悲观")
        
        # 评估警告级别
        warning = WarningLevel.NONE
        if outliers:
            warning = WarningLevel.HIGH if len(outliers) > 2 else WarningLevel.MEDIUM
        
        ai_analysis = f"{topic}：{consensus}。目标公司观点{'一致' if not outliers else '存在偏差'}。"
        
        validation = CrossValidation(
            validation_id=f"{target.company_symbol}_{quarter}_{topic}",
            topic=topic,
            quarter=quarter,
            target_company=target,
            peer_statements=peers,
            upstream_statements=upstream,
            downstream_statements=downstream,
            consensus_view=consensus,
            outliers=outliers,
            ai_analysis=ai_analysis,
            warning_level=warning
        )
        
        return validation

    def generate_report(self, validation: CrossValidation) -> str:
        md = f"# 同行交叉验证 - {validation.target_company.company_name}\n\n"
        md += f"**主题**: {validation.topic}\n"
        md += f"**季度**: {validation.quarter}\n"
        md += f"**共识观点**: {validation.consensus_view}\n"
        md += f"**警告级别**: {validation.warning_level.value}\n\n"
        
        if validation.outliers:
            md += "## ⚠️ 异常发现\n\n"
            for outlier in validation.outliers:
                md += f"- {outlier}\n"
            md += "\n"
        
        md += f"**AI分析**: {validation.ai_analysis}\n"
        return md


def main():
    base_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation")
    db_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation/peer.db")
    
    analyzer = PeerAnalyzer(base_path, db_path)
    
    target = PeerStatement(
        company_symbol="000001",
        company_name="目标公司",
        quarter="2024Q1",
        topic="市场需求",
        statement="市场需求旺盛，订单饱满",
        sentiment=Sentiment.POSITIVE,
        key_metrics={"revenue_growth": 0.30}
    )
    
    peers = [
        PeerStatement("000002", "同行A", "2024Q1", "市场需求",
                     "需求平稳，竞争激烈", Sentiment.NEUTRAL, {}),
        PeerStatement("000003", "同行B", "2024Q1", "市场需求",
                     "需求疲软，价格承压", Sentiment.NEGATIVE, {})
    ]
    
    validation = analyzer.analyze_topic("市场需求", "2024Q1", target, peers)
    print(analyzer.generate_report(validation))


if __name__ == "__main__":
    main()
