#!/usr/bin/env python3
"""
Career Essay Studio - MBA/EMBA文书写作系统

核心功能：
1. 核心叙事线挖掘：通过AI对话找到真正的兴趣点
2. 素材筛选：基于叙事线评估和裁剪经历
3. 主文书生成：生成学校定制的初稿框架
4. 学校适配：快速拆分配比到不同学校
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到路径
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from utils.feishu_notifier import FeishuNotifier

# Anthropic SDK
try:
    import anthropic
except ImportError:
    print("❌ 未安装 anthropic SDK，请运行: pip install anthropic")
    sys.exit(1)

# ... (其余代码保持不变)
