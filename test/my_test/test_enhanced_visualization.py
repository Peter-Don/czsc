#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速测试增强后的可视化功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq
from czsc.utils.echarts_plot import kline_pro
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def create_simple_test_data():
    """创建简单的测试数据"""
    dates = pd.date_range('2023-01-01', periods=50, freq='1h')
    bars = []
    
    price = 100.0
    for i, dt in enumerate(dates):
        change = np.sin(i * 0.3) * 2 + np.random.normal(0, 0.5)
        price += change
        
        high = price + abs(change) * 0.5
        low = price - abs(change) * 0.5
        open_price = price - change * 0.3
        close_price = price
        
        bar = RawBar(
            symbol="TEST",
            id=i,
            dt=dt,
            freq=Freq.F60,
            open=round(open_price, 2),
            close=round(close_price, 2),
            high=round(high, 2),
            low=round(low, 2),
            vol=1000 + i * 10,
            amount=1000000 + i * 10000
        )
        bars.append(bar)
    
    return bars

def test_enhanced_visualization():
    """测试增强的可视化功能"""
    print("测试增强的分型级别可视化功能...")
    
    # 创建测试数据
    bars = create_simple_test_data()
    czsc = CZSC(bars=bars)
    
    print(f"分析结果: {len(czsc.fx_list)}个分型, {len(czsc.bi_list)}个笔")
    
    # 手动设置一些分型级别进行测试
    for i, fx in enumerate(czsc.fx_list):
        if i % 3 == 0:
            fx.gfc_level = 2
            fx.level_2_reasons = ['测试二级原因']
        elif i % 5 == 0:
            fx.gfc_level = 3
            fx.level_2_reasons = ['测试二级原因']
            fx.level_3_reasons = ['测试三级原因']
    
    # 准备可视化数据
    kline = [x.__dict__ for x in czsc.bars_raw]
    bi = []
    if len(czsc.bi_list) > 0:
        bi = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx} for x in czsc.bi_list] + \
             [{'dt': czsc.bi_list[-1].fx_b.dt, "bi": czsc.bi_list[-1].fx_b.fx}]
    
    # 创建增强的fx数据（包含级别信息）
    fx_enhanced = []
    for fx in czsc.fx_list:
        fx_enhanced.append({
            'dt': fx.dt,
            'fx': fx.fx,
            'level': fx.gfc_level,
            'mark': fx.mark.value,
            'level_desc': fx.level_description,
            'enhancement_summary': fx.enhancement_summary,
            'level_2_reasons': fx.level_2_reasons,
            'level_3_reasons': fx.level_3_reasons
        })
    
    print(f"准备了 {len(fx_enhanced)} 个分型数据，其中包含级别信息")
    
    # 使用增强的kline_pro函数
    chart = kline_pro(
        kline=kline,
        bi=bi,
        fx=fx_enhanced,  # 传入包含级别信息的fx数据
        title="增强分型级别可视化测试",
        width="1400px",
        height="600px"
    )
    
    # 生成HTML文件
    html_file = "enhanced_visualization_test.html"
    chart.render(html_file)
    
    print(f"✅ 增强可视化测试文件已生成: {html_file}")
    print("🎨 分型将按不同级别显示不同颜色和大小:")
    print("   - 一级分型: 灰色小点")
    print("   - 二级分型: 蓝色中点") 
    print("   - 三级分型: 红色大点")
    print("   - 四级分型: 金色特大点")
    
    return html_file

if __name__ == "__main__":
    try:
        result = test_enhanced_visualization()
        print(f"\n🎉 测试成功! 请打开 {result} 查看增强的分型级别可视化效果")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()