#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CZSC Enhanced FVG和OB可视化修复版本
直接使用本地项目的完整kline_pro功能
"""

import sys
import os
import importlib.util

# 确保使用本地项目
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from czsc.analyze import CZSC
from czsc.objects import RawBar, Operate
from czsc.enum import Freq, Direction, Mark
from czsc.utils.ta import SMA


# 直接从本地项目导入完整的echarts_plot模块
def load_local_echarts_module():
    """加载本地项目的echarts_plot模块"""
    echarts_path = os.path.join(project_root, "czsc", "utils", "echarts_plot.py")
    
    # 预先导入依赖
    ta_path = os.path.join(project_root, "czsc", "utils", "ta.py") 
    ta_spec = importlib.util.spec_from_file_location("ta", ta_path)
    ta_module = importlib.util.module_from_spec(ta_spec)
    ta_spec.loader.exec_module(ta_module)
    
    # 将ta模块添加到sys.modules中，以便相对导入能找到它
    sys.modules['czsc.utils.ta'] = ta_module
    
    # 导入其他必要的依赖
    from pyecharts import options as opts
    from pyecharts.charts import HeatMap, Kline, Line, Bar, Scatter, Grid, Boxplot
    from pyecharts.commons.utils import JsCode
    from typing import List, Optional
    
    # 准备echarts_plot模块的执行环境
    echarts_spec = importlib.util.spec_from_file_location("echarts_plot", echarts_path)
    echarts_module = importlib.util.module_from_spec(echarts_spec)
    
    # 手动添加必要的全局变量到模块中
    echarts_module.opts = opts
    echarts_module.HeatMap = HeatMap
    echarts_module.Kline = Kline
    echarts_module.Line = Line
    echarts_module.Bar = Bar
    echarts_module.Scatter = Scatter
    echarts_module.Grid = Grid
    echarts_module.Boxplot = Boxplot
    echarts_module.JsCode = JsCode
    echarts_module.List = List
    echarts_module.Optional = Optional
    echarts_module.np = np
    echarts_module.Operate = Operate
    echarts_module.SMA = ta_module.SMA
    echarts_module.MACD = ta_module.MACD
    
    try:
        from lightweight_charts import Chart
        from lightweight_charts.widgets import StreamlitChart
        echarts_module.Chart = Chart
        echarts_module.StreamlitChart = StreamlitChart
    except ImportError:
        pass  # lightweight_charts是可选的
    
    # 执行模块
    echarts_spec.loader.exec_module(echarts_module)
    
    return echarts_module


def load_real_btc_data(file_path, max_rows=500):
    """加载真实的BTCUSDT数据"""
    print(f"📊 加载真实BTCUSDT数据: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        print(f"   原始数据行数: {len(df)}")
        
        if len(df) > max_rows:
            start_idx = len(df) // 3
            df = df.iloc[start_idx:start_idx + max_rows].copy()
        
        print(f"   使用数据范围: {len(df)}行")
        
        bars = []
        for i, row in df.iterrows():
            dt = pd.to_datetime(row['open_time'])
            
            bar = RawBar(
                symbol="BTCUSDT",
                id=i,
                dt=dt,
                freq=Freq.F1,
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                vol=float(row['volume']),
                amount=float(row['quote_volume'])
            )
            bars.append(bar)
        
        print(f"✅ 数据加载完成")
        print(f"   时间范围: {bars[0].dt} 到 {bars[-1].dt}")
        print(f"   价格范围: {min(bar.low for bar in bars):.2f} - {max(bar.high for bar in bars):.2f}")
        
        return bars
        
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return []


def analyze_czsc(bars):
    """CZSC分析"""
    print(f"\\n🔍 CZSC分析")
    czsc = CZSC(bars)
    
    print(f"📈 原始K线数量: {len(bars)}")
    print(f"📊 处理后K线数量: {len(czsc.bars_ubi)}")
    print(f"📍 识别分型数量: {len(czsc.fx_list)}")
    print(f"📏 构建笔数量: {len(czsc.bi_list)}")
    
    return czsc


def create_fvg_data(czsc):
    """创建FVG数据"""
    print(f"\\n🔳 生成FVG数据")
    
    fvg_data = []
    bars = czsc.bars_raw
    
    if len(bars) < 3:
        return fvg_data
    
    recent_bars = bars[-100:] if len(bars) > 100 else bars
    
    for i in range(2, len(recent_bars)):
        bar1, bar2, bar3 = recent_bars[i-2], recent_bars[i-1], recent_bars[i]
        
        # 检测向上FVG
        if bar1.high < bar3.low:
            gap_size = bar3.low - bar1.high
            if gap_size > bar1.high * 0.0001:
                fvg_data.append({
                    'start_dt': bar1.dt,
                    'end_dt': bar3.dt,
                    'dt': bar2.dt,
                    'high': bar3.low,
                    'low': bar1.high,
                    'direction': 'Up',
                    'size': gap_size
                })
        
        # 检测向下FVG
        elif bar1.low > bar3.high:
            gap_size = bar1.low - bar3.high
            if gap_size > bar3.high * 0.0001:
                fvg_data.append({
                    'start_dt': bar1.dt,
                    'end_dt': bar3.dt,
                    'dt': bar2.dt,
                    'high': bar1.low,
                    'low': bar3.high,
                    'direction': 'Down',
                    'size': gap_size
                })
    
    print(f"   检测到 {len(fvg_data)} 个FVG")
    return fvg_data


def create_ob_data(czsc):
    """创建Order Block数据"""
    print(f"\\n📦 生成Order Block数据")
    
    ob_data = []
    
    # 基于分型创建Order Block
    for fx in czsc.fx_list[-20:]:  # 只取最近20个分型
        if fx.mark == Mark.G:  # 高点分型 -> 供应区域
            ob_data.append({
                'start_dt': fx.dt,
                'end_dt': fx.dt,
                'dt': fx.dt,
                'high': fx.high * 1.001,
                'low': fx.low * 0.999,
                'type': '供应区域',
                'direction': 'Down'
            })
        else:  # 低点分型 -> 需求区域
            ob_data.append({
                'start_dt': fx.dt,
                'end_dt': fx.dt,
                'dt': fx.dt,
                'high': fx.high * 1.001,
                'low': fx.low * 0.999,
                'type': '需求区域',
                'direction': 'Up'
            })
    
    print(f"   生成了 {len(ob_data)} 个Order Block")
    return ob_data


def create_bs_data(czsc):
    """创建买卖点数据"""
    print(f"\\n🎯 生成买卖点数据")
    
    bs_data = []
    
    if len(czsc.bi_list) >= 2:
        for i in range(1, len(czsc.bi_list)):
            prev_bi = czsc.bi_list[i-1]
            curr_bi = czsc.bi_list[i]
            
            if prev_bi.direction == Direction.Down and curr_bi.direction == Direction.Up:
                bs_data.append({
                    'dt': curr_bi.fx_a.dt,
                    'price': curr_bi.fx_a.fx,
                    'op': Operate.LO,
                    'op_desc': '类一买点'
                })
            elif prev_bi.direction == Direction.Up and curr_bi.direction == Direction.Down:
                bs_data.append({
                    'dt': curr_bi.fx_a.dt,
                    'price': curr_bi.fx_a.fx,
                    'op': Operate.SO,
                    'op_desc': '类一卖点'
                })
    
    print(f"   生成了 {len(bs_data)} 个买卖点")
    return bs_data


def prepare_visualization_data(czsc, fvg_data, ob_data, bs_data):
    """准备可视化数据"""
    print(f"\\n📊 准备可视化数据")
    
    # K线数据
    kline = []
    for bar in czsc.bars_raw:
        kline.append({
            'dt': bar.dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'vol': bar.vol,
            'amount': bar.amount
        })
    
    # 分型数据
    fx = []
    for fx_item in czsc.fx_list:
        fx.append({
            'dt': fx_item.dt,
            'fx': fx_item.fx,
            'mark': fx_item.mark.value
        })
    
    # 笔数据
    bi = []
    if len(czsc.bi_list) > 0:
        for bi_item in czsc.bi_list:
            bi.append({'dt': bi_item.fx_a.dt, "bi": bi_item.fx_a.fx})
        bi.append({'dt': czsc.bi_list[-1].fx_b.dt, "bi": czsc.bi_list[-1].fx_b.fx})
    
    print(f"   K线数据: {len(kline)}条")
    print(f"   分型数据: {len(fx)}个")
    print(f"   笔数据: {len(bi)}个")
    print(f"   FVG数据: {len(fvg_data)}个")
    print(f"   OB数据: {len(ob_data)}个")
    print(f"   买卖点数据: {len(bs_data)}个")
    
    return {
        'kline': kline,
        'fx': fx,
        'bi': bi,
        'xd': [],  # 线段数据暂空
        'bs': bs_data,
        'fvg': fvg_data,
        'ob': ob_data
    }


def main():
    """主函数"""
    print("🚀 CZSC Enhanced FVG和OB可视化修复版本")
    print("=" * 60)
    
    try:
        # 1. 加载本地echarts模块
        print("📦 加载本地echarts_plot模块...")
        echarts_module = load_local_echarts_module()
        kline_pro = echarts_module.kline_pro
        
        # 验证函数签名
        import inspect
        sig = inspect.signature(kline_pro)
        print(f"✅ 本地kline_pro函数签名: {sig}")
        
        # 2. 加载数据
        data_file = os.path.join(project_root, "test", "data", "BTCUSDT_1m_2023-09.csv")
        bars = load_real_btc_data(data_file, max_rows=500)
        
        if not bars:
            print("❌ 数据加载失败，退出")
            return
        
        # 3. CZSC分析
        czsc = analyze_czsc(bars)
        
        # 4. 生成增强组件数据
        fvg_data = create_fvg_data(czsc)
        ob_data = create_ob_data(czsc)
        bs_data = create_bs_data(czsc)
        
        # 5. 准备可视化数据
        viz_data = prepare_visualization_data(czsc, fvg_data, ob_data, bs_data)
        
        # 6. 使用本地kline_pro生成可视化（支持FVG和OB）
        print(f"\\n🎨 生成完整可视化图表")
        
        chart = kline_pro(
            kline=viz_data['kline'],
            fx=viz_data['fx'],
            bi=viz_data['bi'],
            xd=viz_data['xd'],
            bs=viz_data['bs'],
            fvg=viz_data['fvg'],    # FVG数据
            ob=viz_data['ob'],      # OB数据
            title="CZSC Enhanced - FVG和OB完整可视化",
            t_seq=[5, 13, 21],
            width="1600px",
            height="900px"
        )
        
        # 7. 保存结果
        result_dir = os.path.join(project_root, "test", "result")
        os.makedirs(result_dir, exist_ok=True)
        output_path = os.path.join(result_dir, "fixed_fvg_ob_visualization.html")
        
        chart.render(output_path)
        
        print(f"\\n✅ 可视化完成!")
        print(f"📊 数据统计:")
        print(f"   K线: {len(viz_data['kline'])}条")
        print(f"   分型: {len(viz_data['fx'])}个")
        print(f"   笔: {len(viz_data['bi'])}个")
        print(f"   FVG: {len(viz_data['fvg'])}个")
        print(f"   Order Block: {len(viz_data['ob'])}个")
        print(f"   买卖点: {len(viz_data['bs'])}个")
        print(f"\\n📈 输出文件: {output_path}")
        print(f"📁 文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
        print(f"\\n🎉 请打开HTML文件查看包含FVG和OB的完整可视化效果!")
        
    except Exception as e:
        print(f"\\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()