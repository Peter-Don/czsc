#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分型级别可视化测试脚本

功能：
1. 生成测试数据，创建不同级别的分型
2. 在图表中用不同颜色和大小区分不同级别的分型
3. 添加级别信息标注
4. 生成HTML可视化文件供用户查看

级别区分方案：
- 一级分型：小圆点，灰色
- 二级分型：中圆点，蓝色  
- 三级分型：大圆点，红色
- 四级分型：特大圆点，金色
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq, Mark
from czsc.utils.echarts_plot import kline_pro
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json


def create_complex_test_data():
    """创建复杂的测试数据，包含不同级别的分型"""
    
    # 创建时间序列
    start_time = datetime(2023, 1, 1, 9, 0)
    dates = [start_time + timedelta(hours=i) for i in range(200)]
    
    bars = []
    base_price = 100.0
    
    # 模拟复杂的价格走势，包含多级别的趋势
    for i, dt in enumerate(dates):
        # 主趋势：长期上涨
        main_trend = i * 0.1
        
        # 中级趋势：每20根K线一个周期
        mid_trend = 10 * np.sin(i * 2 * np.pi / 20)
        
        # 短期波动：每5根K线一个小波动
        short_wave = 3 * np.sin(i * 2 * np.pi / 5)
        
        # 随机噪音
        noise = np.random.normal(0, 1)
        
        # 合成价格
        price = base_price + main_trend + mid_trend + short_wave + noise
        
        # 生成OHLC
        volatility = 0.5 + abs(np.sin(i * 0.1)) * 2  # 动态波动率
        open_price = price
        close_price = price + np.random.normal(0, 0.3)
        high_price = max(open_price, close_price) + volatility * abs(np.random.normal(0, 0.5))
        low_price = min(open_price, close_price) - volatility * abs(np.random.normal(0, 0.5))
        
        # 成交量模拟
        volume = 1000 + i * 5 + abs(np.random.normal(0, 200))
        amount = volume * price
        
        bar = RawBar(
            symbol="TEST",
            id=i,
            dt=dt,
            freq=Freq.F60,
            open=round(open_price, 2),
            close=round(close_price, 2),
            high=round(high_price, 2),
            low=round(low_price, 2),
            vol=round(volume),
            amount=round(amount)
        )
        bars.append(bar)
    
    return bars


def enhance_fx_levels_for_demo(czsc):
    """为演示目的手动设置一些分型的级别"""
    if not czsc.fx_list:
        return
    
    # 设置不同级别的分型用于演示
    fx_count = len(czsc.fx_list)
    
    for i, fx in enumerate(czsc.fx_list):
        # 重置级别
        fx.gfc_level = 1
        fx.level_2_reasons = []
        fx.level_3_reasons = []
        
        # 根据位置和一些特征设置级别
        if i % 8 == 0:  # 每8个分型设置一个三级分型
            fx.gfc_level = 3
            fx.level_2_reasons = ['大幅破坏后续分型', '成交量放大确认']
            fx.level_3_reasons = ['多周期共振', '关键时间窗口']
        elif i % 4 == 0:  # 每4个分型设置一个二级分型
            fx.gfc_level = 2
            fx.level_2_reasons = ['后续分型被破坏', 'VSA确认']
        elif fx.power_str == '强':  # 力度强的设为二级
            fx.gfc_level = 2
            fx.level_2_reasons = ['力度强势突破']
        
        # 特殊情况：最高点和最低点设为三级
        if i < fx_count:
            all_highs = [f.fx for f in czsc.fx_list if f.mark == Mark.G]
            all_lows = [f.fx for f in czsc.fx_list if f.mark == Mark.D]
            
            if all_highs and fx.mark == Mark.G and fx.fx == max(all_highs):
                fx.gfc_level = 3
                fx.level_2_reasons = ['全局最高点', '成交量背离']
                fx.level_3_reasons = ['关键阻力位', '多周期顶部']
            
            if all_lows and fx.mark == Mark.D and fx.fx == min(all_lows):
                fx.gfc_level = 3
                fx.level_2_reasons = ['全局最低点', '成交量背离'] 
                fx.level_3_reasons = ['关键支撑位', '多周期底部']


