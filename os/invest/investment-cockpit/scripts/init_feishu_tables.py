"""Initialize Feishu Bitable tables and fields automatically."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.integrations.feishu_bitable import BITABLE_SCHEMA, FeishuBitable
from src.integrations.feishu_client import FeishuClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def init_all_tables() -> None:
    """Initialize all Feishu Bitable tables and fields."""
    settings = load_app_settings()
    
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        logger.error("Feishu credentials not configured")
        return
    
    if not settings.feishu_bitable_app_token:
        logger.error("Feishu Bitable app token not configured")
        return
    
    client = FeishuClient(
        app_id=settings.feishu_app_id,
        app_secret=settings.feishu_app_secret,
    )
    bitable = FeishuBitable(client, app_token=settings.feishu_bitable_app_token)
    
    logger.info("Fetching existing tables...")
    existing_tables = bitable.list_tables()
    table_map = {t['name']: t['table_id'] for t in existing_tables}
    
    logger.info(f"Found {len(existing_tables)} existing tables")
    
    # Create or update each table
    for table_key, schema in BITABLE_SCHEMA.items():
        table_name = schema['name']
        logger.info(f"Processing table: {table_name} ({table_key})")
        
        # Create table if not exists
        if table_name not in table_map:
            logger.info(f"  Creating table: {table_name}")
            result = bitable.create_table(table_name)
            table_id = result['table_id']
            table_map[table_name] = table_id
            logger.info(f"  Created table_id: {table_id}")
        else:
            table_id = table_map[table_name]
            logger.info(f"  Table exists, table_id: {table_id}")
        
        # Get existing fields
        existing_fields = bitable.list_fields(table_id)
        existing_field_names = {f['field_name'] for f in existing_fields}
        
        # Add missing fields
        for field_def in schema['fields']:
            field_name = field_def['field_name']
            if field_name in existing_field_names:
                logger.info(f"  Field exists: {field_name}")
                continue
            
            logger.info(f"  Adding field: {field_name}")
            try:
                bitable.add_field(table_id, field_def)
                logger.info(f"  Added field: {field_name}")
            except Exception as e:
                if "FieldNameDuplicated" in str(e):
                    logger.info(f"  Field already exists: {field_name}")
                else:
                    logger.error(f"  Failed to add field {field_name}: {e}")
    
    logger.info("Feishu tables initialization completed")
    
    # Print summary
    print("\n" + "="*50)
    print("飞书多维表格初始化完成")
    print("="*50)
    print(f"\n已配置 {len(BITABLE_SCHEMA)} 张表:")
    for table_key, schema in BITABLE_SCHEMA.items():
        table_name = schema['name']
        field_count = len(schema['fields'])
        print(f"  ✓ {table_name} ({field_count} 个字段)")
    print(f"\n访问地址: https://feishu.cn/base/{settings.feishu_bitable_app_token}")
    print("\n提示: 请在飞书中手动创建仪表盘和图表进行可视化")


if __name__ == "__main__":
    init_all_tables()
