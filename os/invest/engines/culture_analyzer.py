#!/usr/bin/env python3
"""
Invest OS - Culture Analyzer
投资OS - 企业文化分析模块

多年行为模式提取，困难时期决策分析

Author: Nia OS Team
Version: 1.0.0
Created: 2026-08-18
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PatternType(Enum):
    """模式类型"""
    RD_INVESTMENT = "rd_investment"
    EMPLOYEE_TREATMENT = "employee_treatment"
    SHAREHOLDER_RETURN = "shareholder_return"
    COST_CONTROL = "cost_control"


@dataclass
class BehaviorExample:
    """行为示例"""
    date: str
    context: str
    decision: str
    outcome: Optional[str] = None


@dataclass
class BehaviorPattern:
    """行为模式"""
    pattern_id: str
    company_symbol: str
    pattern_type: PatternType
    time_span: str
    normal_behavior: str
    crisis_behavior: str
    pattern_consistency: float
    examples: List[BehaviorExample]
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class CultureProfile:
    """企业文化画像"""
    company_symbol: str
    company_name: str
    patterns: List[BehaviorPattern]
    culture_keywords: List[str]
    crisis_response_quality: float
    management_credibility: float
    ai_summary: str
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class CultureAnalyzer:
    """企业文化分析器"""

    def __init__(self, base_path: Path, db_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_patterns (
            pattern_id TEXT PRIMARY KEY,
            company_symbol TEXT,
            pattern_type TEXT,
            time_span TEXT,
            normal_behavior TEXT,
            crisis_behavior TEXT,
            pattern_consistency REAL,
            examples TEXT,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS culture_profiles (
            profile_id TEXT PRIMARY KEY,
            company_symbol TEXT,
            company_name TEXT,
            culture_keywords TEXT,
            crisis_response_quality REAL,
            management_credibility REAL,
            ai_summary TEXT,
            created_at TEXT
        )
        """)

        conn.commit()
        conn.close()

    def analyze_rd_pattern(
        self,
        company_symbol: str,
        historical_data: List[Dict]
    ) -> BehaviorPattern:
        """分析研发投入模式"""
        
        # 区分正常年份和困难年份
        normal_years = [d for d in historical_data if d.get("profit_growth", 0) > 0]
        crisis_years = [d for d in historical_data if d.get("profit_growth", 0) < -0.1]
        
        # 计算研发投入变化
        normal_rd_growth = sum(d.get("rd_growth", 0) for d in normal_years) / len(normal_years) if normal_years else 0
        crisis_rd_growth = sum(d.get("rd_growth", 0) for d in crisis_years) / len(crisis_years) if crisis_years else 0
        
        # 判断一致性
        consistency = 1.0 if crisis_rd_growth > -0.1 else 0.5
        
        normal_behavior = f"正常时期研发投入年均增长{normal_rd_growth:.1%}"
        crisis_behavior = f"困难时期{'继续投入' if crisis_rd_growth > 0 else '削减研发'}"
        
        examples = [
            BehaviorExample("2020", "疫情影响", "研发投入不降反增", "产品竞争力提升")
        ]
        
        return BehaviorPattern(
            pattern_id=f"{company_symbol}_rd",
            company_symbol=company_symbol,
            pattern_type=PatternType.RD_INVESTMENT,
            time_span="2015-2024",
            normal_behavior=normal_behavior,
            crisis_behavior=crisis_behavior,
            pattern_consistency=consistency,
            examples=examples
        )

    def generate_profile(
        self,
        company_symbol: str,
        company_name: str,
        patterns: List[BehaviorPattern]
    ) -> CultureProfile:
        """生成企业文化画像"""
        
        # 提取关键词
        keywords: List[str] = []
        for pattern in patterns:
            if pattern.pattern_type == PatternType.RD_INVESTMENT:
                if pattern.pattern_consistency > 0.7:
                    keywords.append("长期主义")
        
        # 计算危机应对质量
        crisis_quality = sum(p.pattern_consistency for p in patterns) / len(patterns) if patterns else 0.5
        
        # 管理层信用
        credibility = crisis_quality * 0.9  # 简化计算
        
        ai_summary = f"{company_name}展现出{'良好' if crisis_quality > 0.7 else '一般'}的危机应对能力。"
        
        return CultureProfile(
            company_symbol=company_symbol,
            company_name=company_name,
            patterns=patterns,
            culture_keywords=keywords,
            crisis_response_quality=crisis_quality,
            management_credibility=credibility,
            ai_summary=ai_summary
        )

    def generate_report(self, profile: CultureProfile) -> str:
        md = f"# 企业文化分析 - {profile.company_name}\n\n"
        md += f"**关键词**: {', '.join(profile.culture_keywords)}\n"
        md += f"**危机应对质量**: {profile.crisis_response_quality:.2f}\n"
        md += f"**管理层信用**: {profile.management_credibility:.2f}\n\n"
        md += f"**AI总结**: {profile.ai_summary}\n\n"
        
        for pattern in profile.patterns:
            md += f"## {pattern.pattern_type.value}\n\n"
            md += f"- **正常时期**: {pattern.normal_behavior}\n"
            md += f"- **困难时期**: {pattern.crisis_behavior}\n"
            md += f"- **一致性**: {pattern.pattern_consistency:.2f}\n\n"
        
        return md


def main():
    base_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation")
    db_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation/culture.db")
    
    analyzer = CultureAnalyzer(base_path, db_path)
    
    historical_data = [
        {"year": 2020, "profit_growth": -0.2, "rd_growth": 0.1},
        {"year": 2021, "profit_growth": 0.3, "rd_growth": 0.15},
        {"year": 2022, "profit_growth": 0.25, "rd_growth": 0.12}
    ]
    
    rd_pattern = analyzer.analyze_rd_pattern("000001", historical_data)
    profile = analyzer.generate_profile("000001", "测试公司", [rd_pattern])
    
    print(analyzer.generate_report(profile))


if __name__ == "__main__":
    main()