def create_enhanced_chart_data(czsc):
    """创建增强的图表数据，包含不同级别的分型"""
    
    # 基础K线数据
    kline = [x.__dict__ for x in czsc.bars_raw]
    
    # 笔数据
    bi = []
    if len(czsc.bi_list) > 0:
        bi = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx} for x in czsc.bi_list] + \
             [{'dt': czsc.bi_list[-1].fx_b.dt, "bi": czsc.bi_list[-1].fx_b.fx}]
    
    # 分级分型数据
    fx_data = {
        'level_1': [],  # 一级分型
        'level_2': [],  # 二级分型  
        'level_3': [],  # 三级分型
        'level_4': []   # 四级分型
    }
    
    for fx in czsc.fx_list:
        fx_point = {
            'dt': fx.dt,
            'fx': fx.fx,
            'mark': fx.mark.value,
            'level': fx.gfc_level,
            'level_desc': fx.level_description,
            'reasons_2': fx.level_2_reasons,
            'reasons_3': fx.level_3_reasons,
            'power': fx.power_str,
            'enhancement_summary': fx.enhancement_summary
        }
        
        if fx.gfc_level == 1:
            fx_data['level_1'].append(fx_point)
        elif fx.gfc_level == 2:
            fx_data['level_2'].append(fx_point)
        elif fx.gfc_level == 3:
            fx_data['level_3'].append(fx_point)
        elif fx.gfc_level >= 4:
            fx_data['level_4'].append(fx_point)
    
    return kline, bi, fx_data


def create_enhanced_kline_chart(kline, bi, fx_data, title="分型级别可视化"):
    """创建增强的K线图表，显示不同级别的分型"""
    
    from pyecharts import options as opts
    from pyecharts.charts import Kline, Line, Scatter
    from pyecharts.commons.utils import JsCode
    
    # 创建K线图
    kline_chart = (
        Kline()
        .add_xaxis([x['dt'].strftime('%Y-%m-%d %H:%M') for x in kline])
        .add_yaxis(
            "K线",
            [[x['open'], x['close'], x['low'], x['high']] for x in kline],
            itemstyle_opts=opts.ItemStyleOpts(
                color="#ef232a",
                color0="#14b143",
                border_color="#ef232a", 
                border_color0="#14b143",
            )
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, subtitle="不同颜色和大小表示不同级别的分型"),
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(
                scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False, type_="inside", xaxis_index=[0], range_=[70, 100]
                ),
                opts.DataZoomOpts(
                    is_show=True, xaxis_index=[0], type_="slider", range_=[70, 100]
                ),
            ],
        )
    )
    
    # 添加笔线
    if bi:
        line_chart = (
            Line()
            .add_xaxis([x['dt'].strftime('%Y-%m-%d %H:%M') for x in bi])
            .add_yaxis(
                "笔",
                [x['bi'] for x in bi],
                is_smooth=False,
                linestyle_opts=opts.LineStyleOpts(width=2, color="#1f77b4"),
                label_opts=opts.LabelOpts(is_show=False),
            )
        )
        kline_chart = kline_chart.overlap(line_chart)
    
    # 添加不同级别的分型
    level_configs = {
        'level_1': {'color': '#8c8c8c', 'size': 8, 'name': '一级分型'},
        'level_2': {'color': '#1890ff', 'size': 12, 'name': '二级分型'},
        'level_3': {'color': '#f5222d', 'size': 16, 'name': '三级分型'},
        'level_4': {'color': '#faad14', 'size': 20, 'name': '四级分型'}
    }
    
    for level, config in level_configs.items():
        if fx_data[level]:
            scatter_chart = (
                Scatter()
                .add_xaxis([x['dt'].strftime('%Y-%m-%d %H:%M') for x in fx_data[level]])
                .add_yaxis(
                    config['name'],
                    [
                        opts.ScatterItem(
                            name=f"{x['mark']} - {x['level_desc']}",
                            value=[x['dt'].strftime('%Y-%m-%d %H:%M'), x['fx']],
                            symbol_size=config['size'],
                            itemstyle_opts=opts.ItemStyleOpts(color=config['color'])
                        ) for x in fx_data[level]
                    ],
                    label_opts=opts.LabelOpts(is_show=False),
                )
                .set_series_opts(
                    tooltip_opts=opts.TooltipOpts(
                        formatter=JsCode("""
                        function(params) {
                            var data = params.data;
                            var info = data.name + '<br/>';
                            info += '时间: ' + data.value[0] + '<br/>';
                            info += '价格: ' + data.value[1] + '<br/>';
                            return info;
                        }
                        """)
                    )
                )
            )
            kline_chart = kline_chart.overlap(scatter_chart)
    
    return kline_chart


