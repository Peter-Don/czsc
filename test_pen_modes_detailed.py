#!/usr/bin/env python
# coding: utf-8
"""
详细的笔模式对比测试，包括可视化分析
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Dict, Any

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 添加项目路径
sys.path.insert(0, '/home/moses2204/proj/czsc_enhanced')

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq, Direction

def read_test_data(limit: int = 200) -> List[RawBar]:
    """读取测试数据"""
    cur_path = os.path.dirname(os.path.abspath(__file__))
    file_kline = os.path.join(cur_path, "test/data/000001.SH_D.csv")
    
    kline = pd.read_csv(file_kline, encoding="utf-8")
    kline['amount'] = kline['close'] * kline['vol']
    kline.loc[:, "dt"] = pd.to_datetime(kline.dt)
    
    bars = [RawBar(symbol=row['symbol'], id=i, freq=Freq.D, open=row['open'], dt=row['dt'],
                   close=row['close'], high=row['high'], low=row['low'], vol=row['vol'], amount=row['amount'])
            for i, row in kline.iterrows()]
    
    return bars[:limit]

def create_comparison_chart(bars: List[RawBar], results: Dict[str, Any]):
    """创建对比图表"""
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    
    # 准备K线数据
    dates = [bar.dt for bar in bars]
    closes = [bar.close for bar in bars]
    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    
    colors = ['blue', 'red', 'green']
    mode_names = ['标准模式', '灵活模式', '自适应模式']
    
    for i, (mode_name, color) in enumerate(zip(mode_names, colors)):
        ax = axes[i]
        
        # 绘制K线价格
        ax.plot(dates, closes, color='black', linewidth=1, alpha=0.7, label='收盘价')
        ax.fill_between(dates, lows, highs, alpha=0.1, color='gray', label='价格区间')
        
        # 绘制笔
        if mode_name in results and results[mode_name]:
            bi_list = results[mode_name]['bi_list']
            
            # 绘制笔的连线
            for j, bi in enumerate(bi_list):
                start_dt = bi.fx_a.dt
                end_dt = bi.fx_b.dt
                start_price = bi.fx_a.fx
                end_price = bi.fx_b.fx
                
                line_color = 'red' if bi.direction == Direction.Up else 'blue'
                ax.plot([start_dt, end_dt], [start_price, end_price], 
                       color=line_color, linewidth=2, alpha=0.8)
                
                # 标注笔的序号
                mid_dt = start_dt + (end_dt - start_dt) / 2
                mid_price = (start_price + end_price) / 2
                ax.text(mid_dt, mid_price, str(j+1), fontsize=8, 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        ax.set_title(f'{mode_name} - 笔数: {len(results[mode_name]["bi_list"]) if mode_name in results and results[mode_name] else 0}', 
                    fontsize=14, fontweight='bold')
        ax.set_ylabel('价格', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 设置日期格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig('/home/moses2204/proj/czsc_enhanced/pen_modes_comparison.png', dpi=300, bbox_inches='tight')
    print("📊 对比图表已保存至: pen_modes_comparison.png")

def analyze_bi_transitions(bi_list) -> Dict[str, Any]:
    """分析笔的转折特征"""
    if len(bi_list) < 2:
        return {}
    
    transitions = []
    for i in range(1, len(bi_list)):
        prev_bi = bi_list[i-1]
        curr_bi = bi_list[i]
        
        # 计算转折强度
        transition_strength = abs(curr_bi.change) + abs(prev_bi.change)
        
        # 计算时间间隔
        time_gap = (curr_bi.sdt - prev_bi.edt).days
        
        transitions.append({
            'index': i,
            'strength': transition_strength,
            'time_gap': time_gap,
            'prev_direction': prev_bi.direction,
            'curr_direction': curr_bi.direction
        })
    
    return {
        'transitions': transitions,
        'avg_strength': sum(t['strength'] for t in transitions) / len(transitions),
        'avg_time_gap': sum(t['time_gap'] for t in transitions) / len(transitions)
    }

def detailed_comparison():
    """详细对比分析"""
    print("="*80)
    print("CZSC Enhanced 详细笔模式对比分析")
    print("="*80)
    
    # 读取更多数据用于详细分析
    bars = read_test_data(limit=200)
    print(f"✅ 读取测试数据: {len(bars)} 根K线")
    print(f"时间范围: {bars[0].dt.date()} 到 {bars[-1].dt.date()}")
    
    # 测试配置
    test_configs = [
        {
            'name': '标准模式',
            'params': {'market_type': 'stock'}
        },
        {
            'name': '灵活模式', 
            'params': {'pen_model': 'flexible', 'market_type': 'stock'}
        },
        {
            'name': '自适应模式',
            'params': {
                'pen_model': 'flexible',
                'use_adaptive_pen': True,
                'adaptive_vol_ratio': 1.8,  # 降低阈值以便观察效果
                'adaptive_atr_ratio': 1.2,
                'market_type': 'stock'
            }
        }
    ]
    
    results = {}
    
    # 执行分析
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"分析 {config['name']}")
        
        try:
            c = CZSC(bars, **config['params'])
            
            # 基础统计
            bi_count = len(c.bi_list)
            up_count = sum(1 for bi in c.bi_list if bi.direction == Direction.Up)
            down_count = bi_count - up_count
            
            # 转折分析
            transition_analysis = analyze_bi_transitions(c.bi_list)
            
            results[config['name']] = {
                'bi_list': c.bi_list,
                'bi_count': bi_count,
                'up_count': up_count,
                'down_count': down_count,
                'transition_analysis': transition_analysis,
                'czsc_obj': c
            }
            
            print(f"✅ 笔数: {bi_count} (向上: {up_count}, 向下: {down_count})")
            
            if transition_analysis:
                print(f"   平均转折强度: {transition_analysis['avg_strength']:.2%}")
                print(f"   平均时间间隔: {transition_analysis['avg_time_gap']:.1f} 天")
                
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            results[config['name']] = None
    
    # 生成对比报告
    print(f"\n{'='*80}")
    print("📊 详细对比报告")
    print(f"{'='*80}")
    
    # 1. 基础统计对比
    print("\n1. 基础统计对比:")
    print(f"{'模式':<15} {'总笔数':<10} {'向上笔':<10} {'向下笔':<10} {'平均转折强度':<15} {'平均时间间隔':<15}")
    print("-" * 85)
    
    for name, result in results.items():
        if result:
            trans = result['transition_analysis']
            avg_strength = trans['avg_strength'] if trans else 0
            avg_gap = trans['avg_time_gap'] if trans else 0
            
            print(f"{name:<15} {result['bi_count']:<10} {result['up_count']:<10} {result['down_count']:<10} "
                  f"{avg_strength:<15.2%} {avg_gap:<15.1f}")
    
    # 2. 敏感性分析
    print("\n2. 敏感性分析:")
    standard_count = results['标准模式']['bi_count'] if results['标准模式'] else 0
    flexible_count = results['灵活模式']['bi_count'] if results['灵活模式'] else 0
    adaptive_count = results['自适应模式']['bi_count'] if results['自适应模式'] else 0
    
    if standard_count > 0:
        flex_ratio = flexible_count / standard_count
        adaptive_ratio = adaptive_count / standard_count
        
        print(f"   - 灵活模式相对标准模式敏感性: {flex_ratio:.1f}x")
        print(f"   - 自适应模式相对标准模式敏感性: {adaptive_ratio:.1f}x")
        print(f"   - 灵活模式额外识别笔数: {flexible_count - standard_count}")
        print(f"   - 自适应模式额外识别笔数: {adaptive_count - standard_count}")
    
    # 3. 创建对比图表
    print(f"\n3. 生成可视化对比图表...")
    try:
        create_comparison_chart(bars[:100], results)  # 使用前100根K线绘图
    except Exception as e:
        print(f"⚠️  图表生成失败: {e}")
    
    # 4. 实际案例分析
    print(f"\n4. 实际案例分析:")
    print("   以下是每种模式识别的前5笔详情:")
    
    for name, result in results.items():
        if result and result['bi_list']:
            print(f"\n   {name}:")
            for i, bi in enumerate(result['bi_list'][:5]):
                direction = "↑" if bi.direction == Direction.Up else "↓"
                print(f"     笔{i+1}: {direction} {bi.sdt.strftime('%Y-%m-%d')} → {bi.edt.strftime('%Y-%m-%d')} "
                      f"({bi.change:+.2%}, {bi.length}根K线)")
    
    # 5. 使用建议
    print(f"\n5. 使用建议:")
    print("   - 标准模式: 适用于中长期趋势分析，信号稳定但较少")
    print("   - 灵活模式: 适用于短期交易，能捕捉更多转折点")
    print("   - 自适应模式: 适用于波动性较大的市场，能识别突发性转折")
    
    print(f"\n{'='*80}")
    print("✅ 详细分析完成")
    print(f"{'='*80}")

if __name__ == "__main__":
    detailed_comparison()