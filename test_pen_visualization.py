#!/usr/bin/env python
# coding: utf-8
"""
使用可视化方法展示不同笔模式的效果
调用 CZSC 的可视化方法来查看笔的形状
"""

import os
import sys
import pandas as pd
import time
from datetime import datetime
from typing import List

# 添加项目路径
sys.path.insert(0, '/home/moses2204/proj/czsc_enhanced')

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq

def read_test_data(limit: int = 100) -> List[RawBar]:
    """读取测试数据，参照 test_analyze.py 的方法"""
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
    
    return bars[:limit]

def test_visualization_methods():
    """测试不同笔模式的可视化效果"""
    print("="*80)
    print("CZSC Enhanced 笔模式可视化测试")
    print("="*80)
    
    # 读取测试数据
    bars = read_test_data(limit=150)
    print(f"✅ 读取测试数据: {len(bars)} 根K线")
    print(f"时间范围: {bars[0].dt.date()} 到 {bars[-1].dt.date()}")
    
    # 测试不同笔模式
    test_configs = [
        {
            'name': '标准模式',
            'filename': 'standard_mode_analysis.html',
            'params': {
                'market_type': 'stock',
                'threshold_mode': 'moderate'
            }
        },
        {
            'name': '灵活模式',
            'filename': 'flexible_mode_analysis.html', 
            'params': {
                'pen_model': 'flexible',
                'market_type': 'stock',
                'threshold_mode': 'moderate'
            }
        },
        {
            'name': '自适应模式',
            'filename': 'adaptive_mode_analysis.html',
            'params': {
                'pen_model': 'flexible',
                'use_adaptive_pen': True,
                'adaptive_vol_ratio': 1.5,  # 降低阈值以便观察效果
                'adaptive_atr_ratio': 1.2,
                'market_type': 'stock',
                'threshold_mode': 'moderate'
            }
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"🔍 分析 {config['name']}")
        print(f"⚙️  参数: {config['params']}")
        
        try:
            # 创建CZSC分析器
            c = CZSC(bars, **config['params'])
            
            # 基础统计
            bi_count = len(c.bi_list)
            up_count = sum(1 for bi in c.bi_list if hasattr(bi, 'direction') and str(bi.direction) == 'Direction.Up')
            down_count = bi_count - up_count
            
            print(f"✅ 分析完成:")
            print(f"   - 总笔数: {bi_count}")
            print(f"   - 向上笔: {up_count}")
            print(f"   - 向下笔: {down_count}")
            
            # 显示前几笔的详细信息
            if c.bi_list:
                print(f"   - 前3笔详情:")
                for i, bi in enumerate(c.bi_list[:3]):
                    direction = "↑" if str(bi.direction) == 'Direction.Up' else "↓"
                    print(f"     笔{i+1}: {direction} {bi.sdt.strftime('%Y-%m-%d')} → {bi.edt.strftime('%Y-%m-%d')} "
                          f"({bi.change:+.2%})")
            
            # 生成可视化图表
            print(f"📊 生成可视化图表...")
            
            # 方法1: 使用 to_echarts() 生成HTML文件
            try:
                chart = c.to_echarts(width="1400px", height="600px")
                chart.render(config['filename'])
                print(f"   ✅ ECharts图表已保存: {config['filename']}")
            except Exception as e:
                print(f"   ❌ ECharts图表生成失败: {e}")
            
            # 方法2: 使用 open_in_browser() 直接打开（注释掉避免打开太多浏览器窗口）
            # c.open_in_browser()
            
            results.append({
                'name': config['name'],
                'bi_count': bi_count,
                'up_count': up_count,
                'down_count': down_count,
                'czsc_obj': c,
                'filename': config['filename']
            })
            
        except Exception as e:
            print(f"❌ {config['name']} 分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 生成对比报告
    print(f"\n{'='*80}")
    print("📊 笔模式对比报告")
    print(f"{'='*80}")
    
    print(f"{'模式':<15} {'总笔数':<8} {'向上笔':<8} {'向下笔':<8} {'可视化文件':<25}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['name']:<15} {result['bi_count']:<8} {result['up_count']:<8} {result['down_count']:<8} {result['filename']:<25}")
    
    # 生成一个综合对比页面
    print(f"\n📈 生成综合对比页面...")
    create_comparison_page(results)
    
    print(f"\n{'='*60}")
    print("✅ 可视化测试完成")
    print(f"{'='*60}")
    print("📂 生成的文件:")
    for result in results:
        print(f"   - {result['filename']}")
    print(f"   - comparison_summary.html")
    print(f"\n💡 使用方法:")
    print(f"   1. 直接打开HTML文件查看单个模式的详细分析")
    print(f"   2. 打开comparison_summary.html查看综合对比")
    print(f"   3. 在浏览器中可以交互式查看K线和笔的详细信息")

def create_comparison_page(results):
    """创建一个综合对比页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CZSC 笔模式对比分析</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; text-align: center; }
            h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
            .summary { background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }
            .chart-links { display: flex; justify-content: space-around; margin: 20px 0; }
            .chart-link { 
                display: inline-block; 
                padding: 10px 20px; 
                background: #007bff; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px;
                margin: 5px;
            }
            .chart-link:hover { background: #0056b3; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #f2f2f2; }
            .highlight { background-color: #fff3cd; }
        </style>
    </head>
    <body>
        <h1>CZSC Enhanced 笔模式对比分析</h1>
        
        <div class="summary">
            <h2>📊 测试总结</h2>
            <p>本次测试使用000001.SH日线数据，对比了三种不同的笔模式识别效果：</p>
            <ul>
                <li><strong>标准模式</strong>: 严格5根K线笔判断，保持原始CZSC逻辑</li>
                <li><strong>灵活模式</strong>: 允许3根K线成笔，适用于快速市场</li>
                <li><strong>自适应模式</strong>: 基于成交量和ATR的极端情况判断</li>
            </ul>
        </div>
        
        <h2>🔗 详细分析图表</h2>
        <div class="chart-links">
    """
    
    for result in results:
        html_content += f'''
            <a href="{result['filename']}" class="chart-link" target="_blank">
                {result['name']}<br>
                <small>{result['bi_count']}笔</small>
            </a>
        '''
    
    html_content += """
        </div>
        
        <h2>📈 数据对比</h2>
        <table>
            <tr>
                <th>模式</th>
                <th>总笔数</th>
                <th>向上笔</th>
                <th>向下笔</th>
                <th>特点</th>
            </tr>
    """
    
    for result in results:
        characteristics = {
            '标准模式': '信号稳定，适合长期分析',
            '灵活模式': '敏感度高，适合短期交易',
            '自适应模式': '处理极端情况，适合波动市场'
        }
        
        html_content += f'''
            <tr>
                <td><strong>{result['name']}</strong></td>
                <td class="highlight">{result['bi_count']}</td>
                <td>{result['up_count']}</td>
                <td>{result['down_count']}</td>
                <td>{characteristics.get(result['name'], '未知')}</td>
            </tr>
        '''
    
    html_content += """
        </table>
        
        <h2>💡 使用建议</h2>
        <div class="summary">
            <h3>选择指南:</h3>
            <ul>
                <li><strong>长期投资者</strong>: 选择标准模式，信号稳定，噪音较少</li>
                <li><strong>短线交易者</strong>: 选择灵活模式，能捕捉更多短期机会</li>
                <li><strong>量化策略</strong>: 选择自适应模式，在极端情况下提供额外保护</li>
            </ul>
        </div>
        
        <div class="summary">
            <h3>技术实现:</h3>
            <pre><code>
# 标准模式
c = CZSC(bars, market_type='stock')

# 灵活模式
c = CZSC(bars, pen_model='flexible', market_type='stock')

# 自适应模式
c = CZSC(bars, pen_model='flexible', use_adaptive_pen=True, 
         adaptive_vol_ratio=1.5, adaptive_atr_ratio=1.2)
            </code></pre>
        </div>
        
        <footer style="text-align: center; margin-top: 40px; color: #666;">
            <p>Generated by CZSC Enhanced - 缠中说禅增强版</p>
        </footer>
    </body>
    </html>
    """
    
    with open('comparison_summary.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    test_visualization_methods()