def generate_level_statistics_html(czsc):
    """生成级别统计信息的HTML"""
    
    stats = czsc.get_level_statistics()
    
    html = f"""
    <div style="margin: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h3>🔍 分型级别统计分析</h3>
        
        <div style="display: flex; gap: 20px; margin: 15px 0;">
            <div style="background: #f6f6f6; padding: 15px; border-radius: 5px; flex: 1;">
                <h4>📊 分型统计</h4>
                <p><span style="color: #8c8c8c;">●</span> 一级分型: {stats['fx_statistics']['level_1']}个</p>
                <p><span style="color: #1890ff;">●</span> 二级分型: {stats['fx_statistics']['level_2']}个</p>
                <p><span style="color: #f5222d;">●</span> 三级分型: {stats['fx_statistics']['level_3']}个</p>
                <p><span style="color: #faad14;">●</span> 四级分型: {stats['fx_statistics']['level_4']}个</p>
                <p><strong>总计: {stats['total_fxs']}个分型</strong></p>
            </div>
            
            <div style="background: #f6f6f6; padding: 15px; border-radius: 5px; flex: 1;">
                <h4>📈 笔统计</h4>
                <p>一级笔: {stats['bi_statistics']['level_1']}个</p>
                <p>二级笔: {stats['bi_statistics']['level_2']}个</p>
                <p>三级笔: {stats['bi_statistics']['level_3']}个</p>
                <p>四级笔: {stats['bi_statistics']['level_4']}个</p>
                <p><strong>总计: {stats['total_bis']}个笔</strong></p>
            </div>
        </div>
        
        <div style="background: #e6f7ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h4>💡 图例说明</h4>
            <p><span style="color: #8c8c8c;">● 灰色小点</span>：一级分型（标准分型）</p>
            <p><span style="color: #1890ff;">● 蓝色中点</span>：二级分型（确认分型）</p>
            <p><span style="color: #f5222d;">● 红色大点</span>：三级分型（强确认分型）</p>
            <p><span style="color: #faad14;">● 金色特大点</span>：四级分型（超强分型）</p>
        </div>
    </div>
    """
    
    return html


