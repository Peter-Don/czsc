#!/usr/bin/env python
# coding: utf-8
"""
OB检测数据流调试脚本
"""

import os
import sys
import pandas as pd
from datetime import datetime

# 添加项目根路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from czsc.analyze import CZSC
from czsc.objects import RawBar, NewBar
from czsc.enum import Freq
from czsc.poi.ob import OBDetector


def debug_ob_flow():
    """调试OB检测的数据流"""
    print("=" * 80)
    print("OB检测数据流调试")
    print("=" * 80)
    
    # 使用测试数据
    data_path = os.path.join("test", "data", "BTCUSDT_1m_2023-09.csv")
    
    if not os.path.exists(data_path):
        print(f"❌ 数据文件不存在: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    df['dt'] = pd.to_datetime(df['open_time'])
    df = df.head(200)  # 使用200根K线测试
    
    # 创建K线数据
    bars = []
    for i, row in df.iterrows():
        bar = RawBar(
            symbol="BTCUSDT",
            id=i,
            dt=row['dt'],
            freq=Freq.F1,
            open=float(row['open']),
            close=float(row['close']),
            high=float(row['high']),
            low=float(row['low']),
            vol=float(row['volume']),
            amount=float(row['quote_volume'])
        )
        bars.append(bar)
    
    print(f"📊 准备数据: {len(bars)} 根K线")
    
    # 初始化CZSC
    print("\n🔧 初始化CZSC...")
    c = CZSC(bars, pen_model='standard')
    
    # 检查各个组件的状态
    print(f"\n📈 CZSC组件状态:")
    print(f"   - 原始K线: {len(c.bars_raw)} 根")
    print(f"   - 包含处理后: {len(c.bars_ubi)} 根")
    print(f"   - 分型: {len(c.fx_list)} 个")
    print(f"   - 笔: {len(c.bi_list)} 个")
    print(f"   - FVG: {len(c.fvg_detector.fvgs)} 个")
    print(f"   - OB: {len(c.ob_detector.obs)} 个")
    
    # 检查OB检测的条件
    print(f"\n🔍 OB检测条件检查:")
    print(f"   - len(c.fx_list) >= 3: {len(c.fx_list) >= 3}")
    print(f"   - 分型数量: {len(c.fx_list)}")
    
    if len(c.fx_list) >= 3:
        print("   ✅ 条件满足，OB检测器应该被调用")
        
        # 手动创建newbars用于检测
        print("\n🔧 手动创建newbars...")
        newbars = []
        for bar in c.bars_raw:
            newbar = NewBar(
                symbol=bar.symbol,
                id=bar.id,
                dt=bar.dt,
                freq=bar.freq,
                open=bar.open,
                close=bar.close,
                high=bar.high,
                low=bar.low,
                vol=bar.vol,
                amount=bar.amount,
                elements=[bar]
            )
            newbars.append(newbar)
        
        print(f"   - 创建了 {len(newbars)} 个NewBar")
        
        # 手动调用OB检测器
        print("\n🔧 手动调用OB检测器...")
        c.ob_detector.update_obs(newbars)
        
        print(f"   - 检测到 {len(c.ob_detector.obs)} 个OB")
        
        # 显示OB详细信息
        for i, ob in enumerate(c.ob_detector.obs):
            direction_symbol = "↑" if ob.is_bullish_ob() else "↓"
            print(f"   {i+1}. {direction_symbol} {ob.dt.strftime('%H:%M')} [{ob.low:.2f}, {ob.high:.2f}] "
                  f"大小:{ob.size:.2f} 强度:{ob.strength:.3f}")
    
    else:
        print("   ❌ 条件不满足，OB检测器不会被调用")
        print(f"   需要至少3个分型，当前只有{len(c.fx_list)}个")
    
    # 逐步添加更多K线，观察变化
    print(f"\n📊 逐步添加K线，观察分型生成:")
    
    # 从200根开始，逐步增加到500根
    for target_size in [300, 400, 500]:
        if target_size > len(df):
            continue
            
        print(f"\n🔄 扩展到 {target_size} 根K线...")
        
        # 添加更多K线
        extended_df = df.head(target_size)
        extended_bars = []
        for i, row in extended_df.iterrows():
            bar = RawBar(
                symbol="BTCUSDT",
                id=i,
                dt=row['dt'],
                freq=Freq.F1,
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                vol=float(row['volume']),
                amount=float(row['quote_volume'])
            )
            extended_bars.append(bar)
        
        # 重新初始化CZSC
        c2 = CZSC(extended_bars, pen_model='standard')
        
        print(f"   - 分型数量: {len(c2.fx_list)}")
        print(f"   - 笔数量: {len(c2.bi_list)}")
        print(f"   - FVG数量: {len(c2.fvg_detector.fvgs)}")
        print(f"   - OB数量: {len(c2.ob_detector.obs)}")
        
        if len(c2.fx_list) >= 3:
            print("   ✅ OB检测条件满足")
        else:
            print("   ❌ OB检测条件不满足")
    
    print(f"\n{'='*80}")
    print("调试完成")


if __name__ == "__main__":
    debug_ob_flow()