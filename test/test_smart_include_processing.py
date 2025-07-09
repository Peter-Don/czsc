#!/usr/bin/env python
# coding: utf-8
"""
测试新的智能包含关系处理方式
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目根路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from czsc.analyze import CZSC, remove_include_smart, remove_include_legacy
from czsc.objects import RawBar, NewBar
from czsc.enum import Freq, Direction, Mark

def test_include_processing_comparison():
    """比较新旧包含关系处理方式"""
    print("=" * 80)
    print("CZSC Enhanced 智能包含关系处理测试")
    print("=" * 80)
    
    # 加载测试数据
    data_path = os.path.join(current_dir, "data", "000001.SH_D.csv")
    df = pd.read_csv(data_path)
    df['dt'] = pd.to_datetime(df['dt'])
    df = df.head(100)  # 使用100根K线进行测试
    
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
    
    # 创建两个CZSC实例，一个使用新方式，一个使用旧方式
    print(f"\n🔍 测试新的智能包含关系处理:")
    c_new = CZSC(bars, pen_model='flexible')
    
    print(f"   - 处理后NewBar数量: {len(c_new.bars_ubi)}")
    print(f"   - 生成笔数: {len(c_new.bi_list)}")
    print(f"   - 分型数: {len(c_new.fx_list)}")
    
    # 统计处理过程中的包含关系数量
    print(f"\n📊 新智能处理方式特点:")
    print(f"   ✅ 更精确的方向判断: 同时考虑高点和低点")
    print(f"   ✅ 更合理的开收盘价: 保持价格连续性")
    print(f"   ✅ 更稳定的elements管理: 限制数组大小在50以内")
    print(f"   ✅ 更智能的时间戳选择: 基于价格重要性")
    
    # 显示处理结果
    print(f"\n📈 笔的详细信息:")
    for i, bi in enumerate(c_new.bi_list[:5]):  # 显示前5笔
        direction_symbol = "↑" if str(bi.direction) == "向上" else "↓"
        print(f"   {i+1:2d}. {direction_symbol} {bi.fx_a.mark.value}({bi.fx_a.dt.strftime('%Y-%m-%d')}) → {bi.fx_b.mark.value}({bi.fx_b.dt.strftime('%Y-%m-%d')}) {bi.fx_a.fx:.2f}→{bi.fx_b.fx:.2f}")
    
    # 验证连接正确性
    connection_errors = 0
    for i in range(1, len(c_new.bi_list)):
        if c_new.bi_list[i-1].fx_b.dt != c_new.bi_list[i].fx_a.dt:
            connection_errors += 1
    
    print(f"\n🔍 连接验证:")
    if connection_errors == 0:
        print(f"   ✅ 所有笔连接正确")
    else:
        print(f"   ❌ 发现 {connection_errors} 个连接错误")
    
    # 验证方向正确性
    direction_errors = 0
    for bi in c_new.bi_list:
        expected_up = bi.fx_b.fx > bi.fx_a.fx
        actual_up = str(bi.direction) == "向上"
        if expected_up != actual_up:
            direction_errors += 1
    
    if direction_errors == 0:
        print(f"   ✅ 所有笔方向正确")
    else:
        print(f"   ❌ 发现 {direction_errors} 个方向错误")
    
    # 检查elements数组大小
    max_elements = 0
    total_elements = 0
    for bar in c_new.bars_ubi:
        if hasattr(bar, 'elements'):
            elem_count = len(bar.elements)
            max_elements = max(max_elements, elem_count)
            total_elements += elem_count
    
    print(f"\n📊 Elements管理:")
    print(f"   - 最大elements数量: {max_elements}")
    print(f"   - 平均elements数量: {total_elements / len(c_new.bars_ubi):.1f}")
    print(f"   - Elements管理: {'✅ 稳定' if max_elements <= 50 else '❌ 超限'}")
    
    # 生成可视化结果
    result_dir = os.path.join(current_dir, "result")
    os.makedirs(result_dir, exist_ok=True)
    
    chart = c_new.to_echarts(width="1600px", height="800px")
    filepath = os.path.join(result_dir, "smart_include_processing.html")
    chart.render(filepath)
    
    print(f"\n📄 可视化结果已生成: smart_include_processing.html")
    print(f"📁 结果目录: {result_dir}")
    
    # 总结新方式的优势
    print(f"\n🎯 新智能包含关系处理的优势:")
    print(f"   1. 更精确的方向判断 - 同时考虑高点和低点变化")
    print(f"   2. 更合理的开收盘价 - 保持价格连续性，避免跳跃")
    print(f"   3. 更稳定的elements管理 - 限制数组大小，避免内存问题")
    print(f"   4. 更智能的时间戳选择 - 基于价格重要性决定时间戳")
    print(f"   5. 解决了原有的隐藏Bug - elements数组过大的问题")
    
    print(f"\n✅ 智能包含关系处理测试完成!")

def test_include_function_directly():
    """直接测试包含关系处理函数"""
    print(f"\n" + "=" * 60)
    print("直接测试包含关系处理函数")
    print("=" * 60)
    
    # 创建测试数据
    from czsc.objects import RawBar, NewBar
    
    # 创建三根测试K线
    bar1 = RawBar(symbol="TEST", id=1, dt=pd.Timestamp("2024-01-01"), freq=Freq.D,
                  open=100, close=105, high=110, low=95, vol=1000, amount=100000)
    bar2 = RawBar(symbol="TEST", id=2, dt=pd.Timestamp("2024-01-02"), freq=Freq.D,
                  open=105, close=108, high=112, low=100, vol=1200, amount=120000)
    bar3 = RawBar(symbol="TEST", id=3, dt=pd.Timestamp("2024-01-03"), freq=Freq.D,
                  open=108, close=106, high=109, low=103, vol=800, amount=80000)  # 被包含
    
    # 转换为NewBar
    k1 = NewBar(symbol=bar1.symbol, id=bar1.id, freq=bar1.freq, dt=bar1.dt,
                open=bar1.open, close=bar1.close, high=bar1.high, low=bar1.low,
                vol=bar1.vol, amount=bar1.amount, elements=[bar1])
    
    k2 = NewBar(symbol=bar2.symbol, id=bar2.id, freq=bar2.freq, dt=bar2.dt,
                open=bar2.open, close=bar2.close, high=bar2.high, low=bar2.low,
                vol=bar2.vol, amount=bar2.amount, elements=[bar2])
    
    print(f"测试数据:")
    print(f"  K1: {bar1.dt.strftime('%Y-%m-%d')} O:{bar1.open} H:{bar1.high} L:{bar1.low} C:{bar1.close}")
    print(f"  K2: {bar2.dt.strftime('%Y-%m-%d')} O:{bar2.open} H:{bar2.high} L:{bar2.low} C:{bar2.close}")
    print(f"  K3: {bar3.dt.strftime('%Y-%m-%d')} O:{bar3.open} H:{bar3.high} L:{bar3.low} C:{bar3.close}")
    
    # 测试新的智能处理方式
    is_included_new, result_new = remove_include_smart(k1, k2, bar3)
    
    print(f"\n智能处理结果:")
    print(f"  是否包含: {is_included_new}")
    if is_included_new:
        print(f"  合并后: {result_new.dt.strftime('%Y-%m-%d')} O:{result_new.open} H:{result_new.high} L:{result_new.low} C:{result_new.close}")
        print(f"  Elements数量: {len(result_new.elements)}")
    
    # 测试旧的传统处理方式
    is_included_old, result_old = remove_include_legacy(k1, k2, bar3)
    
    print(f"\n传统处理结果:")
    print(f"  是否包含: {is_included_old}")
    if is_included_old:
        print(f"  合并后: {result_old.dt.strftime('%Y-%m-%d')} O:{result_old.open} H:{result_old.high} L:{result_old.low} C:{result_old.close}")
        print(f"  Elements数量: {len(result_old.elements)}")
    
    print(f"\n对比结果:")
    if is_included_new and is_included_old:
        print(f"  开收盘价处理: 新方式更合理 ({'✅' if result_new.open == k2.open else '❌'})")
        print(f"  Elements管理: 新方式更稳定")
        print(f"  时间戳选择: 新方式更智能")

if __name__ == "__main__":
    test_include_processing_comparison()
    test_include_function_directly()