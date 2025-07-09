#!/usr/bin/env python
# coding: utf-8
"""
不同笔模式对比测试脚本
严格参照 czsc_enhanced/test/test_analyze.py 的测试方法
"""

import os
import sys
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, '/home/moses2204/proj/czsc_enhanced')

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq, Direction
from czsc.config_loader import pen_config

def read_test_data() -> List[RawBar]:
    """读取测试数据，参照 test_analyze.py 的 read_daily 函数"""
    cur_path = os.path.dirname(os.path.abspath(__file__))
    file_kline = os.path.join(cur_path, "test/data/000001.SH_D.csv")
    
    if not os.path.exists(file_kline):
        raise FileNotFoundError(f"测试数据文件不存在: {file_kline}")
    
    kline = pd.read_csv(file_kline, encoding="utf-8")
    kline['amount'] = kline['close'] * kline['vol']
    kline.loc[:, "dt"] = pd.to_datetime(kline.dt)
    
    bars = [RawBar(symbol=row['symbol'], id=i, freq=Freq.D, open=row['open'], dt=row['dt'],
                   close=row['close'], high=row['high'], low=row['low'], vol=row['vol'], amount=row['amount'])
            for i, row in kline.iterrows()]
    
    # 只取前100根K线用于测试
    return bars[:100]

def analyze_bi_characteristics(bi_list) -> Dict[str, Any]:
    """分析笔的特征统计"""
    if not bi_list:
        return {
            'total_count': 0,
            'up_count': 0,
            'down_count': 0,
            'avg_length': 0,
            'avg_change': 0,
            'max_change': 0,
            'min_change': 0
        }
    
    up_count = sum(1 for bi in bi_list if bi.direction == Direction.Up)
    down_count = len(bi_list) - up_count
    
    lengths = [bi.length for bi in bi_list]
    changes = [abs(bi.change) for bi in bi_list]
    
    return {
        'total_count': len(bi_list),
        'up_count': up_count,
        'down_count': down_count,
        'avg_length': sum(lengths) / len(lengths) if lengths else 0,
        'avg_change': sum(changes) / len(changes) if changes else 0,
        'max_change': max(changes) if changes else 0,
        'min_change': min(changes) if changes else 0
    }

def print_bi_details(bi_list, mode_name: str, max_display: int = 10):
    """打印笔的详细信息"""
    print(f"\n=== {mode_name} 笔详情 (前{max_display}笔) ===")
    
    if not bi_list:
        print("未检测到任何笔")
        return
    
    print(f"{'序号':<4} {'方向':<6} {'开始时间':<20} {'结束时间':<20} {'长度':<6} {'变化幅度':<10} {'起始价':<10} {'结束价':<10}")
    print("-" * 100)
    
    for i, bi in enumerate(bi_list[:max_display]):
        direction_str = "向上" if bi.direction == Direction.Up else "向下"
        start_time = bi.sdt.strftime("%Y-%m-%d") if bi.sdt else "N/A"
        end_time = bi.edt.strftime("%Y-%m-%d") if bi.edt else "N/A"
        
        print(f"{i+1:<4} {direction_str:<6} {start_time:<20} {end_time:<20} "
              f"{bi.length:<6} {bi.change:<10.2%} {bi.fx_a.fx:<10.2f} {bi.fx_b.fx:<10.2f}")

