"""Feishu Bitable operation wrappers and schema bootstrap."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from src.integrations.feishu_client import FeishuApiError, FeishuClient

FIELD_TYPE_TEXT = 1
FIELD_TYPE_NUMBER = 2
FIELD_TYPE_SINGLE_SELECT = 3
FIELD_TYPE_DATE = 5

BITABLE_SCHEMA: Dict[str, Dict[str, Any]] = {
    "real_positions": {
        "name": "真实持仓",
        "fields": [
            {"field_name": "股票代码", "type": FIELD_TYPE_TEXT},
            {"field_name": "股票名称", "type": FIELD_TYPE_TEXT},
            {"field_name": "持仓数量", "type": FIELD_TYPE_NUMBER},
            {"field_name": "成本价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "当前价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "市值", "type": FIELD_TYPE_NUMBER},
            {"field_name": "盈亏金额", "type": FIELD_TYPE_NUMBER},
            {"field_name": "盈亏比例", "type": FIELD_TYPE_NUMBER},
            {"field_name": "仓位比例", "type": FIELD_TYPE_NUMBER},
            {"field_name": "买入日期", "type": FIELD_TYPE_DATE},
            {"field_name": "持仓类型", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "短线"}, {"name": "波段"}, {"name": "稳健"}]}},
            {"field_name": "止损位", "type": FIELD_TYPE_NUMBER},
            {"field_name": "目标价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "状态", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "持有"}, {"name": "观察"}, {"name": "计划卖出"}] }},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "real_trades": {
        "name": "交易记录",
        "fields": [
            {"field_name": "交易日期", "type": FIELD_TYPE_DATE},
            {"field_name": "股票代码", "type": FIELD_TYPE_TEXT},
            {"field_name": "股票名称", "type": FIELD_TYPE_TEXT},
            {"field_name": "操作类型", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "买入"}, {"name": "卖出"}] }},
            {"field_name": "价格", "type": FIELD_TYPE_NUMBER},
            {"field_name": "数量", "type": FIELD_TYPE_NUMBER},
            {"field_name": "金额", "type": FIELD_TYPE_NUMBER},
            {"field_name": "原因", "type": FIELD_TYPE_TEXT},
            {"field_name": "是否按模型", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "是"}, {"name": "否"}] }},
            {"field_name": "偏离原因", "type": FIELD_TYPE_TEXT},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "daily_signals": {
        "name": "每日信号",
        "fields": [
            {"field_name": "日期", "type": FIELD_TYPE_DATE},
            {"field_name": "股票代码", "type": FIELD_TYPE_TEXT},
            {"field_name": "股票名称", "type": FIELD_TYPE_TEXT},
            {"field_name": "策略类型", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "短线"}, {"name": "波段"}, {"name": "稳健"}] }},
            {"field_name": "综合得分", "type": FIELD_TYPE_NUMBER},
            {"field_name": "推荐理由", "type": FIELD_TYPE_TEXT},
            {"field_name": "趋势因子分数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "动量因子分数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "成交量因子分数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "新闻因子分数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "基本面因子分数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "行业因子分数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "买入触发", "type": FIELD_TYPE_TEXT},
            {"field_name": "入场价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "目标价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "止损位", "type": FIELD_TYPE_NUMBER},
            {"field_name": "仓位比例", "type": FIELD_TYPE_NUMBER},
            {"field_name": "预期收益", "type": FIELD_TYPE_NUMBER},
            {"field_name": "风险收益比", "type": FIELD_TYPE_NUMBER},
            {"field_name": "风险等级", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "低"}, {"name": "中"}, {"name": "高"}] }},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "factor_radar": {
        "name": "因子雷达数据",
        "fields": [
            {"field_name": "日期", "type": FIELD_TYPE_DATE},
            {"field_name": "股票代码", "type": FIELD_TYPE_TEXT},
            {"field_name": "股票名称", "type": FIELD_TYPE_TEXT},
            {"field_name": "策略类型", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "短线"}, {"name": "波段"}, {"name": "稳健"}]}},
            {"field_name": "因子名称", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "趋势因子"}, {"name": "动量因子"}, {"name": "成交量因子"}, {"name": "新闻因子"}, {"name": "基本面因子"}, {"name": "行业因子"}]}},
            {"field_name": "因子分数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "watchlist": {
        "name": "股票池",
        "fields": [
            {"field_name": "股票代码", "type": FIELD_TYPE_TEXT},
            {"field_name": "股票名称", "type": FIELD_TYPE_TEXT},
            {"field_name": "一级分类", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "算力基础设施"}, {"name": "半导体"}, {"name": "光通信"}, {"name": "软件"}, {"name": "AI应用"}, {"name": "智能硬件"}] }},
            {"field_name": "二级分类", "type": FIELD_TYPE_TEXT},
            {"field_name": "池状态", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "核心池"}, {"name": "观察池"}, {"name": "事件池"}, {"name": "波段池"}, {"name": "剔除池"}, {"name": "禁买池"}] }},
            {"field_name": "加入日期", "type": FIELD_TYPE_DATE},
            {"field_name": "备注", "type": FIELD_TYPE_TEXT},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "weekly_review": {
        "name": "周度复盘",
        "fields": [
            {"field_name": "周次", "type": FIELD_TYPE_TEXT},
            {"field_name": "开始日期", "type": FIELD_TYPE_DATE},
            {"field_name": "结束日期", "type": FIELD_TYPE_DATE},
            {"field_name": "短线组合收益", "type": FIELD_TYPE_NUMBER},
            {"field_name": "波段组合收益", "type": FIELD_TYPE_NUMBER},
            {"field_name": "稳健组合收益", "type": FIELD_TYPE_NUMBER},
            {"field_name": "真实组合收益", "type": FIELD_TYPE_NUMBER},
            {"field_name": "推荐数量", "type": FIELD_TYPE_NUMBER},
            {"field_name": "执行数量", "type": FIELD_TYPE_NUMBER},
            {"field_name": "执行率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "主要收获", "type": FIELD_TYPE_TEXT},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "parameter_optimization_history": {
        "name": "参数优化历史",
        "fields": [
            {"field_name": "优化日期", "type": FIELD_TYPE_DATE},
            {"field_name": "旧参数版本", "type": FIELD_TYPE_TEXT},
            {"field_name": "新参数版本", "type": FIELD_TYPE_TEXT},
            {"field_name": "优化方法", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "网格"}, {"name": "随机"}, {"name": "贝叶斯"}]}},
            {"field_name": "旧Sharpe", "type": FIELD_TYPE_NUMBER},
            {"field_name": "新Sharpe", "type": FIELD_TYPE_NUMBER},
            {"field_name": "旧胜率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "新胜率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "改进幅度", "type": FIELD_TYPE_NUMBER},
            {"field_name": "是否切换", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "是"}, {"name": "否"}]}},
            {"field_name": "切换原因", "type": FIELD_TYPE_TEXT},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "signal_performance_tracking": {
        "name": "信号表现追踪",
        "fields": [
            {"field_name": "日期", "type": FIELD_TYPE_DATE},
            {"field_name": "股票代码", "type": FIELD_TYPE_TEXT},
            {"field_name": "股票名称", "type": FIELD_TYPE_TEXT},
            {"field_name": "策略类型", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "短线"}, {"name": "波段"}, {"name": "稳健"}]}},
            {"field_name": "信号日期", "type": FIELD_TYPE_DATE},
            {"field_name": "入场价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "目标价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "止损价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "当前价", "type": FIELD_TYPE_NUMBER},
            {"field_name": "持有天数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "当前收益率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "最高收益率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "最低收益率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "状态", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "持有中"}, {"name": "达到目标"}, {"name": "触发止损"}, {"name": "持有超时"}]}},
            {"field_name": "退出日期", "type": FIELD_TYPE_DATE},
            {"field_name": "退出价格", "type": FIELD_TYPE_NUMBER},
            {"field_name": "退出收益率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "退出原因", "type": FIELD_TYPE_TEXT},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
    "daily_strategy_performance": {
        "name": "每日策略表现",
        "fields": [
            {"field_name": "日期", "type": FIELD_TYPE_DATE},
            {"field_name": "策略类型", "type": FIELD_TYPE_SINGLE_SELECT, "property": {"options": [{"name": "短线"}, {"name": "波段"}, {"name": "稳健"}]}},
            {"field_name": "总信号数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "活跃信号数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "已平仓数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "盈利次数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "亏损次数", "type": FIELD_TYPE_NUMBER},
            {"field_name": "胜率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "平均收益率", "type": FIELD_TYPE_NUMBER},
            {"field_name": "平均盈利", "type": FIELD_TYPE_NUMBER},
            {"field_name": "平均亏损", "type": FIELD_TYPE_NUMBER},
            {"field_name": "盈亏比", "type": FIELD_TYPE_NUMBER},
            {"field_name": "最大收益", "type": FIELD_TYPE_NUMBER},
            {"field_name": "最大亏损", "type": FIELD_TYPE_NUMBER},
            {"field_name": "总收益", "type": FIELD_TYPE_NUMBER},
            {"field_name": "唯一键", "type": FIELD_TYPE_TEXT},
        ],
    },
}


class FeishuBitable:
    """Bitable CRUD abstraction based on Feishu open APIs."""

    def __init__(self, client: FeishuClient, app_token: Optional[str] = None) -> None:
        self.client = client
        self.app_token = (app_token or "").strip()

    def set_app_token(self, app_token: str) -> None:
        self.app_token = (app_token or "").strip()

    def _ensure_app_token(self) -> None:
        if not self.app_token:
            raise FeishuApiError("FEISHU_BITABLE_APP_TOKEN is empty. Create/select a bitable first.")

    def list_tables(self) -> List[Dict[str, Any]]:
        self._ensure_app_token()
        data = self.client.request("GET", f"/open-apis/bitable/v1/apps/{self.app_token}/tables")
        return data.get("items", [])

    def create_table(self, table_name: str) -> Dict[str, Any]:
        self._ensure_app_token()
        return self.client.request(
            "POST",
            f"/open-apis/bitable/v1/apps/{self.app_token}/tables",
            json={"table": {"name": table_name}},
        )

    def add_field(self, table_id: str, field: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_app_token()
        return self.client.request(
            "POST",
            f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields",
            json={"field": field},
        )

    def list_fields(self, table_id: str) -> List[Dict[str, Any]]:
        self._ensure_app_token()
        data = self.client.request("GET", f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields")
        return data.get("items", [])

    def list_records(
        self,
        table_id: str,
        page_token: Optional[str] = None,
        page_size: int = 500,
    ) -> Dict[str, Any]:
        self._ensure_app_token()
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        return self.client.request(
            "GET",
            f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records",
            params=params,
        )

    def create_record(self, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_app_token()
        return self.client.request(
            "POST",
            f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records",
            json={"fields": fields},
        )

    def update_record(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_app_token()
        return self.client.request(
            "PUT",
            f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}",
            json={"fields": fields},
        )

    def delete_record(self, table_id: str, record_id: str) -> Dict[str, Any]:
        self._ensure_app_token()
        return self.client.request(
            "DELETE",
            f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}",
        )

    def batch_create_records(self, table_id: str, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._ensure_app_token()
        batch = [{"fields": r} for r in records]
        return self.client.request(
            "POST",
            f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/batch_create",
            json={"records": batch},
        ).get("records", [])

    def ensure_schema(self) -> Dict[str, str]:
        """Ensure required tables exist and return mapping: logical_name -> table_id.

        Note: Field creation is skipped as Feishu API does not support adding fields programmatically.
        Users must manually add fields via the Feishu web interface.
        """
        existing = {t["name"]: t["table_id"] for t in self.list_tables()}
        mapping: Dict[str, str] = {}
        for logical, spec in BITABLE_SCHEMA.items():
            display_name = spec["name"]
            table_id = existing.get(display_name)
            if not table_id:
                created = self.create_table(display_name)
                table_id = created.get("table_id") or created.get("table", {}).get("table_id")
                if not table_id:
                    raise ValueError(f"Failed to get table_id from create_table response: {created}")
            mapping[logical] = table_id
            # Skip field creation - fields must be added manually in Feishu web interface
        return mapping
