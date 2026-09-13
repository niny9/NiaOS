#!/usr/bin/env python3
"""
Career Precision Applier - AI驱动的精准投递工作流

核心功能：
1. 岗位匹配挖掘：基于简历推荐TOP10岗位 + 能力拆解
2. STAR简历改写：生成STAR简历底稿 + 可复用素材库
3. 定向物料生成：一岗一版定制简历 + 打招呼话术
4. 投递复盘迭代：分析投递效果，优化策略
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


class CareerPrecisionApplier:
    """精准投递工作流核心类"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化Anthropic客户端
        api_key = self._load_api_key()
        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://cc-vibe.com/v1")
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

        # 初始化飞书通知（可选）
        self.notifier = FeishuNotifier()

    def _load_api_key(self) -> str:
        """加载API Key"""
        key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if key:
            return key

        # 尝试从配置文件读取
        config_candidates = [
            ROOT / "config" / "api_keys.json",
            ROOT / "config" / "llm_config.json",
        ]

        for cfg in config_candidates:
            if not cfg.exists():
                continue
            try:
                with open(cfg, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    key = data.get("ANTHROPIC_API_KEY") or data.get("CLAUDE_API_KEY")
                    if key:
                        return key
            except Exception:
                continue

        raise RuntimeError("未找到 Claude API key，请设置 ANTHROPIC_API_KEY 环境变量")

    def match_positions(self, resume_file: str, constraints_file: str) -> Dict:
        """
        Step 1: 岗位匹配挖掘

        Args:
            resume_file: 原始简历文件路径
            constraints_file: 求职约束文件路径（目标城市、期望薪资等）

        Returns:
            岗位匹配表（TOP10岗位 + 硬技能 + 软技能）
        """
        print("🔍 Step 1: 岗位匹配挖掘...")

        # 读取输入文件
        with open(resume_file, 'r', encoding='utf-8') as f:
            resume_content = f.read()
        with open(constraints_file, 'r', encoding='utf-8') as f:
            constraints_content = f.read()

        # 构造Prompt
        prompt = f"""你现在是业务面试官，基于下面这份简历和我的求职约束完成任务：

1. 输出TOP10最匹配我的岗位名称，标注所属行业，标记哪些属于当下高薪赛道；
2. 针对每一个岗位，拆解岗位核心能力，分成硬技能、软技能两个清单；
   - 硬技能指工具、技术栈、专业能力、证书
   - 软技能指项目推进、跨部门协作这类业务素养
3. 结果整理成JSON格式，禁止编造岗位。

简历内容：
{resume_content}

求职约束：
{constraints_content}

输出JSON Schema:
{{
  "top_positions": [
    {{
      "position_name": "岗位名称",
      "industry": "所属行业",
      "high_salary_track": true/false,
      "hard_skills": ["技能1", "技能2"],
      "soft_skills": ["能力1", "能力2"]
    }}
  ]
}}
"""

        # 调用Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        # 提取文本内容
        result_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result_text = block.text
                break

        # 提取JSON（处理可能的markdown代码块包裹）
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)

        # 保存结果
        output_file = self.output_dir / "01_岗位匹配表.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"✅ 岗位匹配完成，输出：{output_file}")
        print(f"   推荐了 {len(result['top_positions'])} 个岗位")

        return result

    def rewrite_star_resume(self, resume_file: str, keywords_file: str) -> Dict:
        """
        Step 2: STAR简历改写

        Args:
            resume_file: 原始简历文件路径
            keywords_file: Step1输出的关键词文件

        Returns:
            包含STAR简历底稿和素材库的字典
        """
        print("✍️ Step 2: STAR简历改写...")

        # 读取输入
        with open(resume_file, 'r', encoding='utf-8') as f:
            resume_content = f.read()
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords_data = json.load(f)

        # 合并所有关键词
        all_keywords = set()
        for pos in keywords_data['top_positions']:
            all_keywords.update(pos['hard_skills'])
            all_keywords.update(pos['soft_skills'])
        keywords_str = "、".join(all_keywords)

        # 构造Prompt
        prompt = f"""你是求职简历优化师，严格遵守规则改写简历：

1. 绝不编造项目经历、业绩数据，只能基于我提供的真实经历重组；
2. 每一段工作/项目经历使用STAR法则重构：情境S、任务T、行动A、结果R；
3. 结果尽量量化，无精确数字就写客观可验证成果，禁止捏造数据；
4. 自然植入岗位关键词，不要堆砌；
5. 输出两份内容：
   - 通用STAR简历底稿（markdown格式，可导出PDF）
   - 简历素材库（把每一条STAR案例单独拆分，方便后续按需抽取修改）

简历原文：
{resume_content}

关键词库：{keywords_str}

输出JSON Schema:
{{
  "star_resume_base": "完整的STAR格式简历markdown内容",
  "star_material_lib": [
    {{
      "title": "案例标题",
      "situation": "情境描述",
      "task": "任务描述",
      "action": "行动描述",
      "result": "结果描述",
      "applicable_positions": ["适用岗位1", "适用岗位2"],
      "key_metrics": ["关键数据1", "关键数据2"]
    }}
  ]
}}
"""

        # 调用Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        # 提取文本内容
        result_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result_text = block.text
                break

        # 提取JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)

        # 保存STAR简历底稿
        base_file = self.output_dir / "02_STAR简历底稿.md"
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(result['star_resume_base'])

        # 保存素材库
        lib_dir = self.output_dir / "03_STAR素材库"
        lib_dir.mkdir(exist_ok=True)

        for i, material in enumerate(result['star_material_lib'], 1):
            material_file = lib_dir / f"案例{i:02d}_{material['title']}.json"
            with open(material_file, 'w', encoding='utf-8') as f:
                json.dump(material, f, ensure_ascii=False, indent=2)

        print(f"✅ STAR简历改写完成")
        print(f"   - 底稿：{base_file}")
        print(f"   - 素材库：{len(result['star_material_lib'])} 个案例")

        return result

    def generate_application_materials(self, jd_file: str, resume_base: str) -> Dict:
        """
        Step 3: 定向岗位物料生成

        Args:
            jd_file: 岗位JD文件路径
            resume_base: STAR简历底稿文件路径

        Returns:
            岗位台账条目（含匹配度、定制简历、打招呼话术）
        """
        print(f"🎯 Step 3: 生成岗位物料 - {Path(jd_file).name}")

        # 读取输入
        with open(jd_file, 'r', encoding='utf-8') as f:
            jd_content = f.read()
        with open(resume_base, 'r', encoding='utf-8') as f:
            resume_content = f.read()

        # 构造Prompt
        prompt = f"""根据这份岗位JD和我的STAR简历底稿完成任务：

1. 给出岗位匹配度0-100分，写明打分理由；
2. 基于JD关键词微调简历底稿，生成专属附件简历文本（一岗一版）；
   注意：这份内容用于导出PDF附件投递，不要修改BOSS平台在线简历；
3. 写BOSS打招呼开场白，控制80字以内，弱化模板感，突出1个和JD匹配的核心项目经历。

JD内容：
{jd_content}

简历底稿：
{resume_content}

输出JSON Schema:
{{
  "match_score": 85,
  "match_reason": "打分理由说明",
  "customized_resume": "定制简历完整markdown内容",
  "greeting_message": "打招呼话术"
}}
"""

        # 调用Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}]
        )

        # 提取文本内容
        result_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result_text = block.text
                break

        # 提取JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)

        # 添加元数据
        jd_filename = Path(jd_file).stem
        result['jd_file'] = jd_filename
        result['applied_date'] = None
        result['is_read'] = False
        result['got_interview'] = False

        # 追加到岗位台账
        ledger_file = self.output_dir / "04_岗位台账.jsonl"
        with open(ledger_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

        # 保存定制简历
        resume_file = self.output_dir / f"定制简历_{jd_filename}.md"
        with open(resume_file, 'w', encoding='utf-8') as f:
            f.write(result['customized_resume'])

        print(f"✅ 岗位物料生成完成")
        print(f"   - 匹配度：{result['match_score']}分")
        print(f"   - 定制简历：{resume_file}")

        return result

    def review_applications(self, ledger_file: str) -> Dict:
        """
        Step 4: 投递复盘

        Args:
            ledger_file: 岗位台账文件路径

        Returns:
            投递复盘报告
        """
        print("📊 Step 4: 投递复盘...")

        # 读取台账
        applications = []
        with open(ledger_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    applications.append(json.loads(line))

        # 统计分析
        total = len(applications)
        read_count = sum(1 for app in applications if app.get('is_read', False))
        interview_count = sum(1 for app in applications if app.get('got_interview', False))

        read_rate = (read_count / total * 100) if total > 0 else 0
        interview_rate = (interview_count / total * 100) if total > 0 else 0

        # 分析最佳案例（简化版，实际应使用AI分析）
        interviewed = [app for app in applications if app.get('got_interview', False)]
        best_position_type = "未知" if not interviewed else interviewed[0]['jd_file']

        report = {
            "total_applied": total,
            "total_read": read_count,
            "total_interview": interview_count,
            "read_rate": round(read_rate, 2),
            "interview_rate": round(interview_rate, 2),
            "insights": {
                "best_position_type": best_position_type,
                "best_star_case": "需要AI深度分析",
                "suggested_optimization": "根据面试邀约情况优化简历素材库"
            }
        }

        # 保存报告
        report_file = self.output_dir / "05_投递复盘报告.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 投递复盘完成：{report_file}")
        print(f"   - 已读率：{read_rate:.1f}%")
        print(f"   - 面试率：{interview_rate:.1f}%")

        return report


def main():
    parser = argparse.ArgumentParser(description='Career Precision Applier')
    parser.add_argument('--mode', required=True,
                       choices=['match', 'rewrite', 'generate', 'review', 'full'],
                       help='运行模式')
    parser.add_argument('--resume-file', help='原始简历文件路径')
    parser.add_argument('--constraints-file', help='求职约束文件路径')
    parser.add_argument('--keywords-file', help='关键词文件路径（Step1输出）')
    parser.add_argument('--jd-file', help='岗位JD文件路径')
    parser.add_argument('--resume-base', help='STAR简历底稿路径')
    parser.add_argument('--ledger-file', help='岗位台账文件路径')
    parser.add_argument('--output-dir', default='~/Asset/Career OS/精准投递',
                       help='输出目录')

    args = parser.parse_args()

    # 扩展路径
    output_dir = os.path.expanduser(args.output_dir)

    # 创建实例
    applier = CareerPrecisionApplier(output_dir)

    try:
        if args.mode == 'match':
            if not args.resume_file or not args.constraints_file:
                print("❌ match模式需要 --resume-file 和 --constraints-file")
                sys.exit(1)
            result = applier.match_positions(args.resume_file, args.constraints_file)

        elif args.mode == 'rewrite':
            if not args.resume_file or not args.keywords_file:
                print("❌ rewrite模式需要 --resume-file 和 --keywords-file")
                sys.exit(1)
            result = applier.rewrite_star_resume(args.resume_file, args.keywords_file)

        elif args.mode == 'generate':
            if not args.jd_file or not args.resume_base:
                print("❌ generate模式需要 --jd-file 和 --resume-base")
                sys.exit(1)
            result = applier.generate_application_materials(args.jd_file, args.resume_base)

        elif args.mode == 'review':
            if not args.ledger_file:
                print("❌ review模式需要 --ledger-file")
                sys.exit(1)
            result = applier.review_applications(args.ledger_file)

        elif args.mode == 'full':
            if not args.resume_file or not args.constraints_file:
                print("❌ full模式需要 --resume-file 和 --constraints-file")
                sys.exit(1)
            # 执行Step 1 + 2
            match_result = applier.match_positions(args.resume_file, args.constraints_file)
            keywords_file = os.path.join(output_dir, "01_岗位匹配表.json")
            rewrite_result = applier.rewrite_star_resume(args.resume_file, keywords_file)

            print("\n" + "="*60)
            print("✅ 完整流程执行完成！")
            print("="*60)
            print(f"📁 输出目录：{output_dir}")
            print(f"   - 01_岗位匹配表.json（{len(match_result['top_positions'])}个岗位）")
            print(f"   - 02_STAR简历底稿.md")
            print(f"   - 03_STAR素材库/（{len(rewrite_result['star_material_lib'])}个案例）")
            print("\n下一步：")
            print("1. 查看岗位匹配表，选择感兴趣的岗位")
            print("2. 去BOSS直聘筛选岗位，复制JD到文本文件")
            print("3. 运行 --mode generate 批量生成定制简历和打招呼话术")

        print("\n✅ 任务完成")

    except Exception as e:
        print(f"\n❌ 执行失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
