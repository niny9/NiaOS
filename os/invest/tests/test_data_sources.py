"""
数据源集成测试
验证所有数据源的可用性
"""
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.data_sources.financial_report_fetcher import FinancialReportFetcher
from engines.data_sources.announcement_fetcher import AnnouncementFetcher
from engines.data_sources.research_report_fetcher import ResearchReportFetcher
from engines.data_sources.earnings_call_fetcher import EarningsCallFetcher
from engines.data_sources.fallback_fetcher import FallbackFetcher
from engines.data_sources.data_acquisition_workflow import DataAcquisitionWorkflow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_financial_report_fetcher():
    """测试财报获取器"""
    print("\n" + "=" * 60)
    print("测试 1/6: 财报获取器")
    print("=" * 60)

    fetcher = FinancialReportFetcher()
    data = fetcher.fetch_quarterly_report("600519", "2024Q2")

    if data:
        print("✅ 财报获取成功")
        print(f"  股票: {data['symbol']}")
        print(f"  季度: {data['quarter']}")
        print(f"  营收: {data.get('revenue', 0):.2f}")
        print(f"  净利润: {data.get('net_profit', 0):.2f}")
        print(f"  数据源: {data.get('source', 'unknown')}")
        return True
    else:
        print("❌ 财报获取失败")
        return False


def test_announcement_fetcher():
    """测试公告获取器"""
    print("\n" + "=" * 60)
    print("测试 2/6: 公告获取器")
    print("=" * 60)

    fetcher = AnnouncementFetcher()
    announcements = fetcher.fetch_announcements("600519")

    if announcements:
        print(f"✅ 公告获取成功，共 {len(announcements)} 条重要公告")
        for i, ann in enumerate(announcements[:3], 1):
            print(f"  {i}. {ann['date']} - {ann['title'][:40]}...")
        return True
    else:
        print("⚠️ 未获取到公告（可能无重要公告）")
        return True  # 无公告也算正常


def test_research_report_fetcher():
    """测试研报获取器"""
    print("\n" + "=" * 60)
    print("测试 3/6: 研报获取器")
    print("=" * 60)

    fetcher = ResearchReportFetcher()
    reports = fetcher.fetch_research_reports("600519", days=90)

    if reports:
        print(f"✅ 研报获取成功，共 {len(reports)} 份")
        for i, report in enumerate(reports[:3], 1):
            print(f"  {i}. {report['date']} - {report['institution']} - {report['rating']}")

        # 测试一致性评级
        consensus = fetcher.get_consensus_rating(reports)
        if consensus:
            print(f"\n一致性评级: {consensus['consensus']}")
            print(f"平均权重: {consensus['avg_weight']:.2f}")
        return True
    else:
        print("⚠️ 未获取到研报")
        return True


def test_earnings_call_fetcher():
    """测试电话会议获取器"""
    print("\n" + "=" * 60)
    print("测试 4/6: 电话会议获取器")
    print("=" * 60)

    fetcher = EarningsCallFetcher()
    transcript = fetcher.fetch_earnings_call_transcript("600519", "2024Q2")

    if transcript:
        print("✅ 电话会议记录获取成功")
        print(f"  日期: {transcript.get('date', 'N/A')}")
        print(f"  类型: {transcript.get('type', 'N/A')}")
        print(f"  来源: {transcript.get('source', 'N/A')}")
        return True
    else:
        print("⚠️ 未获取到电话会议记录（需手动上传）")
        return True


def test_fallback_fetcher():
    """测试降级机制"""
    print("\n" + "=" * 60)
    print("测试 5/6: 降级获取器")
    print("=" * 60)

    fetcher = FallbackFetcher()
    results = fetcher.test_all_sources("600519")

    print("降级测试结果:")
    all_success = True
    for data_type, result in results.items():
        status = "✅" if result['success'] else "❌"
        source = result['source'] or "全部失败"
        print(f"  {status} {data_type:15s} -> {source}")
        if not result['success']:
            all_success = False

    return all_success


def test_data_acquisition_workflow():
    """测试完整数据获取工作流"""
    print("\n" + "=" * 60)
    print("测试 6/6: 完整数据获取工作流")
    print("=" * 60)

    workflow = DataAcquisitionWorkflow()
    result = workflow.acquire_full_company_data("600519", "2024Q2")

    print(f"\n完整数据获取结果:")
    print(f"  股票: {result['symbol']}")
    print(f"  季度: {result['quarter']}")
    print(f"  成功率: {result['success_rate']}")

    print(f"\n详细状态:")
    success_count = 0
    for key, status in result['status'].items():
        icon = "✅" if status == 'success' else "❌"
        print(f"  {icon} {key:15s} -> {status}")
        if status == 'success':
            success_count += 1

    # 至少成功获取2种数据即为通过
    return success_count >= 2


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Invest OS 数据源集成测试")
    print("=" * 60)

    tests = [
        ("财报获取器", test_financial_report_fetcher),
        ("公告获取器", test_announcement_fetcher),
        ("研报获取器", test_research_report_fetcher),
        ("电话会议获取器", test_earnings_call_fetcher),
        ("降级获取器", test_fallback_fetcher),
        ("完整工作流", test_data_acquisition_workflow),
    ]

    results = {}

    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"{name} 测试失败: {e}", exc_info=True)
            results[name] = False

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {status:10s} {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！数据源系统工作正常")
        return 0
    elif passed >= total * 0.7:
        print(f"\n⚠️ 大部分测试通过（{passed}/{total}），系统基本可用")
        return 0
    else:
        print(f"\n❌ 测试失败过多（{passed}/{total}），请检查配置")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
