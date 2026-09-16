"""AI industry chain seed universe initialization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from src.database.db_manager import DatabaseManager


@dataclass(frozen=True)
class SeedStock:
    """Seed stock definition."""

    code: str
    name: str
    l1: str
    l2: str
    status: str = "观察池"
    note: str = "AI产业链种子"


SEED_STOCKS: List[SeedStock] = [
    SeedStock("300308", "中际旭创", "算力基础设施", "光模块", "核心池"),
    SeedStock("300502", "新易盛", "算力基础设施", "光模块", "核心池"),
    SeedStock("300394", "天孚通信", "算力基础设施", "光器件", "核心池"),
    SeedStock("601138", "工业富联", "算力基础设施", "服务器", "核心池"),
    SeedStock("300442", "润泽科技", "算力基础设施", "IDC"),
    SeedStock("300383", "光环新网", "算力基础设施", "IDC"),
    SeedStock("300017", "网宿科技", "算力基础设施", "IDC"),
    SeedStock("300738", "奥飞数据", "算力基础设施", "IDC"),
    SeedStock("000977", "浪潮信息", "算力基础设施", "服务器", "核心池"),
    SeedStock("603019", "中科曙光", "算力基础设施", "服务器", "核心池"),
    SeedStock("002230", "科大讯飞", "软件", "大模型平台", "核心池"),
    SeedStock("688327", "云从科技", "软件", "大模型平台"),
    SeedStock("688787", "海天瑞声", "软件", "数据治理"),
    SeedStock("688111", "金山办公", "AI应用", "办公", "核心池"),
    SeedStock("300496", "中科创达", "AI应用", "智能驾驶"),
    SeedStock("002415", "海康威视", "智能硬件", "智能终端"),
    SeedStock("002475", "立讯精密", "智能硬件", "智能终端"),
    SeedStock("601360", "三六零", "软件", "大模型平台"),
    SeedStock("688256", "寒武纪", "半导体", "AI芯片", "核心池"),
    SeedStock("688041", "海光信息", "半导体", "AI芯片", "核心池"),
    SeedStock("300474", "景嘉微", "半导体", "GPU"),
    SeedStock("603986", "兆易创新", "半导体", "存储芯片"),
    SeedStock("603501", "韦尔股份", "半导体", "AI芯片"),
    SeedStock("688981", "中芯国际", "半导体", "先进封装", "核心池"),
    SeedStock("688012", "中微公司", "半导体", "设备"),
    SeedStock("002371", "北方华创", "半导体", "设备", "核心池"),
    SeedStock("300223", "北京君正", "半导体", "存储芯片"),
    SeedStock("688008", "澜起科技", "半导体", "AI芯片"),
    SeedStock("002463", "沪电股份", "光通信", "PCB"),
    SeedStock("002916", "深南电路", "光通信", "PCB", "核心池"),
    SeedStock("300570", "太辰光", "光通信", "光器件"),
    SeedStock("300620", "光库科技", "光通信", "光器件"),
    SeedStock("603083", "剑桥科技", "光通信", "光模块"),
    SeedStock("002281", "光迅科技", "光通信", "光模块", "核心池"),
    SeedStock("002436", "兴森科技", "光通信", "PCB"),
    SeedStock("300548", "博创科技", "光通信", "光模块"),
    SeedStock("002459", "晶澳科技", "智能硬件", "新能源设备"),
    SeedStock("601012", "隆基绿能", "智能硬件", "新能源设备"),
    SeedStock("300124", "汇川技术", "智能硬件", "工业自动化", "核心池"),
    SeedStock("300024", "机器人", "智能硬件", "机器人"),
    SeedStock("688017", "绿的谐波", "智能硬件", "机器人"),
    SeedStock("002747", "埃斯顿", "智能硬件", "机器人"),
    SeedStock("300450", "先导智能", "智能硬件", "工业自动化"),
    SeedStock("300274", "阳光电源", "智能硬件", "工业自动化"),
    SeedStock("300433", "蓝思科技", "智能硬件", "智能终端"),
    SeedStock("601689", "拓普集团", "智能硬件", "智能汽车"),
    SeedStock("002594", "比亚迪", "智能硬件", "智能汽车", "核心池"),
    SeedStock("601127", "赛力斯", "智能硬件", "智能汽车"),
    SeedStock("300750", "宁德时代", "智能硬件", "智能汽车", "核心池"),
    SeedStock("002517", "恺英网络", "AI应用", "AIGC"),
    SeedStock("300418", "昆仑万维", "AI应用", "AIGC"),
    SeedStock("603444", "吉比特", "AI应用", "AIGC"),
    SeedStock("600588", "用友网络", "AI应用", "行业软件"),
    SeedStock("600570", "恒生电子", "AI应用", "行业软件"),
    SeedStock("300033", "同花顺", "AI应用", "行业软件"),
    SeedStock("300803", "指南针", "AI应用", "行业软件"),
    SeedStock("002153", "石基信息", "AI应用", "行业软件"),
    SeedStock("300347", "泰格医药", "AI应用", "智能医疗"),
    SeedStock("300760", "迈瑞医疗", "AI应用", "智能医疗", "核心池"),
    SeedStock("002223", "鱼跃医疗", "AI应用", "智能医疗"),
    SeedStock("300253", "卫宁健康", "AI应用", "智能医疗"),
    SeedStock("300957", "贝泰妮", "AI应用", "智能客服"),
    SeedStock("002410", "广联达", "软件", "AI开发工具"),
    SeedStock("600845", "宝信软件", "软件", "云计算"),
    SeedStock("600536", "中国软件", "软件", "数据治理"),
    SeedStock("600100", "同方股份", "软件", "云计算"),
]


def init_ai_chain_pool(db: DatabaseManager) -> int:
    """Initialize AI chain watchlist seed stocks.

    Args:
        db: Database manager.

    Returns:
        Number of upserted stocks.
    """
    today = date.today().isoformat()
    for stock in SEED_STOCKS:
        db.upsert(
            "watchlist",
            {
                "code": stock.code,
                "name": stock.name,
                "industry_chain_l1": stock.l1,
                "industry_chain_l2": stock.l2,
                "pool_status": stock.status,
                "add_date": today,
                "note": stock.note,
                "updated_at": today,
            },
            conflict_columns=["code"],
        )
    return len(SEED_STOCKS)