def create_level_detail_table(czsc):
    """创建级别详情表格"""
    
    html = """
    <div style="margin: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h3>📋 分型详细信息表</h3>
        <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
            <thead>
                <tr style="background: #f0f0f0;">
                    <th style="border: 1px solid #ddd; padding: 8px;">序号</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">时间</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">类型</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">价格</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">级别</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">二级原因</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">三级原因</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # 只显示二级以上的分型
    high_level_fxs = [fx for fx in czsc.fx_list if fx.gfc_level >= 2]
    
    level_colors = {1: '#8c8c8c', 2: '#1890ff', 3: '#f5222d', 4: '#faad14'}
    
    for i, fx in enumerate(high_level_fxs[:20]):  # 只显示前20个
        color = level_colors.get(fx.gfc_level, '#000000')
        
        html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{i+1}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{fx.dt.strftime('%m-%d %H:%M')}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{fx.mark.value}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{fx.fx:.2f}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: {color}; font-weight: bold;">{fx.level_description}</td>
                <td style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">{', '.join(fx.level_2_reasons[:2])}</td>
                <td style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">{', '.join(fx.level_3_reasons[:2])}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html


def main():
    """主函数：生成完整的分型级别可视化测试"""
    
    print("=" * 60)
    print("🔍 分型级别可视化测试")
    print("=" * 60)
    
    # 1. 创建测试数据
    print("📊 创建复杂测试数据...")
    bars = create_complex_test_data()
    print(f"生成了 {len(bars)} 根K线数据")
    
    # 2. 进行CZSC分析
    print("🔬 进行CZSC分析...")
    czsc = CZSC(bars=bars)
    print(f"识别出 {len(czsc.fx_list)} 个分型，{len(czsc.bi_list)} 个笔")
    
    # 3. 设置分型级别（演示用）
    print("⚡ 设置分型级别...")
    enhance_fx_levels_for_demo(czsc)
    
    # 4. 统计级别信息
    stats = czsc.get_level_statistics()
    print("📈 级别统计:")
    print(f"  一级分型: {stats['fx_statistics']['level_1']}个")
    print(f"  二级分型: {stats['fx_statistics']['level_2']}个") 
    print(f"  三级分型: {stats['fx_statistics']['level_3']}个")
    print(f"  四级分型: {stats['fx_statistics']['level_4']}个")
    
    # 5. 创建可视化数据
    print("🎨 创建可视化数据...")
    kline, bi, fx_data = create_enhanced_chart_data(czsc)
    
    # 6. 使用原有的kline_pro函数，但添加级别信息
    print("📊 生成增强K线图...")
    
    # 转换fx_data为原有格式，但添加级别信息
    fx_for_chart = []
    for level, fxs in fx_data.items():
        for fx in fxs:
            fx_for_chart.append({
                'dt': fx['dt'],
                'fx': fx['fx'],
                'level': fx['level'],
                'mark': fx['mark'],
                'level_desc': fx['level_desc'],
                'enhancement_summary': fx['enhancement_summary']
            })
    
    # 使用增强的kline_pro函数
    chart = kline_pro(
        kline=kline,
        bi=bi,
        fx=fx_for_chart,
        title="分型级别可视化测试",
        width="1600px",
        height="800px"
    )
    
    # 7. 生成HTML文件
    html_file = "分型级别可视化测试.html"
    
    # 获取chart的HTML内容
    chart_html = chart.render_embed()
    
    # 创建完整的HTML文件
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>分型级别可视化测试</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            .header {{ text-align: center; margin: 20px 0; }}
            .container {{ max-width: 1800px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 CZSC 分型级别可视化测试</h1>
                <p>不同颜色和大小的点表示不同级别的分型</p>
            </div>
            
            {generate_level_statistics_html(czsc)}
            
            <div style="margin: 20px 0;">
                {chart_html}
            </div>
            
            {create_level_detail_table(czsc)}
            
            <div style="margin: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
                <h3>📝 测试说明</h3>
                <ul>
                    <li>本测试使用模拟数据，包含复杂的多级别价格走势</li>
                    <li>分型级别基于破坏程度、成交量确认、关键位置等因素判定</li>
                    <li>可以通过拖拽缩放查看不同时间段的分型分布</li>
                    <li>鼠标悬停在分型点上可以查看详细信息</li>
                    <li>蓝色线条表示笔的连接</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 写入文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✅ 可视化文件已生成: {html_file}")
    print("🌐 请在浏览器中打开该文件查看效果")
    
    # 8. 打印一些高级分型的详细信息
    print("\n" + "=" * 60)
    print("🔍 高级分型详细信息 (前10个)")
    print("=" * 60)
    
    high_level_fxs = [fx for fx in czsc.fx_list if fx.gfc_level >= 2][:10]
    for i, fx in enumerate(high_level_fxs):
        print(f"\n{i+1}. {fx.enhancement_summary}")
        print(f"   时间: {fx.dt.strftime('%Y-%m-%d %H:%M')}")
        print(f"   价格: {fx.fx:.2f}")
        if fx.level_2_reasons:
            print(f"   二级原因: {', '.join(fx.level_2_reasons)}")
        if fx.level_3_reasons:
            print(f"   三级原因: {', '.join(fx.level_3_reasons)}")
    
    return html_file


if __name__ == "__main__":
    try:
        html_file = main()
        print(f"\n🎉 测试完成！请打开 {html_file} 查看分型级别可视化效果")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()