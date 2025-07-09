#!/usr/bin/env python
# coding: utf-8
"""
CZSC Enhanced 可视化使用指南
展示如何使用 CZSC 的可视化功能来查看笔的形状
"""

import os
import sys
import pandas as pd
from datetime import datetime
from typing import List

# 添加项目路径
sys.path.insert(0, '/home/moses2204/proj/czsc_enhanced')

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq

def load_sample_data() -> List[RawBar]:
    """加载示例数据"""
    cur_path = os.path.dirname(os.path.abspath(__file__))
    file_kline = os.path.join(cur_path, "test/data/000001.SH_D.csv")
    
    kline = pd.read_csv(file_kline, encoding="utf-8")
    kline['amount'] = kline['close'] * kline['vol']
    kline.loc[:, "dt"] = pd.to_datetime(kline.dt)
    
    bars = [RawBar(symbol=row['symbol'], id=i, freq=Freq.D, open=row['open'], dt=row['dt'],
                   close=row['close'], high=row['high'], low=row['low'], vol=row['vol'], amount=row['amount'])
            for i, row in kline.iterrows()]
    
    return bars[:100]  # 使用前100根K线

def demo_basic_usage():
    """演示基础使用方法"""
    print("=" * 60)
    print("CZSC Enhanced 可视化使用指南")
    print("=" * 60)
    
    # 加载数据
    bars = load_sample_data()
    print(f"✅ 加载示例数据: {len(bars)} 根K线")
    
    # 方法1: 标准模式 + 快速查看
    print("\n📊 方法1: 标准模式 + 快速查看")
    print("代码示例:")
    print("```python")
    print("c = CZSC(bars, market_type='stock')")
    print("c.open_in_browser()  # 直接在浏览器打开")
    print("```")
    
    try:
        c = CZSC(bars, market_type='stock')
        print(f"✅ 标准模式分析完成，识别出 {len(c.bi_list)} 笔")
        
        # 生成HTML文件（不自动打开浏览器）
        chart = c.to_echarts(width="1400px", height="600px")
        chart.render("demo_standard_mode.html")
        print("✅ 图表已保存：demo_standard_mode.html")
        
    except Exception as e:
        print(f"❌ 标准模式演示失败: {e}")
    
    # 方法2: 灵活模式 + 详细分析
    print("\n📊 方法2: 灵活模式 + 详细分析")
    print("代码示例:")
    print("```python")
    print("c = CZSC(bars, pen_model='flexible', market_type='stock')")
    print("chart = c.to_echarts(width='1400px', height='600px')")
    print("chart.render('analysis.html')")
    print("```")
    
    try:
        c = CZSC(bars, pen_model='flexible', market_type='stock')
        print(f"✅ 灵活模式分析完成，识别出 {len(c.bi_list)} 笔")
        
        # 生成HTML文件
        chart = c.to_echarts(width="1400px", height="600px")
        chart.render("demo_flexible_mode.html")
        print("✅ 图表已保存：demo_flexible_mode.html")
        
    except Exception as e:
        print(f"❌ 灵活模式演示失败: {e}")
    
    # 方法3: 自定义参数
    print("\n📊 方法3: 自定义参数")
    print("代码示例:")
    print("```python")
    print("c = CZSC(bars, pen_model='flexible', market_type='crypto')")
    print("chart = c.to_echarts(width='1600px', height='800px')")
    print("chart.render('crypto_analysis.html')")
    print("```")
    
    try:
        c = CZSC(bars, pen_model='flexible', market_type='crypto', threshold_mode='conservative')
        print(f"✅ 加密货币模式分析完成，识别出 {len(c.bi_list)} 笔")
        
        # 生成更大的图表
        chart = c.to_echarts(width="1600px", height="800px")
        chart.render("demo_crypto_mode.html")
        print("✅ 图表已保存：demo_crypto_mode.html")
        
    except Exception as e:
        print(f"❌ 加密货币模式演示失败: {e}")

