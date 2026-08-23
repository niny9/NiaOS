#!/usr/bin/env python3
"""
Invest OS - Dual Track Fusion
投资OS - 双轨融合系统

AI主观研究 + 数据客观技术 → 人工确认Gate → 交易执行

Author: Nia OS Team
Version: 1.0
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ai_research_track import AIResearchTrack, StockResearch
from quant_signal_track import QuantSignalTrack, QuantSignal, SignalType


class FusionSignal(Enum):
    """融合信号"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    CONFLICT = "conflict"  # AI和量化信号冲突


@dataclass
class FusionRecommendation:
    """融合推荐"""
    symbol: str
    name: str
    ai_thesis: str
    ai_confidence: float
    quant_score: float
    quant_confidence: float
    fusion_signal: FusionSignal
    fusion_score: float  # 综合得分
    suggested_allocation: float  # 建议配置比例
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon: str = "medium"
    needs_human_approval: bool = True
    approval_reason: str = ""
    created_at: str = ""


@dataclass
class HumanApproval:
    """人工审批"""
    recommendation_id: str
    approved: bool
    approver: str
    comments: str
    approved_at: str


@dataclass
class PaperTrade:
    """模拟交易"""
    trade_id: str
    symbol: str
    action: str  # buy, sell
    quantity: int
    price: float
    total_value: float
    executed_at: str
    strategy: str  # 策略来源


