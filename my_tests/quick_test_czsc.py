# -*- coding: utf-8 -*-
"""
CZSC 快速测试脚本

基于项目内置功能，快速测试CZSC组件和策略
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from czsc.analyze import CZSC
from czsc.objects import RawBar, Freq
from czsc.utils.echarts_plot import kline_pro
from czsc.mock import generate_symbol_kines
from czsc.utils.bar_generator import format_standard_kline


def test_with_builtin_data():
    """使用内置测试数据进行测试"""
    print("=== 使用内置测试数据测试CZSC ===")
    
    try:
        # 方法1：直接使用test目录的数据
        test_data_path = os.path.join(os.path.dirname(__file__), '../test/data/000001.SH_D.csv')
        if os.path.exists(test_data_path):
            print(f"加载测试数据: {test_data_path}")
            df = pd.read_csv(test_data_path)
            
            # 转换为RawBar格式
            bars = []
            for i, row in df.iterrows():
                try:
                    dt = pd.to_datetime(row['dt']).to_pydatetime()
                    bar = RawBar(
                        symbol='000001.SH',
                        id=i,
                        dt=dt,
                        freq=Freq.D,
                        open=float(row['open']),
                        close=float(row['close']),
                        high=float(row['high']),
                        low=float(row['low']),
                        vol=float(row['vol']),
                        amount=float(row['amount'])
                    )
                    bars.append(bar)
                except Exception as e:
                    continue
            
            print(f"成功加载 {len(bars)} 根K线")
            return test_czsc_analysis(bars, "内置测试数据")
            
    except Exception as e:
        print(f"加载内置数据失败: {e}")
    
    # 方法2：使用模拟数据
    return test_with_mock_data()


def test_with_mock_data():
    """使用模拟数据进行测试"""
    print("=== 使用模拟数据测试CZSC ===")
    
    try:
        # 生成模拟数据
        df = generate_symbol_kines(
            symbol='TEST.SH',
            freq='日线',
            sdt='20220101',
            edt='20231201',
            adjust=True
        )
        
        # 转换为标准K线格式
        bars = format_standard_kline(df, freq='日线')
        
        print(f"生成模拟数据 {len(bars)} 根K线")
        return test_czsc_analysis(bars, "模拟数据")
        
    except Exception as e:
        print(f"生成模拟数据失败: {e}")
        return None


def test_with_btc_data():
    """使用BTC历史数据进行测试"""
    print("=== 使用BTC历史数据测试CZSC ===")
    
    btc_data_path = "/mnt/d/trading/storage/csv/crypto/futures/1m/BTCUSDT"
    
    if not os.path.exists(btc_data_path):
        print(f"BTC数据路径不存在: {btc_data_path}")
        return test_with_mock_data()
    
    try:
        import glob
        csv_files = glob.glob(os.path.join(btc_data_path, "BTCUSDT_1m_2023-*.csv"))
        
        if not csv_files:
            print("未找到BTC数据文件")
            return test_with_mock_data()
        
        # 使用第一个文件
        file = sorted(csv_files)[0]
        df = pd.read_csv(file)
        df['datetime'] = pd.to_datetime(df['open_time'])
        
        # 取前1000根K线进行测试
        df = df.iloc[:1000].reset_index(drop=True)
        
        # 转换为RawBar格式
        bars = []
        for i, row in df.iterrows():
            bar = RawBar(
                symbol='BTCUSDT',
                id=i,
                dt=row['datetime'].to_pydatetime(),
                freq=Freq.F1,
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                vol=float(row['volume']),
                amount=float(row['quote_volume'])
            )
            bars.append(bar)
        
        print(f"加载BTC数据 {len(bars)} 根K线")
        return test_czsc_analysis(bars, "BTC真实数据")
        
    except Exception as e:
        print(f"加载BTC数据失败: {e}")
        return test_with_mock_data()


def test_czsc_analysis(bars, data_source="未知"):
    """测试CZSC分析功能"""
    print(f"\n=== CZSC分析测试 ({data_source}) ===")
    
    try:
        # 创建CZSC分析对象
        c = CZSC(bars)
        
        # 基础统计
        print(f"原始K线数量: {len(c.bars_raw)}")
        print(f"处理后K线数量: {len(c.bars_ubi)}")
        print(f"分型数量: {len(c.fx_list)}")
        print(f"笔数量: {len(c.bi_list)}")
        print(f"完成的笔数量: {len(c.finished_bis)}")
        
        # 分型分析
        if c.fx_list:
            from czsc.enum import Mark
            ding_count = sum(1 for fx in c.fx_list if fx.mark == Mark.G)
            di_count = sum(1 for fx in c.fx_list if fx.mark == Mark.D)
            print(f"顶分型: {ding_count}, 底分型: {di_count}")
            
            # 显示最近的分型
            recent_fx = c.fx_list[-3:] if len(c.fx_list) >= 3 else c.fx_list
            print("\n最近分型:")
            for i, fx in enumerate(recent_fx):
                fx_type = "顶分型" if fx.mark == Mark.G else "底分型"
                print(f"  {i+1}. {fx_type} @ {fx.fx:.2f} ({fx.dt.strftime('%Y-%m-%d %H:%M')})")
        
        # 笔分析
        if c.bi_list:
            from czsc.enum import Direction
            up_bi = sum(1 for bi in c.bi_list if bi.direction == Direction.Up)
            down_bi = sum(1 for bi in c.bi_list if bi.direction == Direction.Down)
            print(f"向上笔: {up_bi}, 向下笔: {down_bi}")
            
            # 显示最近的笔
            recent_bi = c.bi_list[-3:] if len(c.bi_list) >= 3 else c.bi_list
            print("\n最近笔信息:")
            for i, bi in enumerate(recent_bi):
                direction = "向上" if bi.direction == Direction.Up else "向下"
                start_price = bi.fx_a.fx
                end_price = bi.fx_b.fx
                change_pct = (end_price - start_price) / start_price * 100
                print(f"  {i+1}. {direction} {start_price:.2f} -> {end_price:.2f} ({change_pct:+.2f}%)")
        
        # 生成图表
        generate_chart(c, data_source)
        
        return c
        
    except Exception as e:
        print(f"CZSC分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_chart(czsc_obj, title_suffix=""):
    """生成可视化图表"""
    print(f"\n=== 生成可视化图表 ===")
    
    try:
        # 准备K线数据
        kline_data = []
        for bar in czsc_obj.bars_raw:
            kline_data.append({
                'dt': bar.dt,
                'open': bar.open,
                'close': bar.close,
                'high': bar.high,
                'low': bar.low,
                'vol': bar.vol
            })
        
        # 准备分型数据
        fx_data = []
        if czsc_obj.fx_list:
            for fx in czsc_obj.fx_list:
                fx_data.append({
                    'dt': fx.dt,
                    'fx': fx.fx,
                    'mark': fx.mark.value
                })
        
        # 准备笔数据
        bi_data = []
        if czsc_obj.bi_list:
            for bi in czsc_obj.bi_list:
                bi_data.append({
                    'dt': bi.fx_a.dt,
                    'bi': bi.fx_a.fx
                })
                bi_data.append({
                    'dt': bi.fx_b.dt,
                    'bi': bi.fx_b.fx
                })
        
        # 生成图表
        chart_title = f"CZSC分析结果 - {title_suffix}"
        chart = kline_pro(
            kline=kline_data,
            fx=fx_data,
            bi=bi_data,
            title=chart_title,
            width="1400px",
            height="680px"
        )
        
        # 保存图表
        output_path = f"/home/moses2204/proj/czsc_enhanced/my_tests/czsc_analysis_{title_suffix.replace(' ', '_')}.html"
        chart.render(output_path)
        print(f"图表已保存: {output_path}")
        
        return chart
        
    except Exception as e:
        print(f"生成图表失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_signals():
    """测试信号系统"""
    print("\n=== 测试信号系统 ===")
    
    try:
        from czsc.traders.base import CzscSignals
        from czsc.utils.bar_generator import BarGenerator
        
        # 生成测试数据
        df = generate_symbol_kines('TEST.SH', '30分钟', '20230101', '20231201')
        bars = format_standard_kline(df, freq='30分钟')
        
        # 配置信号
        signals_config = [
            {
                'name': 'czsc.signals.cxt_bi_status_V230101',
                'freq': '30分钟',
                'di': 1
            }
        ]
        
        # 创建信号计算器
        bg = BarGenerator(base_freq='30分钟', freqs=['30分钟'], max_count=2000)
        for bar in bars:
            bg.update(bar)
        
        cs = CzscSignals(bg, signals_config=signals_config)
        
        # 计算信号
        for bar in bars[-100:]:  # 测试最后100根K线
            cs.update_signals(bar)
        
        # 输出信号
        print("当前信号:")
        for key, value in cs.s.items():
            print(f"  {key}: {value}")
        
        return cs
        
    except Exception as e:
        print(f"信号测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    print("🚀 CZSC 快速测试脚本")
    print("=" * 50)
    
    # 测试数据源优先级：BTC真实数据 > 内置数据 > 模拟数据
    czsc_result = test_with_btc_data()
    
    if czsc_result is None:
        print("\n尝试其他数据源...")
        czsc_result = test_with_builtin_data()
    
    # 测试信号系统
    signal_result = test_signals()
    
    print("\n=" * 50)
    print("✅ 测试完成!")
    
    if czsc_result:
        print(f"CZSC分析成功，共识别 {len(czsc_result.fx_list)} 个分型，{len(czsc_result.bi_list)} 个笔")
    
    if signal_result:
        print(f"信号系统测试成功，当前有 {len(signal_result.s)} 个信号")
    
    print("\n📁 检查 my_tests/ 目录下的图表文件")


if __name__ == "__main__":
    main()