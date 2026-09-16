#!/usr/bin/env python3
"""
Factor Evaluation - 因子评估
评估因子的有效性：IC, IR, 分层回测
"""

import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import numpy as np
import pandas as pd


def load_factor_data(db_path: str, factor_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """从数据库加载因子数据"""

    conn = sqlite3.connect(db_path)

    # 简化版：假设因子数据在 factor_scores 表
    query = f"""
        SELECT date, code, score as factor_value
        FROM factor_scores
        WHERE date BETWEEN ? AND ?
        ORDER BY date, code
    """

    try:
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        if df.empty:
            print(f"警告: 未找到因子数据")
            return pd.DataFrame()

        return df
    except Exception as e:
        print(f"警告: 加载因子数据失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def load_return_data(db_path: str, start_date: str, end_date: str) -> pd.DataFrame:
    """加载收益率数据"""

    conn = sqlite3.connect(db_path)

    query = """
        SELECT
            date,
            code,
            close,
            LAG(close) OVER (PARTITION BY code ORDER BY date) as prev_close
        FROM stock_daily_bar
        WHERE date BETWEEN ? AND ?
        ORDER BY date, code
    """

    try:
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))

        if df.empty:
            return pd.DataFrame()

        # 计算收益率
        df['return'] = (df['close'] - df['prev_close']) / df['prev_close']
        df = df.dropna()

        return df[['date', 'code', 'return']]

    except Exception as e:
        print(f"警告: 加载收益率失败: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def calculate_ic(factor_df: pd.DataFrame, return_df: pd.DataFrame) -> Dict[str, float]:
    """计算信息系数 (IC)"""

    # 合并因子和收益率
    merged = pd.merge(factor_df, return_df, on=['date', 'code'], how='inner')

    if merged.empty:
        return {'ic_mean': 0, 'ic_std': 0, 'ic_ir': 0, 'ic_positive_ratio': 0}

    # 按日期分组计算相关系数
    daily_ic = merged.groupby('date').apply(
        lambda x: x['factor_value'].corr(x['return'])
    )

    ic_mean = daily_ic.mean()
    ic_std = daily_ic.std()
    ic_ir = ic_mean / ic_std if ic_std > 0 else 0
    ic_positive_ratio = (daily_ic > 0).mean()

    return {
        'ic_mean': float(ic_mean),
        'ic_std': float(ic_std),
        'ic_ir': float(ic_ir),
        'ic_positive_ratio': float(ic_positive_ratio)
    }


def calculate_rank_ic(factor_df: pd.DataFrame, return_df: pd.DataFrame) -> Dict[str, float]:
    """计算 Rank IC（Spearman相关系数）"""

    merged = pd.merge(factor_df, return_df, on=['date', 'code'], how='inner')

    if merged.empty:
        return {'rank_ic_mean': 0, 'rank_ic_std': 0, 'rank_ic_ir': 0}

    # 按日期分组计算 Rank 相关系数
    daily_rank_ic = merged.groupby('date').apply(
        lambda x: x['factor_value'].corr(x['return'], method='spearman')
    )

    rank_ic_mean = daily_rank_ic.mean()
    rank_ic_std = daily_rank_ic.std()
    rank_ic_ir = rank_ic_mean / rank_ic_std if rank_ic_std > 0 else 0

    return {
        'rank_ic_mean': float(rank_ic_mean),
        'rank_ic_std': float(rank_ic_std),
        'rank_ic_ir': float(rank_ic_ir)
    }


def stratified_backtest(factor_df: pd.DataFrame, return_df: pd.DataFrame, n_groups: int = 5) -> Dict[str, Any]:
    """分层回测"""

    merged = pd.merge(factor_df, return_df, on=['date', 'code'], how='inner')

    if merged.empty:
        return {}

    # 按日期和因子值分组
    merged['group'] = merged.groupby('date')['factor_value'].apply(
        lambda x: pd.qcut(x, n_groups, labels=False, duplicates='drop')
    )

    # 计算每组的平均收益
    group_returns = merged.groupby(['date', 'group'])['return'].mean().unstack()

    # 计算累计收益
    cumulative_returns = (1 + group_returns).cumprod()

    # 计算每组的统计指标
    results = {}
    for group in range(n_groups):
        if group not in group_returns.columns:
            continue

        group_ret = group_returns[group]

        results[f'group_{group+1}'] = {
            'mean_return': float(group_ret.mean()),
            'std_return': float(group_ret.std()),
            'sharpe': float(group_ret.mean() / group_ret.std() * np.sqrt(252)) if group_ret.std() > 0 else 0,
            'cumulative_return': float(cumulative_returns[group].iloc[-1] - 1) if len(cumulative_returns) > 0 else 0
        }

    # 多空组合收益（最高组 - 最低组）
    if 0 in group_returns.columns and (n_groups-1) in group_returns.columns:
        long_short = group_returns[n_groups-1] - group_returns[0]
        results['long_short'] = {
            'mean_return': float(long_short.mean()),
            'std_return': float(long_short.std()),
            'sharpe': float(long_short.mean() / long_short.std() * np.sqrt(252)) if long_short.std() > 0 else 0
        }

    return results


def evaluate_factor(
    db_path: str,
    factor_name: str,
    start_date: str,
    end_date: str,
    registry_path: str
) -> Dict[str, Any]:
    """因子评估主函数"""

    print(f"📊 评估因子: {factor_name}")
    print(f"   周期: {start_date} ~ {end_date}")
    print()

    # 1. 加载数据
    print("📄 加载因子数据...")
    factor_df = load_factor_data(db_path, factor_name, start_date, end_date)

    if factor_df.empty:
        print("警告: 使用模拟因子数据")
        # 生成模拟数据
        dates = pd.date_range(start_date, end_date, freq='D')
        codes = [f'stock_{i:03d}' for i in range(10)]
        factor_df = pd.DataFrame([
            {'date': d.strftime('%Y-%m-%d'), 'code': c, 'factor_value': np.random.randn()}
            for d in dates for c in codes
        ])

    print(f"✅ 因子数据: {len(factor_df)} 条")

    print("\n📈 加载收益率数据...")
    return_df = load_return_data(db_path, start_date, end_date)

    if return_df.empty:
        print("警告: 使用模拟收益率数据")
        # 生成模拟收益率
        dates = pd.date_range(start_date, end_date, freq='D')
        codes = [f'stock_{i:03d}' for i in range(10)]
        return_df = pd.DataFrame([
            {'date': d.strftime('%Y-%m-%d'), 'code': c, 'return': np.random.randn() * 0.02}
            for d in dates for c in codes
        ])

    print(f"✅ 收益率数据: {len(return_df)} 条")

    # 2. 计算 IC
    print("\n📊 计算 IC...")
    ic_metrics = calculate_ic(factor_df, return_df)
    print(f"✅ IC 均值: {ic_metrics['ic_mean']:.4f}")
    print(f"✅ IC IR: {ic_metrics['ic_ir']:.4f}")

    # 3. 计算 Rank IC
    print("\n📊 计算 Rank IC...")
    rank_ic_metrics = calculate_rank_ic(factor_df, return_df)
    print(f"✅ Rank IC 均值: {rank_ic_metrics['rank_ic_mean']:.4f}")

    # 4. 分层回测
    print("\n📊 分层回测（5组）...")
    stratified_results = stratified_backtest(factor_df, return_df, n_groups=5)
    print(f"✅ 分层回测完成")

    # 5. 汇总结果
    evaluation = {
        'factor_name': factor_name,
        'evaluation_period': f"{start_date} ~ {end_date}",
        'ic_metrics': ic_metrics,
        'rank_ic_metrics': rank_ic_metrics,
        'stratified_backtest': stratified_results,
        'evaluated_at': datetime.now().isoformat()
    }

    # 6. 保存到 registry
    print("\n💾 保存评估结果...")
    if Path(registry_path).exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Factor Registry",
            "factors": []
        }

    # 更新因子评估结果
    found = False
    for factor in registry.get('factors', []):
        if factor.get('name') == factor_name:
            factor['evaluation'] = evaluation
            factor['last_evaluated'] = datetime.now().isoformat()
            found = True
            break

    if not found:
        registry.setdefault('factors', []).append({
            'factor_id': f"factor_{len(registry.get('factors', [])) + 1:03d}_{factor_name}",
            'name': factor_name,
            'evaluation': evaluation,
            'last_evaluated': datetime.now().isoformat()
        })

    registry['last_updated'] = datetime.now().isoformat()

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, indent=2, ensure_ascii=False, fp=f)

    print(f"✅ 已保存到: {registry_path}")

    return evaluation