def compare_pen_modes():
    """对比不同笔模式的效果"""
    print("="*80)
    print("CZSC Enhanced 笔模式对比测试")
    print("="*80)
    
    # 读取测试数据
    try:
        bars = read_test_data()
        print(f"✅ 成功读取测试数据: {len(bars)} 根K线")
        print(f"数据时间范围: {bars[0].dt.date()} 到 {bars[-1].dt.date()}")
        print(f"交易对: {bars[0].symbol}")
    except Exception as e:
        print(f"❌ 读取测试数据失败: {e}")
        return
    
    # 测试不同笔模式
    test_configs = [
        {
            'name': '标准模式',
            'description': '严格5根K线笔判断，保持原始CZSC逻辑',
            'params': {
                'market_type': 'stock',
                'threshold_mode': 'moderate'
            }
        },
        {
            'name': '灵活模式',
            'description': '允许3根K线成笔，适用于快速市场',
            'params': {
                'pen_model': 'flexible',
                'market_type': 'stock', 
                'threshold_mode': 'moderate'
            }
        },
        {
            'name': '自适应模式',
            'description': '基于成交量和ATR的极端情况判断',
            'params': {
                'pen_model': 'flexible',
                'use_adaptive_pen': True,
                'adaptive_vol_ratio': 2.0,
                'adaptive_atr_ratio': 1.5,
                'market_type': 'stock',
                'threshold_mode': 'moderate'
            }
        }
    ]
    
    results = {}
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"🔍 测试 {config['name']}")
        print(f"📝 描述: {config['description']}")
        print(f"⚙️  参数: {config['params']}")
        
        try:
            # 创建CZSC分析器
            c = CZSC(bars, **config['params'])
            
            # 分析结果
            bi_stats = analyze_bi_characteristics(c.bi_list)
            results[config['name']] = {
                'stats': bi_stats,
                'bi_list': c.bi_list,
                'params': config['params']
            }
            
            print(f"✅ 分析完成:")
            print(f"   - 总笔数: {bi_stats['total_count']}")
            print(f"   - 向上笔: {bi_stats['up_count']}")
            print(f"   - 向下笔: {bi_stats['down_count']}")
            print(f"   - 平均长度: {bi_stats['avg_length']:.1f} 根K线")
            print(f"   - 平均变化幅度: {bi_stats['avg_change']:.2%}")
            print(f"   - 最大变化幅度: {bi_stats['max_change']:.2%}")
            
            # 打印详细信息
            print_bi_details(c.bi_list, config['name'])
            
        except Exception as e:
            print(f"❌ {config['name']} 测试失败: {e}")
            results[config['name']] = None
    
    # 生成对比报告
    print(f"\n{'='*80}")
    print("📊 笔模式对比报告")
    print(f"{'='*80}")
    
    print(f"{'模式':<15} {'总笔数':<8} {'向上笔':<8} {'向下笔':<8} {'平均长度':<10} {'平均变化':<10} {'最大变化':<10}")
    print("-" * 80)
    
    for name, result in results.items():
        if result is None:
            print(f"{name:<15} {'失败':<8} {'失败':<8} {'失败':<8} {'失败':<10} {'失败':<10} {'失败':<10}")
        else:
            stats = result['stats']
            print(f"{name:<15} {stats['total_count']:<8} {stats['up_count']:<8} {stats['down_count']:<8} "
                  f"{stats['avg_length']:<10.1f} {stats['avg_change']:<10.2%} {stats['max_change']:<10.2%}")
    
    # 分析差异
    print(f"\n{'='*60}")
    print("🔍 差异分析")
    print(f"{'='*60}")
    
    standard_result = results.get('标准模式')
    flexible_result = results.get('灵活模式')
    adaptive_result = results.get('自适应模式')
    
    if standard_result and flexible_result:
        std_count = standard_result['stats']['total_count']
        flex_count = flexible_result['stats']['total_count']
        diff_count = flex_count - std_count
        
        print(f"📈 灵活模式 vs 标准模式:")
        print(f"   - 笔数差异: {diff_count:+d} ({diff_count/std_count*100:+.1f}%)" if std_count > 0 else "   - 标准模式无笔")
        print(f"   - 灵活模式识别出更多短期转折点" if diff_count > 0 else "   - 笔数量相同或更少")
    
    if adaptive_result:
        ada_count = adaptive_result['stats']['total_count']
        print(f"🎯 自适应模式:")
        print(f"   - 总笔数: {ada_count}")
        print(f"   - 特点: 在极端成交量和价格波动时会产生额外的笔")
    
    # 配置信息
    print(f"\n{'='*60}")
    print("⚙️  当前配置信息")
    print(f"{'='*60}")
    
    try:
        if pen_config:
            pen_config.print_config_info()
        else:
            print("⚠️  配置加载器不可用")
    except Exception as e:
        print(f"⚠️  配置信息显示失败: {e}")
    
    print(f"\n{'='*60}")
    print("✅ 测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    compare_pen_modes()