class DualTrackFusion:
    """双轨融合系统"""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.recommendations_file = self.base_path / "recommendations.json"
        self.approvals_file = self.base_path / "approvals.json"
        self.paper_trades_file = self.base_path / "paper_trades.json"

        self.recommendations: Dict[str, FusionRecommendation] = {}
        self.approvals: Dict[str, HumanApproval] = {}
        self.paper_trades: List[PaperTrade] = []

        self._load_all()

    def _load_all(self):
        """加载所有数据"""
        if self.recommendations_file.exists():
            with open(self.recommendations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for rec_data in data.values():
                    rec_data['fusion_signal'] = FusionSignal(rec_data['fusion_signal'])
                    self.recommendations[rec_data['symbol']] = FusionRecommendation(**rec_data)

        if self.approvals_file.exists():
            with open(self.approvals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for approval_data in data.values():
                    self.approvals[approval_data['recommendation_id']] = HumanApproval(**approval_data)

        if self.paper_trades_file.exists():
            with open(self.paper_trades_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.paper_trades = [PaperTrade(**trade) for trade in data]

    def _save_all(self):
        """保存所有数据"""
        # 保存推荐
        with open(self.recommendations_file, 'w', encoding='utf-8') as f:
            json.dump({
                symbol: {
                    'symbol': rec.symbol,
                    'name': rec.name,
                    'ai_thesis': rec.ai_thesis,
                    'ai_confidence': rec.ai_confidence,
                    'quant_score': rec.quant_score,
                    'quant_confidence': rec.quant_confidence,
                    'fusion_signal': rec.fusion_signal.value,
                    'fusion_score': rec.fusion_score,
                    'suggested_allocation': rec.suggested_allocation,
                    'entry_price': rec.entry_price,
                    'target_price': rec.target_price,
                    'stop_loss': rec.stop_loss,
                    'time_horizon': rec.time_horizon,
                    'needs_human_approval': rec.needs_human_approval,
                    'approval_reason': rec.approval_reason,
                    'created_at': rec.created_at
                }
                for symbol, rec in self.recommendations.items()
            }, f, indent=2, ensure_ascii=False)

        # 保存审批
        with open(self.approvals_file, 'w', encoding='utf-8') as f:
            json.dump({
                rec_id: {
                    'recommendation_id': approval.recommendation_id,
                    'approved': approval.approved,
                    'approver': approval.approver,
                    'comments': approval.comments,
                    'approved_at': approval.approved_at
                }
                for rec_id, approval in self.approvals.items()
            }, f, indent=2, ensure_ascii=False)

        # 保存模拟交易
        with open(self.paper_trades_file, 'w', encoding='utf-8') as f:
            json.dump([
                {
                    'trade_id': trade.trade_id,
                    'symbol': trade.symbol,
                    'action': trade.action,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'total_value': trade.total_value,
                    'executed_at': trade.executed_at,
                    'strategy': trade.strategy
                }
                for trade in self.paper_trades
            ], f, indent=2, ensure_ascii=False)

    def fuse_signals(
        self,
        ai_research: StockResearch,
        quant_signal: QuantSignal,
        current_price: float
    ) -> FusionRecommendation:
        """融合AI研究和量化信号"""
        # AI信心度（基于时间跨度和研究质量）
        ai_confidence = 0.7  # 默认信心度

        # 量化信号转换
        quant_score = quant_signal.composite_score

        # 信号一致性检查
        ai_positive = ai_research.target_price and ai_research.target_price > current_price if ai_research.target_price else True
        quant_positive = quant_signal.signal in [SignalType.BUY, SignalType.STRONG_BUY]

        if ai_positive and quant_positive:
            # 双轨都看多
            fusion_signal = FusionSignal.STRONG_BUY if quant_signal.signal == SignalType.STRONG_BUY else FusionSignal.BUY
            fusion_score = (quant_score * 0.6 + 50 * 0.4)  # 量化权重更高
            needs_approval = False
            approval_reason = "AI和量化信号一致，双轨共振"
        elif not ai_positive and not quant_positive:
            # 双轨都看空
            fusion_signal = FusionSignal.SELL
            fusion_score = quant_score * 0.8
            needs_approval = False
            approval_reason = "双轨一致看空"
        else:
            # 信号冲突
            fusion_signal = FusionSignal.CONFLICT
            fusion_score = 0
            needs_approval = True
            approval_reason = "AI和量化信号冲突，需要人工判断"

        # 计算建议配置
        if fusion_signal in [FusionSignal.STRONG_BUY]:
            suggested_allocation = min(0.10, quant_signal.confidence * 0.15)  # 最高10%
        elif fusion_signal == FusionSignal.BUY:
            suggested_allocation = min(0.05, quant_signal.confidence * 0.08)  # 最高5%
        else:
            suggested_allocation = 0.0

        # 计算止损价
        stop_loss = current_price * 0.92 if fusion_signal in [FusionSignal.BUY, FusionSignal.STRONG_BUY] else None

        recommendation = FusionRecommendation(
            symbol=ai_research.symbol,
            name=ai_research.name,
            ai_thesis=ai_research.thesis,
            ai_confidence=ai_confidence,
            quant_score=quant_score,
            quant_confidence=quant_signal.confidence,
            fusion_signal=fusion_signal,
            fusion_score=fusion_score,
            suggested_allocation=suggested_allocation,
            entry_price=current_price,
            target_price=ai_research.target_price,
            stop_loss=stop_loss,
            time_horizon=ai_research.time_horizon,
            needs_human_approval=needs_approval,
            approval_reason=approval_reason,
            created_at=datetime.now().isoformat()
        )

        self.recommendations[ai_research.symbol] = recommendation
        self._save_all()

        return recommendation

    def submit_for_approval(self, symbol: str) -> bool:
        """提交人工审批"""
        if symbol not in self.recommendations:
            return False

        recommendation = self.recommendations[symbol]
        recommendation.needs_human_approval = True
        self._save_all()

        return True

    def approve_recommendation(
        self,
        symbol: str,
        approved: bool,
        approver: str,
        comments: str
    ) -> HumanApproval:
        """人工审批推荐"""
        if symbol not in self.recommendations:
            raise ValueError(f"推荐不存在: {symbol}")

        approval = HumanApproval(
            recommendation_id=symbol,
            approved=approved,
            approver=approver,
            comments=comments,
            approved_at=datetime.now().isoformat()
        )

        self.approvals[symbol] = approval

        # 更新推荐状态
        self.recommendations[symbol].needs_human_approval = False
        self._save_all()

        return approval

    def execute_paper_trade(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        strategy: str = "dual_track"
    ) -> PaperTrade:
        """执行模拟交易"""
        trade_id = f"trade_{datetime.now().timestamp()}"

        trade = PaperTrade(
            trade_id=trade_id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            total_value=quantity * price,
            executed_at=datetime.now().isoformat(),
            strategy=strategy
        )

        self.paper_trades.append(trade)
        self._save_all()

        return trade

    def get_pending_approvals(self) -> List[FusionRecommendation]:
        """获取待审批推荐"""
        return [
            rec for rec in self.recommendations.values()
            if rec.needs_human_approval and rec.symbol not in self.approvals
        ]

    def get_approved_recommendations(self) -> List[FusionRecommendation]:
        """获取已批准推荐"""
        approved_symbols = {
            rec_id for rec_id, approval in self.approvals.items()
            if approval.approved
        }

        return [
            rec for symbol, rec in self.recommendations.items()
            if symbol in approved_symbols
        ]

    def generate_dashboard(self) -> str:
        """生成投资仪表盘"""
        dashboard = f"# 投资仪表盘\n\n"
        dashboard += f"**更新时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

        # 待审批
        pending = self.get_pending_approvals()
        dashboard += f"## 待审批 ({len(pending)})\n\n"
        for rec in pending:
            dashboard += f"### {rec.name} ({rec.symbol})\n"
            dashboard += f"- **信号:** {rec.fusion_signal.value}\n"
            dashboard += f"- **融合得分:** {rec.fusion_score:.1f}\n"
            dashboard += f"- **建议配置:** {rec.suggested_allocation:.1%}\n"
            dashboard += f"- **原因:** {rec.approval_reason}\n\n"

        # 已批准
        approved = self.get_approved_recommendations()
        dashboard += f"## 已批准 ({len(approved)})\n\n"
        for rec in approved:
            approval = self.approvals.get(rec.symbol)
            dashboard += f"### {rec.name} ({rec.symbol})\n"
            dashboard += f"- **入场价:** ${rec.entry_price:.2f}\n"
            if rec.target_price:
                dashboard += f"- **目标价:** ${rec.target_price:.2f}\n"
            if rec.stop_loss:
                dashboard += f"- **止损价:** ${rec.stop_loss:.2f}\n"
            if approval:
                dashboard += f"- **审批人:** {approval.approver}\n"
                dashboard += f"- **备注:** {approval.comments}\n"
            dashboard += "\n"

        # 模拟交易记录
        dashboard += f"## 模拟交易 ({len(self.paper_trades)})\n\n"
        for trade in self.paper_trades[-10:]:  # 最近10笔
            dashboard += f"- **{trade.symbol}** {trade.action.upper()} {trade.quantity}股 @ ${trade.price:.2f} ({trade.executed_at[:10]})\n"

        return dashboard


def create_dual_track_fusion(base_path: Optional[str] = None) -> DualTrackFusion:
    """创建双轨融合系统"""
    if base_path is None:
        default_path = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/03_fusion"
        return DualTrackFusion(default_path)
    return DualTrackFusion(Path(base_path))
