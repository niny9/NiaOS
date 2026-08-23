#!/usr/bin/env python3
"""
Invest OS - Management Promise Tracker
投资OS - 管理层承诺追踪模块

追踪管理层承诺的兑现情况，识别"承诺漂移"

Author: Nia OS Team
Version: 1.0.0
Created: 2026-08-18
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import sqlite3


class PromiseStatus(Enum):
    """承诺状态"""
    PENDING = "pending"  # 等待兑现
    FULFILLED = "fulfilled"  # 已兑现
    DELAYED = "delayed"  # 延期
    BROKEN = "broken"  # 未兑现
    ONGOING = "ongoing"  # 持续进行中


@dataclass
class PromiseUpdate:
    """承诺更新记录"""
    update_id: str
    update_date: str
    quarter: str
    update_content: str
    timeline_change: Optional[str] = None
    explanation: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ManagementPromise:
    """管理层承诺"""
    promise_id: str
    company_symbol: str
    company_name: str
    promised_at: str  # 承诺日期
    quarter: str  # 承诺季度
    promise_content: str  # 承诺内容
    promised_timeline: str  # 承诺的时间表 (如 "2024Q4", "2025H1")
    category: str  # 承诺类别: product/market/finance/operation
    importance: str  # 重要性: critical/high/medium/low
    status: PromiseStatus = PromiseStatus.PENDING
    tracking_history: List[PromiseUpdate] = field(default_factory=list)
    drift_score: float = 0.0  # 漂移程度 0-1
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


@dataclass
class PromiseDriftAlert:
    """承诺漂移警告"""
    alert_id: str
    promise: ManagementPromise
    drift_score: float
    drift_reasons: List[str]
    recommended_action: str
    severity: str  # low/medium/high/critical
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ManagementTracker:
    """管理层承诺追踪器"""

    def __init__(self, base_path: Path, db_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)

        # 初始化数据库
        self._init_database()

        # 承诺关键词
        self.promise_keywords = [
            "计划", "预计", "将会", "准备", "拟",
            "目标", "规划", "推出", "发布", "实现",
            "达到", "完成", "启动", "建设", "投资"
        ]

        # 时间线模式
        self.timeline_patterns = [
            r"(20\d{2})年",
            r"(20\d{2})Q([1-4])",
            r"(20\d{2})H([12])",
            r"([一二三四])季度",
            r"上半年|下半年",
            r"年内|今年|明年|后年"
        ]

    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 承诺表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS management_promises (
            promise_id TEXT PRIMARY KEY,
            company_symbol TEXT NOT NULL,
            company_name TEXT NOT NULL,
            promised_at TEXT NOT NULL,
            quarter TEXT NOT NULL,
            promise_content TEXT NOT NULL,
            promised_timeline TEXT,
            category TEXT,
            importance TEXT,
            status TEXT,
            drift_score REAL DEFAULT 0.0,
            created_at TEXT,
            updated_at TEXT
        )
        """)

        # 更新记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promise_updates (
            update_id TEXT PRIMARY KEY,
            promise_id TEXT NOT NULL,
            update_date TEXT NOT NULL,
            quarter TEXT,
            update_content TEXT,
            timeline_change TEXT,
            explanation TEXT,
            created_at TEXT,
            FOREIGN KEY (promise_id) REFERENCES management_promises(promise_id)
        )
        """)

        # 漂移警告表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drift_alerts (
            alert_id TEXT PRIMARY KEY,
            promise_id TEXT NOT NULL,
            drift_score REAL,
            drift_reasons TEXT,
            recommended_action TEXT,
            severity TEXT,
            created_at TEXT,
            FOREIGN KEY (promise_id) REFERENCES management_promises(promise_id)
        )
        """)

        conn.commit()
        conn.close()

    def extract_promises_from_text(
        self,
        text: str,
        company_symbol: str,
        company_name: str,
        document_date: str,
        quarter: str
    ) -> List[ManagementPromise]:
        """
        从文本中提取承诺

        Args:
            text: 财报、电话会议等文本
            company_symbol: 股票代码
            company_name: 公司名称
            document_date: 文档日期
            quarter: 季度

        Returns:
            提取的承诺列表
        """
        promises: List[ManagementPromise] = []

        # 按句子分割
        sentences = re.split(r'[。！？\n]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 检查是否包含承诺关键词
            has_keyword = any(kw in sentence for kw in self.promise_keywords)
            if not has_keyword:
                continue

            # 提取时间线
            timeline = self._extract_timeline(sentence)
            if not timeline:
                continue

            # 判断类别
            category = self._categorize_promise(sentence)

            # 创建承诺对象
            promise_id = f"{company_symbol}_{document_date}_{len(promises)}"
            promise = ManagementPromise(
                promise_id=promise_id,
                company_symbol=company_symbol,
                company_name=company_name,
                promised_at=document_date,
                quarter=quarter,
                promise_content=sentence,
                promised_timeline=timeline,
                category=category,
                importance="medium",  # 默认中等，需人工标记
                status=PromiseStatus.PENDING
            )

            promises.append(promise)

        return promises

    def _extract_timeline(self, text: str) -> Optional[str]:
        """从文本中提取时间线"""
        for pattern in self.timeline_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _categorize_promise(self, text: str) -> str:
        """对承诺进行分类"""
        categories = {
            "product": ["产品", "研发", "新品", "技术", "创新"],
            "market": ["市场", "销售", "渠道", "客户", "海外"],
            "finance": ["业绩", "收入", "利润", "毛利", "投资"],
            "operation": ["产能", "工厂", "生产", "效率", "成本"]
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "other"

    def save_promise(self, promise: ManagementPromise):
        """保存承诺到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO management_promises
        (promise_id, company_symbol, company_name, promised_at, quarter,
         promise_content, promised_timeline, category, importance, status,
         drift_score, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            promise.promise_id,
            promise.company_symbol,
            promise.company_name,
            promise.promised_at,
            promise.quarter,
            promise.promise_content,
            promise.promised_timeline,
            promise.category,
            promise.importance,
            promise.status.value,
            promise.drift_score,
            promise.created_at,
            promise.updated_at
        ))

        conn.commit()
        conn.close()

    def add_update(self, promise_id: str, update: PromiseUpdate):
        """添加承诺更新记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO promise_updates
        (update_id, promise_id, update_date, quarter, update_content,
         timeline_change, explanation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            update.update_id,
            promise_id,
            update.update_date,
            update.quarter,
            update.update_content,
            update.timeline_change,
            update.explanation,
            update.created_at
        ))

        conn.commit()
        conn.close()

    def calculate_drift_score(self, promise: ManagementPromise) -> float:
        """
        计算承诺漂移评分

        考虑因素：
        1. 时间表推迟次数
        2. 推迟时间长度
        3. 解释的一致性
        4. 当前状态
        """
        score = 0.0

        # 时间表推迟次数（每次 +0.2）
        timeline_changes = [u for u in promise.tracking_history if u.timeline_change]
        score += len(timeline_changes) * 0.2

        # 状态评分
        status_scores = {
            PromiseStatus.PENDING: 0.0,
            PromiseStatus.ONGOING: 0.1,
            PromiseStatus.DELAYED: 0.5,
            PromiseStatus.BROKEN: 1.0,
            PromiseStatus.FULFILLED: 0.0
        }
        score += status_scores.get(promise.status, 0.0)

        # 解释变化次数（表示摇摆不定）
        if len(promise.tracking_history) >= 3:
            explanations = [u.explanation for u in promise.tracking_history]
            unique_explanations = len(set(explanations))
            if unique_explanations >= 3:
                score += 0.3

        return min(score, 1.0)

    def get_promise(self, promise_id: str) -> Optional[ManagementPromise]:
        """获取承诺详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM management_promises WHERE promise_id = ?
        """, (promise_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # 获取更新记录
        cursor.execute("""
        SELECT * FROM promise_updates WHERE promise_id = ? ORDER BY update_date
        """, (promise_id,))

        updates = []
        for update_row in cursor.fetchall():
            update = PromiseUpdate(
                update_id=update_row[0],
                update_date=update_row[2],
                quarter=update_row[3],
                update_content=update_row[4],
                timeline_change=update_row[5],
                explanation=update_row[6],
                created_at=update_row[7]
            )
            updates.append(update)

        conn.close()

        promise = ManagementPromise(
            promise_id=row[0],
            company_symbol=row[1],
            company_name=row[2],
            promised_at=row[3],
            quarter=row[4],
            promise_content=row[5],
            promised_timeline=row[6],
            category=row[7],
            importance=row[8],
            status=PromiseStatus(row[9]),
            tracking_history=updates,
            drift_score=row[10],
            created_at=row[11],
            updated_at=row[12]
        )

        return promise

    def get_company_promises(
        self,
        company_symbol: str,
        status: Optional[PromiseStatus] = None
    ) -> List[ManagementPromise]:
        """获取公司的所有承诺"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status:
            cursor.execute("""
            SELECT promise_id FROM management_promises
            WHERE company_symbol = ? AND status = ?
            ORDER BY promised_at DESC
            """, (company_symbol, status.value))
        else:
            cursor.execute("""
            SELECT promise_id FROM management_promises
            WHERE company_symbol = ?
            ORDER BY promised_at DESC
            """, (company_symbol,))

        promise_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        promises = []
        for pid in promise_ids:
            promise = self.get_promise(pid)
            if promise:
                promises.append(promise)

        return promises

    def detect_drift_alerts(
        self,
        company_symbol: str,
        threshold: float = 0.5
    ) -> List[PromiseDriftAlert]:
        """检测承诺漂移警告"""
        promises = self.get_company_promises(company_symbol)
        alerts = []

        for promise in promises:
            if promise.status == PromiseStatus.FULFILLED:
                continue

            drift_score = self.calculate_drift_score(promise)

            if drift_score >= threshold:
                # 分析漂移原因
                drift_reasons = []

                if len([u for u in promise.tracking_history if u.timeline_change]) >= 2:
                    drift_reasons.append("时间表多次推迟")

                if promise.status == PromiseStatus.DELAYED:
                    drift_reasons.append("承诺状态为延期")

                if promise.status == PromiseStatus.BROKEN:
                    drift_reasons.append("承诺未兑现")

                # 推荐行动
                if drift_score >= 0.8:
                    severity = "critical"
                    action = "高度关注，考虑降低仓位或退出"
                elif drift_score >= 0.6:
                    severity = "high"
                    action = "重点监控，调研实际情况"
                else:
                    severity = "medium"
                    action = "持续跟踪，下季度重点关注"

                alert = PromiseDriftAlert(
                    alert_id=f"alert_{promise.promise_id}_{datetime.now().strftime('%Y%m%d')}",
                    promise=promise,
                    drift_score=drift_score,
                    drift_reasons=drift_reasons,
                    recommended_action=action,
                    severity=severity
                )

                alerts.append(alert)

                # 更新数据库中的drift_score
                promise.drift_score = drift_score
                promise.updated_at = datetime.now().isoformat()
                self.save_promise(promise)

        return alerts

    def generate_tracking_report(
        self,
        company_symbol: str,
        company_name: str
    ) -> str:
        """生成承诺追踪报告（Markdown格式）"""
        promises = self.get_company_promises(company_symbol)
        alerts = self.detect_drift_alerts(company_symbol)

        report = f"# 管理层承诺追踪报告 - {company_name} ({company_symbol})\n\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"**追踪承诺数**: {len(promises)}\n"
        report += f"**漂移警告数**: {len(alerts)}\n\n"

        report += "---\n\n"

        if alerts:
            report += "## ⚠️ 承诺漂移警告\n\n"
            for alert in sorted(alerts, key=lambda x: x.drift_score, reverse=True):
                promise = alert.promise
                severity_emoji = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "🔍",
                    "low": "ℹ️"
                }
                emoji = severity_emoji.get(alert.severity, "ℹ️")

                report += f"### {emoji} {promise.promise_content[:50]}...\n\n"
                report += f"- **承诺时间**: {promise.promised_at} ({promise.quarter})\n"
                report += f"- **承诺时间表**: {promise.promised_timeline}\n"
                report += f"- **当前状态**: {promise.status.value}\n"
                report += f"- **漂移评分**: {alert.drift_score:.2f}\n"
                report += f"- **漂移原因**: {', '.join(alert.drift_reasons)}\n"
                report += f"- **建议行动**: {alert.recommended_action}\n\n"

                if promise.tracking_history:
                    report += "**追踪历史**:\n"
                    for update in promise.tracking_history:
                        report += f"- {update.update_date} ({update.quarter}): {update.update_content}\n"
                        if update.timeline_change:
                            report += f"  - 时间表变更: {update.timeline_change}\n"
                        if update.explanation:
                            report += f"  - 解释: {update.explanation}\n"

                report += "\n---\n\n"

        # 按状态分类展示所有承诺
        report += "## 📊 承诺分类统计\n\n"

        status_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}

        for promise in promises:
            status_counts[promise.status.value] = status_counts.get(promise.status.value, 0) + 1
            category_counts[promise.category] = category_counts.get(promise.category, 0) + 1

        report += "### 按状态\n\n"
        for status, count in status_counts.items():
            report += f"- {status}: {count}\n"

        report += "\n### 按类别\n\n"
        for category, count in category_counts.items():
            report += f"- {category}: {count}\n"

        report += "\n---\n\n"
        report += "## 📋 完整承诺列表\n\n"

        for promise in promises:
            status_emoji = {
                "pending": "⏳",
                "fulfilled": "✅",
                "delayed": "⚠️",
                "broken": "❌",
                "ongoing": "🔄"
            }
            emoji = status_emoji.get(promise.status.value, "⏳")

            report += f"### {emoji} {promise.promise_content[:60]}...\n\n"
            report += f"- **ID**: `{promise.promise_id}`\n"
            report += f"- **承诺时间**: {promise.promised_at} ({promise.quarter})\n"
            report += f"- **时间表**: {promise.promised_timeline}\n"
            report += f"- **类别**: {promise.category}\n"
            report += f"- **重要性**: {promise.importance}\n"
            report += f"- **状态**: {promise.status.value}\n"
            report += f"- **漂移评分**: {promise.drift_score:.2f}\n\n"

        return report

    def export_to_json(self, company_symbol: str, output_path: Path):
        """导出承诺数据为JSON"""
        promises = self.get_company_promises(company_symbol)
        alerts = self.detect_drift_alerts(company_symbol)

        data = {
            "company_symbol": company_symbol,
            "generated_at": datetime.now().isoformat(),
            "promises": [asdict(p) for p in promises],
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "promise_id": a.promise.promise_id,
                    "drift_score": a.drift_score,
                    "drift_reasons": a.drift_reasons,
                    "recommended_action": a.recommended_action,
                    "severity": a.severity
                }
                for a in alerts
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """测试代码"""
    base_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation")
    db_path = Path("/Users/niny/NiaOS/os/invest/data/reconciliation/promises.db")

    tracker = ManagementTracker(base_path, db_path)

    # 示例：从文本提取承诺
    sample_text = """
    2024年第一季度，公司计划在下半年推出AI芯片新产品。
    我们预计2024Q4实现海外市场放量，目标是海外收入占比达到30%。
    公司将在今年完成新工厂建设，产能将提升50%。
    """

    promises = tracker.extract_promises_from_text(
        text=sample_text,
        company_symbol="000001",
        company_name="测试公司",
        document_date="2024-04-30",
        quarter="2024Q1"
    )

    for promise in promises:
        print(f"提取承诺: {promise.promise_content}")
        print(f"时间表: {promise.promised_timeline}")
        print(f"类别: {promise.category}")
        print("---")
        tracker.save_promise(promise)

    print(f"\n已保存 {len(promises)} 条承诺")


if __name__ == "__main__":
    main()
