#!/usr/bin/env python
# coding: utf-8
"""
OB检测详细调试脚本 - 分析update方法中的调用点
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


def debug_ob_detailed():
    """详细调试OB检测的调用点"""
    print("=" * 80)
    print("OB检测详细调试 - 分析update方法调用点")
    print("=" * 80)
    
    # 使用测试数据
    data_path = os.path.join("test", "data", "BTCUSDT_1m_2023-09.csv")
    
    if not os.path.exists(data_path):
        print(f"❌ 数据文件不存在: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    df['dt'] = pd.to_datetime(df['open_time'])
    df = df.head(100)  # 使用100根K线测试
    
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
    
    # 创建自定义CZSC类来监控OB检测调用
    class DebugCZSC(CZSC):
        def __init__(self, bars, *args, **kwargs):
            self.ob_call_count = 0
            self.ob_call_details = []
            super().__init__(bars, *args, **kwargs)
        
        def update(self, bar):
            """重写update方法，添加调试信息"""
            print(f"\n🔄 更新K线: {bar.dt.strftime('%H:%M')} - 价格: {bar.close:.2f}")
            
            # 调用父类的update方法
            old_fx_count = len(self.fx_list) if hasattr(self, 'fx_list') else 0
            old_ob_count = len(self.ob_detector.obs) if hasattr(self, 'ob_detector') else 0
            
            super().update(bar)
            
            new_fx_count = len(self.fx_list)
            new_ob_count = len(self.ob_detector.obs)
            
            print(f"   - 分型数量: {old_fx_count} → {new_fx_count}")
            print(f"   - OB数量: {old_ob_count} → {new_ob_count}")
            
            # 检查是否达到OB检测条件
            if new_fx_count >= 3:
                print(f"   ✅ 达到OB检测条件 (分型数: {new_fx_count})")
                if new_ob_count > old_ob_count:
                    print(f"   🎯 新增OB: {new_ob_count - old_ob_count} 个")
                    self.ob_call_count += 1
                    self.ob_call_details.append({
                        'bar_dt': bar.dt,
                        'fx_count': new_fx_count,
                        'ob_count': new_ob_count,
                        'new_obs': new_ob_count - old_ob_count
                    })
            else:
                print(f"   ❌ 未达到OB检测条件 (分型数: {new_fx_count} < 3)")
    
    # 初始化调试版本的CZSC
    print("\n🔧 初始化DebugCZSC...")
    c = DebugCZSC(bars[:50], pen_model='standard')  # 先用50根K线初始化
    
    print(f"\n📈 初始状态:")
    print(f"   - 分型数量: {len(c.fx_list)}")
    print(f"   - 笔数量: {len(c.bi_list)}")
    print(f"   - OB数量: {len(c.ob_detector.obs)}")
    print(f"   - OB调用次数: {c.ob_call_count}")
    
    # 逐个添加剩余的K线
    print(f"\n📊 逐个添加K线，观察OB检测调用:")
    
    for i, bar in enumerate(bars[50:], 51):
        print(f"\n--- 第 {i} 根K线 ---")
        c.update(bar)
        
        # 如果有新的OB生成，显示详细信息
        if len(c.ob_detector.obs) > 0:
            latest_ob = c.ob_detector.obs[-1]
            direction_symbol = "↑" if latest_ob.is_bullish_ob() else "↓"
            print(f"   💡 最新OB: {direction_symbol} {latest_ob.dt.strftime('%H:%M')} "
                  f"[{latest_ob.low:.2f}, {latest_ob.high:.2f}] 强度:{latest_ob.strength:.3f}")
        
        # 如果达到一定数量就停止
        if i >= 80:  # 处理到第80根K线
            break
    
    # 总结
    print(f"\n{'='*60}")
    print("📊 调试总结:")
    print(f"   - 总处理K线: {len(c.bars_raw)} 根")
    print(f"   - 最终分型数: {len(c.fx_list)}")
    print(f"   - 最终OB数: {len(c.ob_detector.obs)}")
    print(f"   - OB检测调用次数: {c.ob_call_count}")
    
    print(f"\n📋 OB调用详情:")
    for i, detail in enumerate(c.ob_call_details, 1):
        print(f"   {i}. {detail['bar_dt'].strftime('%H:%M')} - "
              f"分型:{detail['fx_count']}, OB总数:{detail['ob_count']}, "
              f"新增:{detail['new_obs']}")
    
    # 显示所有OB
    print(f"\n🎯 所有检测到的OB:")
    for i, ob in enumerate(c.ob_detector.obs, 1):
        direction_symbol = "↑" if ob.is_bullish_ob() else "↓"
        status = "Broken" if ob.is_broken else ("Tested" if ob.is_tested else "Active")
        print(f"   {i}. {direction_symbol} {ob.dt.strftime('%H:%M')} "
              f"[{ob.low:.2f}, {ob.high:.2f}] 强度:{ob.strength:.3f} ({status})")
    
    print(f"\n{'='*80}")
    print("详细调试完成")


if __name__ == "__main__":
    debug_ob_detailed()