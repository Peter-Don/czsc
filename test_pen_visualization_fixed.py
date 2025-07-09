#!/usr/bin/env python
# coding: utf-8
"""
修复版本：使用可视化方法展示不同笔模式的效果
"""

import os
import sys
import pandas as pd
import webbrowser
from datetime import datetime
from typing import List

# 添加项目路径
sys.path.insert(0, '/home/moses2204/proj/czsc_enhanced')

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq

def read_test_data(limit: int = 120) -> List[RawBar]:
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

def safe_create_czsc(bars, config):
    """安全地创建CZSC对象"""
    try:
        return CZSC(bars, **config['params'])
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
        # 尝试使用更简单的配置
        try:
            simple_params = {k: v for k, v in config['params'].items() 
                           if k in ['pen_model', 'market_type']}
            return CZSC(bars, **simple_params)
        except Exception as e2:
            print(f"   ❌ 简化配置也失败: {e2}")
            return None

def analyze_bi_direction(bi_list):
    """分析笔的方向"""
    up_count = 0
    down_count = 0
    
    for bi in bi_list:
        if hasattr(bi, 'direction'):
            if 'Up' in str(bi.direction):
                up_count += 1
            else:
                down_count += 1
        else:
            # 根据价格变化判断方向
            if bi.fx_b.fx > bi.fx_a.fx:
                up_count += 1
            else:
                down_count += 1
    
    return up_count, down_count

def test_visualization_with_browser():
    """测试可视化并在浏览器中查看"""
    print("="*80)
    print("CZSC Enhanced 笔模式可视化测试 (修复版)")
    print("="*80)
    
    # 读取测试数据
    bars = read_test_data(limit=120)
    print(f"✅ 读取测试数据: {len(bars)} 根K线")
    print(f"时间范围: {bars[0].dt.date()} 到 {bars[-1].dt.date()}")
    
    # 测试配置
    test_configs = [
        {
            'name': '标准模式',
            'filename': 'standard_mode_visualization.html',
            'params': {
                'market_type': 'stock'
            }
        },
        {
            'name': '灵活模式',
            'filename': 'flexible_mode_visualization.html',
            'params': {
                'pen_model': 'flexible',
                'market_type': 'stock'
            }
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"🔍 分析 {config['name']}")
        print(f"⚙️  参数: {config['params']}")
        
        # 创建CZSC分析器
        c = safe_create_czsc(bars, config)
        
        if c is None:
            continue
            
        # 分析结果
        bi_count = len(c.bi_list)
        up_count, down_count = analyze_bi_direction(c.bi_list)
        
        print(f"✅ 分析完成:")
        print(f"   - 总笔数: {bi_count}")
        print(f"   - 向上笔: {up_count}")
        print(f"   - 向下笔: {down_count}")
        
        # 显示前几笔的详细信息
        if c.bi_list:
            print(f"   - 前5笔详情:")
            for i, bi in enumerate(c.bi_list[:5]):
                direction = "↑" if bi.fx_b.fx > bi.fx_a.fx else "↓"
                print(f"     笔{i+1}: {direction} {bi.sdt.strftime('%Y-%m-%d')} → {bi.edt.strftime('%Y-%m-%d')} "
                      f"({bi.change:+.2%}, {bi.length}根K线)")
        
        # 生成可视化图表
        print(f"📊 生成可视化图表...")
        
        try:
            # 使用 to_echarts() 生成HTML文件
            chart = c.to_echarts(width="1400px", height="700px")
            chart.render(config['filename'])
            print(f"   ✅ 图表已保存: {config['filename']}")
            
            # 自动在浏览器中打开
            file_path = os.path.abspath(config['filename'])
            webbrowser.open(f'file://{file_path}')
            print(f"   🌐 已在浏览器中打开")
            
        except Exception as e:
            print(f"   ❌ 图表生成失败: {e}")
            continue
        
        results.append({
            'name': config['name'],
            'bi_count': bi_count,
            'up_count': up_count,
            'down_count': down_count,
            'czsc_obj': c,
            'filename': config['filename']
        })
    
    # 生成详细对比报告
    print(f"\n{'='*80}")
    print("📊 详细对比报告")
    print(f"{'='*80}")
    
    print(f"\n1. 基础统计:")
    print(f"{'模式':<15} {'总笔数':<8} {'向上笔':<8} {'向下笔':<8} {'敏感性':<10}")
    print("-" * 60)
    
    standard_count = 0
    for result in results:
        if result['name'] == '标准模式':
            standard_count = result['bi_count']
            break
    
    for result in results:
        sensitivity = f"{result['bi_count']/standard_count:.1f}x" if standard_count > 0 else "N/A"
        print(f"{result['name']:<15} {result['bi_count']:<8} {result['up_count']:<8} {result['down_count']:<8} {sensitivity:<10}")
    
    # 详细分析
    print(f"\n2. 详细分析:")
    
    for result in results:
        c = result['czsc_obj']
        print(f"\n   {result['name']}:")
        print(f"   - 笔数量: {len(c.bi_list)}")
        print(f"   - 原始K线: {len(c.bars_raw)}")
        print(f"   - 无包含K线: {len(c.bars_ubi)}")
        
        if c.bi_list:
            # 计算平均笔长度
            avg_length = sum(bi.length for bi in c.bi_list) / len(c.bi_list)
            print(f"   - 平均笔长度: {avg_length:.1f} 根K线")
            
            # 计算平均变化幅度
            avg_change = sum(abs(bi.change) for bi in c.bi_list) / len(c.bi_list)
            print(f"   - 平均变化幅度: {avg_change:.2%}")
            
            # 显示最大和最小的笔
            max_bi = max(c.bi_list, key=lambda x: abs(x.change))
            min_bi = min(c.bi_list, key=lambda x: abs(x.change))
            print(f"   - 最大变化笔: {max_bi.change:+.2%}")
            print(f"   - 最小变化笔: {min_bi.change:+.2%}")
    
    # 使用建议
    print(f"\n3. 使用建议:")
    print(f"   - 标准模式: 适合长期投资，信号稳定，每个笔都有较强的技术意义")
    print(f"   - 灵活模式: 适合短线交易，能捕捉更多价格转折点，但需要过滤噪音")
    
    # 技术说明
    print(f"\n4. 技术说明:")
    print(f"   - 图表中的红色线条表示向上的笔")
    print(f"   - 图表中的蓝色线条表示向下的笔")
    print(f"   - 每个笔的起点和终点都是分型（价格转折点）")
    print(f"   - 可以在浏览器中交互式查看具体的价格和时间信息")
    
    print(f"\n{'='*60}")
    print("✅ 可视化测试完成")
    print(f"{'='*60}")
    print("📂 生成的文件:")
    for result in results:
        print(f"   - {result['filename']}")
    print(f"\n💡 提示:")
    print(f"   - 图表已自动在浏览器中打开")
    print(f"   - 可以鼠标悬停查看详细信息")
    print(f"   - 支持缩放和平移查看")

if __name__ == "__main__":
    test_visualization_with_browser()