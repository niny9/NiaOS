#!/usr/bin/env python3
"""
Invest OS - AI研究链完整实现
行业分析、选股、风险评估
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path.home() / "NiaOS/os/invest"
SKILL_DIR = ROOT / "quant-core/ai-research"
DATA_DIR = SKILL_DIR / "data"

SKILL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class AIResearchChain:
    """AI研究链 - 完整实现"""

    def __init__(self):
        # 行业评级标准
        self.industry_criteria = {
            'growth_potential': '增长潜力',
            'policy_support': '政策支持',
            'market_size': '市场规模',
            'competition': '竞争格局',
            'technology': '技术壁垒'
        }

        # 公司评估标准
        self.company_criteria = {
            'financial': '财务状况',
            'management': '管理团队',
            'competitive_edge': '竞争优势',
            'growth': '成长性',
            'valuation': '估值水平'
        }

    def analyze_industry(self, industry: str) -> Dict[str, Any]:
        """
        行业分析

        评估行业前景、政策、竞争格局
        """
        logger.info(f"📊 分析行业: {industry}")

        # 模拟行业分析（真实场景应该调用AI/数据API）
        scores = {
            'growth_potential': 85,  # 0-100分
            'policy_support': 90,
            'market_size': 80,
            'competition': 70,
            'technology': 85
        }

        total_score = sum(scores.values()) / len(scores)

        # 行业评级
        if total_score >= 80:
            rating = 'A'
            outlook = '看好'
        elif total_score >= 70:
            rating = 'B'
            outlook = '中性'
        else:
            rating = 'C'
            outlook = '谨慎'

        analysis = {
            'industry': industry,
            'scores': {k: {'score': v, 'label': self.industry_criteria[k]} for k, v in scores.items()},
            'total_score': round(total_score, 1),
            'rating': rating,
            'outlook': outlook,
            'key_trends': [
                'AI技术快速发展，应用场景持续拓展',
                '政策大力支持，多项扶持政策出台',
                '市场规模持续增长，预计未来3年CAGR 30%+'
            ],
            'risks': [
                '技术迭代快，存在被颠覆风险',
                '竞争加剧，头部效应明显'
            ],
            'analyzed_at': datetime.now().isoformat()
        }

        logger.info(f"✅ 行业分析完成: {analysis['rating']}级 ({analysis['outlook']})")

        return analysis

    def select_stocks(
        self,
        industry: str,
        criteria: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        选股分析

        基于行业和标准筛选股票
        """
        logger.info(f"🎯 选股分析: {industry}")

        # 模拟选股（真实场景应该从数据库/API获取）
        candidates = [
            {
                'code': '000001',
                'name': '平安银行',
                'industry': industry,
                'market_cap': 2500,  # 亿
                'pe': 5.5,
                'pb': 0.8,
                'roe': 12.5,
                'revenue_growth': 8.5
            },
            {
                'code': '600519',
                'name': '贵州茅台',
                'industry': industry,
                'market_cap': 25000,
                'pe': 35.0,
                'pb': 12.0,
                'roe': 30.5,
                'revenue_growth': 15.0
            },
            {
                'code': '000858',
                'name': '五粮液',
                'industry': industry,
                'market_cap': 8000,
                'pe': 25.0,
                'pb': 6.0,
                'roe': 22.0,
                'revenue_growth': 12.0
            }
        ]

        # 评分和排序
        for stock in candidates:
            score = self._calculate_stock_score(stock)
            stock['score'] = score
            stock['recommendation'] = self._get_recommendation(score)

        # 按分数排序
        candidates.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"✅ 选股完成: {len(candidates)}只股票")

        return candidates

    def _calculate_stock_score(self, stock: Dict[str, Any]) -> float:
        """计算股票综合评分"""
        score = 0

        # ROE评分 (30%)
        roe = stock.get('roe', 0)
        if roe >= 20:
            score += 30
        elif roe >= 15:
            score += 25
        elif roe >= 10:
            score += 20
        else:
            score += 10

        # 增长评分 (30%)
        growth = stock.get('revenue_growth', 0)
        if growth >= 15:
            score += 30
        elif growth >= 10:
            score += 25
        elif growth >= 5:
            score += 20
        else:
            score += 10

        # 估值评分 (20%)
        pe = stock.get('pe', 0)
        if pe < 15:
            score += 20
        elif pe < 25:
            score += 15
        elif pe < 35:
            score += 10
        else:
            score += 5

        # PB评分 (20%)
        pb = stock.get('pb', 0)
        if pb < 2:
            score += 20
        elif pb < 5:
            score += 15
        elif pb < 10:
            score += 10
        else:
            score += 5

        return round(score, 1)

    def _get_recommendation(self, score: float) -> str:
        """获取投资建议"""
        if score >= 80:
            return '强烈推荐'
        elif score >= 70:
            return '推荐'
        elif score >= 60:
            return '中性'
        else:
            return '观望'

    def assess_risk(
        self,
        stock: Dict[str, Any],
        portfolio: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        风险评估

        评估单只股票和组合风险
        """
        logger.info(f"⚠️ 风险评估: {stock['name']}")

        risks = {
            'market_risk': self._assess_market_risk(stock),
            'valuation_risk': self._assess_valuation_risk(stock),
            'liquidity_risk': self._assess_liquidity_risk(stock),
            'industry_risk': self._assess_industry_risk(stock)
        }

        # 综合风险评分
        total_risk = sum(r['score'] for r in risks.values()) / len(risks)

        # 风险等级
        if total_risk >= 70:
            risk_level = '高风险'
            color = '🔴'
        elif total_risk >= 40:
            risk_level = '中风险'
            color = '🟡'
        else:
            risk_level = '低风险'
            color = '🟢'

        assessment = {
            'stock': f"{stock['code']} {stock['name']}",
            'risks': risks,
            'total_risk_score': round(total_risk, 1),
            'risk_level': f"{color} {risk_level}",
            'recommendations': self._generate_risk_recommendations(risks, total_risk),
            'assessed_at': datetime.now().isoformat()
        }

        logger.info(f"✅ 风险评估完成: {assessment['risk_level']}")

        return assessment

    def _assess_market_risk(self, stock: Dict) -> Dict:
        """市场风险"""
        # 基于市值评估
        market_cap = stock.get('market_cap', 0)
        if market_cap > 10000:
            score = 20  # 大盘股风险低
        elif market_cap > 5000:
            score = 40
        else:
            score = 60  # 小盘股风险高

        return {'score': score, 'description': '市场系统性风险'}

    def _assess_valuation_risk(self, stock: Dict) -> Dict:
        """估值风险"""
        pe = stock.get('pe', 0)
        if pe > 40:
            score = 80  # 高估值高风险
        elif pe > 25:
            score = 50
        else:
            score = 20  # 低估值低风险

        return {'score': score, 'description': '估值过高风险'}

    def _assess_liquidity_risk(self, stock: Dict) -> Dict:
        """流动性风险"""
        # 基于市值简化评估
        market_cap = stock.get('market_cap', 0)
        if market_cap > 5000:
            score = 10  # 大盘流动性好
        elif market_cap > 1000:
            score = 30
        else:
            score = 60  # 小盘流动性差

        return {'score': score, 'description': '流动性不足风险'}

    def _assess_industry_risk(self, stock: Dict) -> Dict:
        """行业风险"""
        # 简化评估
        return {'score': 30, 'description': '行业政策和竞争风险'}

    def _generate_risk_recommendations(
        self,
        risks: Dict,
        total_risk: float
    ) -> List[str]:
        """生成风险建议"""
        recommendations = []

        if total_risk >= 60:
            recommendations.append('风险较高，建议降低仓位或观望')

        # 针对具体风险
        if risks['valuation_risk']['score'] > 60:
            recommendations.append('估值偏高，注意回调风险')

        if risks['liquidity_risk']['score'] > 50:
            recommendations.append('流动性较差，注意交易成本')

        if not recommendations:
            recommendations.append('风险可控，可适度配置')

        return recommendations

    def generate_research_report(
        self,
        industry: str
    ) -> Dict[str, Any]:
        """
        生成完整研究报告
        """
        logger.info(f"📋 生成AI研究报告: {industry}")

        # 1. 行业分析
        industry_analysis = self.analyze_industry(industry)

        # 2. 选股
        stock_candidates = self.select_stocks(industry)

        # 3. 风险评估（对推荐股票）
        risk_assessments = []
        for stock in stock_candidates[:3]:  # 评估前3只
            risk = self.assess_risk(stock)
            risk_assessments.append(risk)

        # 4. 生成报告
        report = {
            'title': f'{industry} - AI研究报告',
            'generated_at': datetime.now().isoformat(),
            'industry_analysis': industry_analysis,
            'stock_recommendations': stock_candidates,
            'risk_assessments': risk_assessments,
            'summary': {
                'industry_rating': industry_analysis['rating'],
                'top_pick': stock_candidates[0]['name'] if stock_candidates else None,
                'avg_risk': sum(r['total_risk_score'] for r in risk_assessments) / len(risk_assessments) if risk_assessments else 0
            }
        }

        # 保存报告
        report_file = DATA_DIR / f"research_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 研究报告已生成")

        return report


def main():
    research = AIResearchChain()

    print("\n" + "="*60)
    print("AI研究链测试")
    print("="*60)

    # 生成完整报告
    report = research.generate_research_report('AI科技')

    print(f"\n报告标题: {report['title']}")

    print(f"\n行业分析:")
    industry = report['industry_analysis']
    print(f"  评级: {industry['rating']}")
    print(f"  展望: {industry['outlook']}")
    print(f"  综合得分: {industry['total_score']}")

    print(f"\n股票推荐 (Top 3):")
    for i, stock in enumerate(report['stock_recommendations'][:3], 1):
        print(f"  {i}. {stock['name']} ({stock['code']})")
        print(f"     评分: {stock['score']} | {stock['recommendation']}")
        print(f"     PE: {stock['pe']} | ROE: {stock['roe']}%")

    print(f"\n风险评估:")
    for risk in report['risk_assessments']:
        print(f"  {risk['stock']}: {risk['risk_level']} (风险分: {risk['total_risk_score']})")

    print(f"\n总结:")
    print(f"  行业评级: {report['summary']['industry_rating']}")
    print(f"  首选股票: {report['summary']['top_pick']}")
    print(f"  平均风险: {report['summary']['avg_risk']:.1f}")

    print(f"\n✅ AI研究链测试完成")


if __name__ == '__main__':
    main()