def demo_advanced_usage():
    """演示高级使用方法"""
    print(f"\n{'=' * 60}")
    print("高级使用方法")
    print("=" * 60)
    
    bars = load_sample_data()
    
    # 高级功能1: 添加交易信号
    print("\n🎯 高级功能1: 添加交易信号")
    print("代码示例:")
    print("```python")
    print("def get_signals(c):")
    print("    # 自定义信号逻辑")
    print("    return {'signal': 'buy' if len(c.bi_list) > 10 else 'hold'}")
    print("")
    print("c = CZSC(bars, get_signals=get_signals)")
    print("chart = c.to_echarts()")
    print("```")
    
    try:
        def simple_signal(c):
            """简单的信号函数"""
            return {
                'bi_count': len(c.bi_list),
                'signal': 'active' if len(c.bi_list) > 10 else 'wait'
            }
        
        c = CZSC(bars, pen_model='flexible', get_signals=simple_signal)
        print(f"✅ 带信号的分析完成，识别出 {len(c.bi_list)} 笔")
        print(f"📊 信号状态: {c.signals}")
        
        chart = c.to_echarts(width="1400px", height="600px")
        chart.render("demo_with_signals.html")
        print("✅ 图表已保存：demo_with_signals.html")
        
    except Exception as e:
        print(f"❌ 信号演示失败: {e}")
    
    # 高级功能2: 批量分析
    print("\n🔄 高级功能2: 批量分析不同参数")
    print("代码示例:")
    print("```python")
    print("configs = [")
    print("    {'pen_model': 'standard', 'market_type': 'stock'},")
    print("    {'pen_model': 'flexible', 'market_type': 'stock'},")
    print("    {'pen_model': 'flexible', 'market_type': 'crypto'}")
    print("]")
    print("for i, config in enumerate(configs):")
    print("    c = CZSC(bars, **config)")
    print("    chart = c.to_echarts()")
    print("    chart.render(f'analysis_{i}.html')")
    print("```")
    
    configs = [
        {'name': 'standard_stock', 'params': {'market_type': 'stock'}},
        {'name': 'flexible_stock', 'params': {'pen_model': 'flexible', 'market_type': 'stock'}},
        {'name': 'flexible_crypto', 'params': {'pen_model': 'flexible', 'market_type': 'crypto'}}
    ]
    
    for config in configs:
        try:
            c = CZSC(bars, **config['params'])
            chart = c.to_echarts(width="1200px", height="500px")
            chart.render(f"demo_batch_{config['name']}.html")
            print(f"✅ {config['name']}: {len(c.bi_list)} 笔")
        except Exception as e:
            print(f"❌ {config['name']} 失败: {e}")

def show_usage_tips():
    """显示使用技巧"""
    print(f"\n{'=' * 60}")
    print("💡 使用技巧和注意事项")
    print("=" * 60)
    
    print("\n1. 可视化方法选择:")
    print("   - to_echarts(): 生成HTML文件，适合离线分析")
    print("   - to_plotly(): 生成Plotly图表，适合Jupyter环境")
    print("   - open_in_browser(): 直接打开浏览器，适合快速查看")
    
    print("\n2. 参数调优建议:")
    print("   - 标准模式: 适合长期投资，信号稳定")
    print("   - 灵活模式: 适合短线交易，信号敏感")
    print("   - 市场类型: stock/crypto/futures 有不同的默认参数")
    
    print("\n3. 图表交互技巧:")
    print("   - 鼠标悬停: 查看详细价格和时间信息")
    print("   - 滚轮缩放: 放大缩小查看局部细节")
    print("   - 拖拽平移: 查看不同时间段的数据")
    print("   - 图例点击: 显示/隐藏不同类型的线条")
    
    print("\n4. 性能优化:")
    print("   - 数据量大时建议限制K线数量（如取最近500根）")
    print("   - 图表尺寸适中，避免过大影响渲染速度")
    print("   - 定期清理生成的HTML文件")
    
    print("\n5. 常见问题:")
    print("   - 如果没有识别到笔，检查数据质量和数量")
    print("   - 如果笔太多，考虑使用标准模式或调整参数")
    print("   - 如果图表无法显示，检查HTML文件是否正确生成")

def main():
    """主函数"""
    print("CZSC Enhanced 可视化完整使用指南")
    print("参照 test_analyze.py 的测试方法")
    print("使用 CZSC 的可视化功能替代传统的 show() 方法")
    
    try:
        demo_basic_usage()
        demo_advanced_usage()
        show_usage_tips()
        
        print(f"\n{'=' * 60}")
        print("✅ 演示完成！")
        print("=" * 60)
        print("📂 生成的演示文件:")
        demo_files = [
            "demo_standard_mode.html",
            "demo_flexible_mode.html", 
            "demo_crypto_mode.html",
            "demo_with_signals.html",
            "demo_batch_standard_stock.html",
            "demo_batch_flexible_stock.html",
            "demo_batch_flexible_crypto.html"
        ]
        
        for file in demo_files:
            if os.path.exists(file):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} (生成失败)")
        
        print(f"\n🌐 在浏览器中打开这些HTML文件即可查看笔的可视化效果!")
        print(f"📱 支持交互式查看，可以缩放、平移、查看详细信息")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()