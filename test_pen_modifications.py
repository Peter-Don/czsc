# coding: utf-8
"""
测试笔判断修改后的功能
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接从模块导入，避免循环导入问题
from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq
import pandas as pd
from datetime import datetime, timedelta

def create_test_data():
    """创建测试数据"""
    bars = []
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    
    # 创建一些测试K线数据
    test_prices = [
        # 向上趋势后反转的数据
        {'open': 100, 'high': 102, 'low': 99, 'close': 101, 'vol': 1000},
        {'open': 101, 'high': 103, 'low': 100, 'close': 102, 'vol': 1100},
        {'open': 102, 'high': 105, 'low': 101, 'close': 104, 'vol': 1200},
        {'open': 104, 'high': 106, 'low': 103, 'close': 105, 'vol': 1300},
        {'open': 105, 'high': 107, 'low': 104, 'close': 106, 'vol': 1400},
        # 极端反转K线（大成交量，大振幅）
        {'open': 106, 'high': 108, 'low': 95, 'close': 96, 'vol': 5000},  # 极端反转
        {'open': 96, 'high': 98, 'low': 94, 'close': 97, 'vol': 1500},
        {'open': 97, 'high': 99, 'low': 95, 'close': 98, 'vol': 1600},
    ]
    
    for i, price_data in enumerate(test_prices):
        bar = RawBar(
            symbol='TEST',
            id=i,
            freq=Freq.F1,
            dt=base_time + timedelta(minutes=i),
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            vol=price_data['vol'],
            amount=price_data['close'] * price_data['vol']
        )
        bars.append(bar)
    
    return bars

def test_standard_mode():
    """测试标准模式"""
    print("=== 测试标准模式 ===")
    bars = create_test_data()
    
    c = CZSC(bars, pen_model='standard')
    
    print(f"标准模式 - 笔数量: {len(c.bi_list)}")
    for i, bi in enumerate(c.bi_list):
        print(f"  笔{i+1}: {bi.direction.value} {bi.fx_a.dt} -> {bi.fx_b.dt}, 长度: {len(bi.bars)}")
    
    return c

def test_flexible_mode():
    """测试灵活模式"""
    print("\n=== 测试灵活模式 ===")
    bars = create_test_data()
    
    c = CZSC(bars, pen_model='flexible')
    
    print(f"灵活模式 - 笔数量: {len(c.bi_list)}")
    for i, bi in enumerate(c.bi_list):
        print(f"  笔{i+1}: {bi.direction.value} {bi.fx_a.dt} -> {bi.fx_b.dt}, 长度: {len(bi.bars)}")
    
    return c

def test_adaptive_mode():
    """测试自适应模式"""
    print("\n=== 测试自适应模式 ===")
    bars = create_test_data()
    
    c = CZSC(bars, pen_model='flexible', use_adaptive_pen=True, 
             adaptive_vol_ratio=2.0, adaptive_atr_ratio=1.5)
    
    print(f"自适应模式 - 笔数量: {len(c.bi_list)}")
    for i, bi in enumerate(c.bi_list):
        print(f"  笔{i+1}: {bi.direction.value} {bi.fx_a.dt} -> {bi.fx_b.dt}, 长度: {len(bi.bars)}")
    
    return c

def test_load_real_data():
    """测试加载真实数据"""
    print("\n=== 测试真实BTC数据 ===")
    
    # 尝试加载BTC数据
    btc_file = "/mnt/d/trading/storage/csv/crypto/futures/1m/BTCUSDT/BTCUSDT_1m_2024-01-01_2024-01-31.csv"
    if os.path.exists(btc_file):
        print(f"加载BTC数据: {btc_file}")
        df = pd.read_csv(btc_file)
        df['dt'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.head(100)  # 只取前100条数据测试
        
        bars = []
        for i, row in df.iterrows():
            bar = RawBar(
                symbol='BTCUSDT',
                id=i,
                freq=Freq.F1,
                dt=row['dt'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                vol=row['volume'],
                amount=row['close'] * row['volume']
            )
            bars.append(bar)
        
        # 测试三种模式
        print("\n--- 标准模式 ---")
        c1 = CZSC(bars, pen_model='standard')
        print(f"标准模式笔数量: {len(c1.bi_list)}")
        
        print("\n--- 灵活模式 ---")
        c2 = CZSC(bars, pen_model='flexible')
        print(f"灵活模式笔数量: {len(c2.bi_list)}")
        
        print("\n--- 自适应模式 ---")
        c3 = CZSC(bars, pen_model='flexible', use_adaptive_pen=True)
        print(f"自适应模式笔数量: {len(c3.bi_list)}")
        
        return c1, c2, c3
    else:
        print("BTC数据文件不存在，跳过真实数据测试")
        return None, None, None

if __name__ == "__main__":
    print("开始测试笔判断修改...")
    
    try:
        # 测试各种模式
        c1 = test_standard_mode()
        c2 = test_flexible_mode()
        c3 = test_adaptive_mode()
        
        # 测试真实数据
        test_load_real_data()
        
        print("\n=== 测试完成 ===")
        print("所有测试都成功运行！")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()