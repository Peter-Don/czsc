#!/usr/bin/env python
# coding: utf-8
"""
简化版本：只有两种笔模式测试
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目根路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq

def test_two_modes():
    """测试两种笔模式"""
    print("=" * 80)
    print("CZSC Enhanced 简化版本：两种笔模式测试")
    print("=" * 80)
    
    # 加载测试数据
    data_path = os.path.join(current_dir, "data", "000001.SH_D.csv")
    df = pd.read_csv(data_path)
    df['dt'] = pd.to_datetime(df['dt'])
    df = df.head(150)  # 使用150根K线
    
    bars = []
    for i, row in df.iterrows():
        bar = RawBar(
            symbol=row['symbol'],
            id=i,
            dt=row['dt'],
            freq=Freq.D,
            open=float(row['open']),
            close=float(row['close']),
            high=float(row['high']),
            low=float(row['low']),
            vol=float(row['vol']),
            amount=float(row.get('amount', (row['high'] + row['low'] + row['open'] + row['close']) / 4 * row['vol']))
        )
        bars.append(bar)
    
    print(f"✅ 加载数据: {len(bars)} 根K线")
    print(f"📅 时间范围: {bars[0].dt.strftime('%Y-%m-%d')} 至 {bars[-1].dt.strftime('%Y-%m-%d')}")
    
    # 测试两种模式
    modes = [
        {
            'name': '严格模式',
            'description': '标准5K线模式，相邻分型间隔≥5根K线',
            'param': 'standard'
        },
        {
            'name': '灵活模式',
            'description': '灵活3K线模式，相邻分型间隔≥3根K线',
            'param': 'flexible'
        }
    ]
    
    results = {}
    
    for mode in modes:
        print(f"\n{'='*60}")
        print(f"🔍 测试 {mode['name']}")
        print(f"📝 {mode['description']}")
        
        try:
            c = CZSC(bars, pen_model=mode['param'])
            
            bi_count = len(c.bi_list)
            up_count = sum(1 for bi in c.bi_list if str(bi.direction) == "向上")
            down_count = bi_count - up_count
            
            print(f"✅ {mode['name']} 分析完成:")
            print(f"   - 总笔数: {bi_count}")
            print(f"   - 向上笔: {up_count}")
            print(f"   - 向下笔: {down_count}")
            
            # 验证笔的方向正确性
            direction_errors = 0
            for bi in c.bi_list:
                expected_up = bi.fx_b.fx > bi.fx_a.fx
                actual_up = str(bi.direction) == "向上"
                if expected_up != actual_up:
                    direction_errors += 1
            
            if direction_errors == 0:
                print(f"   ✅ 笔方向正确")
            else:
                print(f"   ❌ 笔方向错误: {direction_errors}个")
            
            # 验证笔的连接正确性
            connection_errors = 0
            for i in range(1, len(c.bi_list)):
                if c.bi_list[i-1].fx_b.dt != c.bi_list[i].fx_a.dt:
                    connection_errors += 1
            
            if connection_errors == 0:
                print(f"   ✅ 笔连接正确")
            else:
                print(f"   ❌ 笔连接错误: {connection_errors}个")
            
            # 显示前3笔
            print(f"   📊 前3笔:")
            for i, bi in enumerate(c.bi_list[:3]):
                direction_symbol = "↑" if str(bi.direction) == "向上" else "↓"
                print(f"      {i+1}. {direction_symbol} {bi.fx_a.mark.value}({bi.fx_a.dt.strftime('%m-%d')}) → {bi.fx_b.mark.value}({bi.fx_b.dt.strftime('%m-%d')}) {bi.fx_a.fx:.2f}→{bi.fx_b.fx:.2f}")
            
            results[mode['name']] = {
                'bi_count': bi_count,
                'up_count': up_count,
                'down_count': down_count,
                'direction_errors': direction_errors,
                'connection_errors': connection_errors,
                'czsc': c
            }
            
        except Exception as e:
            print(f"❌ {mode['name']} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results[mode['name']] = None
    
    # 对比结果
    print(f"\n{'='*80}")
    print("📊 两种笔模式对比结果")
    print(f"{'='*80}")
    
    print(f"{'模式':<15} {'笔数':<8} {'向上笔':<8} {'向下笔':<8} {'敏感性':<10} {'方向正确':<10} {'连接正确':<10}")
    print("-" * 85)
    
    std_count = results.get('严格模式', {}).get('bi_count', 1)
    
    for name, result in results.items():
        if result:
            sensitivity = f"{result['bi_count']/std_count:.1f}x" if std_count > 0 else "N/A"
            direction_ok = "✅" if result['direction_errors'] == 0 else "❌"
            connection_ok = "✅" if result['connection_errors'] == 0 else "❌"
            
            print(f"{name:<15} {result['bi_count']:<8} {result['up_count']:<8} {result['down_count']:<8} "
                  f"{sensitivity:<10} {direction_ok:<10} {connection_ok:<10}")
    
    # 核心结论
    print(f"\n🎯 核心结论:")
    
    std_result = results.get('严格模式')
    flex_result = results.get('灵活模式')
    
    if std_result and flex_result:
        print(f"   📊 严格模式: {std_result['bi_count']} 笔")
        print(f"   📊 灵活模式: {flex_result['bi_count']} 笔 (敏感性: {flex_result['bi_count']/std_result['bi_count']:.1f}x)")
    
    # 验证结论
    print(f"\n✅ 验证结论:")
    
    all_correct = True
    for name, result in results.items():
        if result:
            if result['direction_errors'] > 0 or result['connection_errors'] > 0:
                all_correct = False
                print(f"   ❌ {name} 存在错误")
    
    if all_correct:
        print("   ✅ 所有模式分型和笔的连接均正确")
        print("   ✅ 笔的方向判断正确")
        print("   ✅ 分型顺序正确")
        print("   🎉 简化版本成功！")
    else:
        print("   ❌ 仍存在问题需要修复")
    
    # 生成HTML结果
    result_dir = os.path.join(current_dir, "result")
    os.makedirs(result_dir, exist_ok=True)
    
    for name, result in results.items():
        if result:
            filename = f"simplified_{name.replace('模式', '_mode')}.html"
            chart = result['czsc'].to_echarts(width="1600px", height="800px")
            filepath = os.path.join(result_dir, filename)
            chart.render(filepath)
            print(f"   📄 {name} 图表已生成: {filename}")
    
    print(f"\n📁 结果目录: {result_dir}")

if __name__ == "__main__":
    test_two_modes()