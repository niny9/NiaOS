#!/usr/bin/env python3
"""
Invest OS - AI Research Track
投资OS - AI主观研究线（中长期）

行业/板块气候 → 长期配置建议 → 数据驱动验证 → ETF/基金推荐

Author: Nia OS Team
Version: 1.0
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class IndustryTrend(Enum):
    """行业趋势"""
    STRONG_GROWTH = "strong_growth"
    MODERATE_GROWTH = "moderate_growth"
    STABLE = "stable"
    DECLINING = "declining"
    CYCLICAL = "cyclical"


@dataclass
class IndustryAnalysis:
    """行业分析"""
    industry: str
    trend: IndustryTrend
    drivers: List[str]  # 驱动因素
    risks: List[str]
    confidence: float  # 0-1
    time_horizon: str  # short/medium/long
    created_at: str = ""


@dataclass
class StockResearch:
    """个股研究"""
    symbol: str
    name: str
    industry: str
    thesis: str  # 投资逻辑
    catalysts: List[str]  # 催化剂
    risks: List[str]
    target_price: Optional[float] = None
    time_horizon: str = "medium"
    created_at: str = ""


@dataclass
class PortfolioAllocation:
    """配置建议"""
    allocation_id: str
    asset_class: str  # equity, fixed_income, alternative
    allocation_pct: float
    instruments: List[str]  # 具体标的（ETF代码、股票代码等）
    rationale: str
    rebalance_trigger: str
    created_at: str = ""


class AIResearchTrack:
    """AI主观研究线"""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.industry_file = self.base_path / "industry_analysis.json"
        self.stock_file = self.base_path / "stock_research.json"
        self.allocation_file = self.base_path / "allocations.json"

        self.industries: Dict[str, IndustryAnalysis] = {}
        self.stocks: Dict[str, StockResearch] = {}
        self.allocations: Dict[str, PortfolioAllocation] = {}

        self._load_all()

    def _load_all(self):
        """加载所有数据"""
        if self.industry_file.exists():
            with open(self.industry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for industry_data in data.values():
                    industry_data['trend'] = IndustryTrend(industry_data['trend'])
                    self.industries[industry_data['industry']] = IndustryAnalysis(**industry_data)

        if self.stock_file.exists():
            with open(self.stock_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for stock_data in data.values():
                    self.stocks[stock_data['symbol']] = StockResearch(**stock_data)

        if self.allocation_file.exists():
            with open(self.allocation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for alloc_data in data.values():
                    self.allocations[alloc_data['allocation_id']] = PortfolioAllocation(**alloc_data)

    def _save_all(self):
        """保存所有数据"""
        # 保存行业分析
        with open(self.industry_file, 'w', encoding='utf-8') as f:
            json.dump({
                industry: {
                    'industry': analysis.industry,
                    'trend': analysis.trend.value,
                    'drivers': analysis.drivers,
                    'risks': analysis.risks,
                    'confidence': analysis.confidence,
                    'time_horizon': analysis.time_horizon,
                    'created_at': analysis.created_at
                }
                for industry, analysis in self.industries.items()
            }, f, indent=2, ensure_ascii=False)

        # 保存个股研究
        with open(self.stock_file, 'w', encoding='utf-8') as f:
            json.dump({
                symbol: {
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'industry': stock.industry,
                    'thesis': stock.thesis,
                    'catalysts': stock.catalysts,
                    'risks': stock.risks,
                    'target_price': stock.target_price,
                    'time_horizon': stock.time_horizon,
                    'created_at': stock.created_at
                }
                for symbol, stock in self.stocks.items()
            }, f, indent=2, ensure_ascii=False)

        # 保存配置建议
        with open(self.allocation_file, 'w', encoding='utf-8') as f:
            json.dump({
                alloc_id: {
                    'allocation_id': alloc.allocation_id,
                    'asset_class': alloc.asset_class,
                    'allocation_pct': alloc.allocation_pct,
                    'instruments': alloc.instruments,
                    'rationale': alloc.rationale,
                    'rebalance_trigger': alloc.rebalance_trigger,
                    'created_at': alloc.created_at
                }
                for alloc_id, alloc in self.allocations.items()
            }, f, indent=2, ensure_ascii=False)

    def analyze_industry(
        self,
        industry: str,
        trend: IndustryTrend,
        drivers: List[str],
        risks: List[str],
        confidence: float
    ) -> IndustryAnalysis:
        """添加行业分析"""
        analysis = IndustryAnalysis(
            industry=industry,
            trend=trend,
            drivers=drivers,
            risks=risks,
            confidence=confidence,
            time_horizon="long",
            created_at=datetime.now().isoformat()
        )

        self.industries[industry] = analysis
        self._save_all()

        return analysis

    def research_stock(
        self,
        symbol: str,
        name: str,
        industry: str,
        thesis: str,
        catalysts: List[str],
        risks: List[str],
        target_price: Optional[float] = None
    ) -> StockResearch:
        """添加个股研究"""
        research = StockResearch(
            symbol=symbol,
            name=name,
            industry=industry,
            thesis=thesis,
            catalysts=catalysts,
            risks=risks,
            target_price=target_price,
            created_at=datetime.now().isoformat()
        )

        self.stocks[symbol] = research
        self._save_all()

        return research

    def create_allocation(
        self,
        asset_class: str,
        allocation_pct: float,
        instruments: List[str],
        rationale: str,
        rebalance_trigger: str
    ) -> str:
        """创建配置建议"""
        allocation_id = f"alloc_{datetime.now().timestamp()}"

        allocation = PortfolioAllocation(
            allocation_id=allocation_id,
            asset_class=asset_class,
            allocation_pct=allocation_pct,
            instruments=instruments,
            rationale=rationale,
            rebalance_trigger=rebalance_trigger,
            created_at=datetime.now().isoformat()
        )

        self.allocations[allocation_id] = allocation
        self._save_all()

        return allocation_id

    def get_top_industries(self, limit: int = 5) -> List[IndustryAnalysis]:
        """获取最佳行业（按信心度排序）"""
        sorted_industries = sorted(
            self.industries.values(),
            key=lambda x: x.confidence,
            reverse=True
        )
        return sorted_industries[:limit]

    def get_stocks_by_industry(self, industry: str) -> List[StockResearch]:
        """获取某行业的所有个股"""
        return [stock for stock in self.stocks.values() if stock.industry == industry]

    def generate_report(self) -> str:
        """生成研究报告"""
        report = f"# 投资研究报告\n\n"
        report += f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        # 行业分析
        report += "## 行业概览\n\n"
        for industry in self.get_top_industries():
            report += f"### {industry.industry}\n"
            report += f"- **趋势:** {industry.trend.value}\n"
            report += f"- **信心度:** {industry.confidence:.0%}\n"
            report += f"- **驱动因素:** {', '.join(industry.drivers)}\n"
            report += f"- **风险:** {', '.join(industry.risks)}\n\n"

        # 个股推荐
        report += "## 个股推荐\n\n"
        for symbol, stock in self.stocks.items():
            report += f"### {stock.name} ({symbol})\n"
            report += f"- **行业:** {stock.industry}\n"
            report += f"- **投资逻辑:** {stock.thesis}\n"
            if stock.target_price:
                report += f"- **目标价:** ${stock.target_price:.2f}\n"
            report += f"- **催化剂:** {', '.join(stock.catalysts)}\n\n"

        # 配置建议
        report += "## 配置建议\n\n"
        for alloc_id, alloc in self.allocations.items():
            report += f"### {alloc.asset_class}\n"
            report += f"- **配置比例:** {alloc.allocation_pct:.1%}\n"
            report += f"- **标的:** {', '.join(alloc.instruments)}\n"
            report += f"- **理由:** {alloc.rationale}\n\n"

        return report


def create_ai_research_track(base_path: Optional[str] = None) -> AIResearchTrack:
    """创建AI研究线"""
    if base_path is None:
        default_path = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/01_ai_research"
        return AIResearchTrack(default_path)
    return AIResearchTrack(Path(base_path))
