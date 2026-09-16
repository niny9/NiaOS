"""Feishu bot notification module."""

from __future__ import annotations

from typing import Any, Dict, List

import requests


class FeishuBot:
    """Send notifications via Feishu bot webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_text(self, text: str) -> bool:
        """Send plain text message."""
        payload = {"msg_type": "text", "content": {"text": text}}
        return self._send(payload)

    def send_rich_text(self, title: str, content: List[List[Dict[str, Any]]]) -> bool:
        """Send rich text message with formatting."""
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": content,
                    }
                }
            },
        }
        return self._send(payload)

    def send_daily_signal_notification(
        self,
        signals: List[Dict[str, Any]],
        bitable_url: str,
        status: str = "success",
    ) -> bool:
        """Send daily signal notification."""
        title = "📊 投资驾驶舱 - 每日信号更新成功" if status == "success" else "⚠️ 投资驾驶舱 - 任务执行异常"
        content: List[List[Dict[str, Any]]] = []

        content.append(
            [
                {"tag": "text", "text": f"✅ 任务状态：{status}\n"},
                {"tag": "text", "text": f"📈 信号数量：{len(signals)} 条\n\n"},
            ]
        )

        if signals:
            content.append([{"tag": "text", "text": "今日推荐：\n"}])
            for i, signal in enumerate(signals[:10], 1):
                strategy_emoji = {"short_term": "⚡", "swing": "🌊", "stable": "🛡️"}.get(signal.get("signal", ""), "📊")
                score = float(signal.get("score", 0) or 0)
                line = (
                    f"{i}. {strategy_emoji} {signal.get('code', 'N/A')} "
                    f"{signal.get('name', 'N/A')} "
                    f"[{signal.get('signal', 'N/A')}] "
                    f"得分:{score:.1f}\n"
                )
                content.append([{"tag": "text", "text": line}])

        content.append(
            [
                {"tag": "text", "text": "\n📊 查看详情："},
                {"tag": "a", "text": "飞书多维表格", "href": bitable_url},
            ]
        )
        return self.send_rich_text(title, content)

    def _send(self, payload: Dict[str, Any]) -> bool:
        """Send request to webhook."""
        if not self.webhook_url:
            print("Failed to send Feishu bot message: webhook url is empty")
            return False

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("code") == 0
        except Exception as exc:
            print(f"Failed to send Feishu bot message: {exc}")
            return False