def main():
    parser = argparse.ArgumentParser(description='Factor Evaluation - 因子评估')
    parser.add_argument('--factor', default='test_factor', help='因子名称')
    parser.add_argument('--start-date', default='2026-01-01', help='开始日期')
    parser.add_argument('--end-date', default='2026-06-15', help='结束日期')
    parser.add_argument(
        '--db-path',
        default='/Users/niny/NiaOS/data/invest/market_data.db',
        help='数据库路径'
    )
    parser.add_argument(
        '--registry',
        default='/Users/niny/NiaOS/configs/invest/factor_registry.json',
        help='Registry 路径'
    )

    args = parser.parse_args()

    print("🚀 Factor Evaluation 启动...")
    print()

    # 执行评估
    evaluation = evaluate_factor(
        args.db_path,
        args.factor,
        args.start_date,
        args.end_date,
        args.registry
    )

    # 输出结果
    print()
    print("=" * 60)
    print("📊 因子评估报告")
    print("=" * 60)

    print(f"\n因子: {evaluation['factor_name']}")
    print(f"周期: {evaluation['evaluation_period']}")

    print("\n📈 IC 指标:")
    ic = evaluation['ic_metrics']
    print(f"  IC 均值: {ic['ic_mean']:.4f}")
    print(f"  IC 标准差: {ic['ic_std']:.4f}")
    print(f"  IC IR: {ic['ic_ir']:.4f}")
    print(f"  IC 胜率: {ic['ic_positive_ratio']:.2%}")

    print("\n📈 Rank IC 指标:")
    rank_ic = evaluation['rank_ic_metrics']
    print(f"  Rank IC 均值: {rank_ic['rank_ic_mean']:.4f}")
    print(f"  Rank IC IR: {rank_ic['rank_ic_ir']:.4f}")

    if evaluation.get('stratified_backtest'):
        print("\n📊 分层回测结果:")
        for group_name, metrics in evaluation['stratified_backtest'].items():
            if 'long_short' in group_name:
                print(f"\n  多空组合:")
                print(f"    年化收益: {metrics['mean_return']*252:.2%}")
                print(f"    Sharpe: {metrics['sharpe']:.2f}")
            elif 'group' in group_name:
                print(f"  {group_name}: Sharpe={metrics['sharpe']:.2f}")

    print("\n✅ Factor Evaluation 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
