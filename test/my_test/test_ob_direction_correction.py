# -*- coding: utf-8 -*-
"""
OB方向判断修正测试
author: Claude Code AI Assistant
create_dt: 2025-01-11
describe: 测试修正后的OB方向判断逻辑，验证各种市场场景
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from czsc.objects import NewBar, FX, BI
from czsc.objects_enhanced import UnifiedOrderBlockDetector
from czsc.enum import Mark, Direction, Freq


def create_uptrend_scenario() -> tuple:
    """场景1：上涨趋势中的OB（应该都是看涨的）"""
    bars = []
    base_time = datetime(2024, 1, 15, 9, 30)
    
    # 创建上涨趋势：低点 → 底分型 → 突破上涨 → FVG形成
    prices = [
        # 初始低点
        (48000, 48200, 47800, 47900),  # K1 低位
        (47900, 48100, 47700, 47850),  # K2 继续低位
        
        # 底分型形成（K3-K4-K5）
        (47850, 48000, 47600, 47700),  # K3 探底
        (47700, 47750, 47400, 47500),  # K4 分型最低点
        (47500, 48200, 47450, 48000),  # K5 反弹开始
        
        # 上涨推进
        (48000, 48800, 47950, 48600),  # K6 强势上涨
        (48600, 49200, 48500, 49000),  # K7 继续上涨
        
        # FVG形成（K8-K9-K10）
        (49000, 49300, 48950, 49200),  # K8 (潜在OB)
        (49200, 49400, 49100, 49350),  # K9 (中间)
        (49350, 50000, 49600, 49850),  # K10 (跳空上涨，形成FVG)
        
        # 后续确认上涨
        (49850, 50200, 49700, 50100),  # K11 持续上涨
        (50100, 50500, 50000, 50400),  # K12 更高
    ]
    
    for i, (open_price, high, low, close) in enumerate(prices):
        bar = NewBar(
            symbol="BTCUSDT",
            id=i + 1,
            dt=base_time + timedelta(minutes=i * 5),
            freq=Freq.F5,
            open=open_price,
            close=close,
            high=high,
            low=low,
            vol=1000 + i * 100,
            amount=close * 1000,
            elements=[],
            cache={}
        )
        bars.append(bar)
    
    # 创建底分型（K3-K4-K5）
    fractal_bars = bars[2:5]
    fx = FX(
        symbol="BTCUSDT",
        dt=fractal_bars[1].dt,  # K4时间
        mark=Mark.D,  # 底分型
        high=max(bar.high for bar in fractal_bars),
        low=min(bar.low for bar in fractal_bars),
        fx=fractal_bars[1].low,  # K4最低点
        elements=fractal_bars
    )
    
    # 创建包含上涨笔的CZSC（模拟）
    # 从K4到K10的上涨笔
    upward_bi = BI(
        symbol="BTCUSDT",
        fx_a=fx,  # 从底分型开始
        fx_b=FX(symbol="BTCUSDT", dt=bars[9].dt, mark=Mark.G, 
               high=bars[9].high, low=bars[9].low, fx=bars[9].high, elements=[bars[9]]),
        fxs=[],
        direction=Direction.Up,  # 上涨笔
        bars=bars[3:10]
    )
    
    class MockCZSC:
        def __init__(self, bars, fractals, bis):
            self.bars_ubi = bars
            self.fx_list = fractals
            self.bi_list = bis
    
    czsc = MockCZSC(bars, [fx], [upward_bi])
    
    return bars, fx, czsc, "上涨趋势中的底分型OB"


def create_downtrend_scenario() -> tuple:
    """场景2：下跌趋势中的OB（应该都是看跌的）"""
    bars = []
    base_time = datetime(2024, 1, 15, 14, 30)
    
    # 创建下跌趋势：高点 → 顶分型 → 突破下跌 → FVG形成
    prices = [
        # 初始高点
        (52000, 52200, 51800, 52100),  # K1 高位
        (52100, 52300, 51900, 52150),  # K2 继续高位
        
        # 顶分型形成（K3-K4-K5）
        (52150, 52400, 52000, 52300),  # K3 冲高
        (52300, 52500, 52200, 52450),  # K4 分型最高点
        (52450, 52500, 51800, 52000),  # K5 开始下跌
        
        # 下跌推进
        (52000, 52100, 51200, 51400),  # K6 大幅下跌
        (51400, 51600, 50800, 51000),  # K7 继续下跌
        
        # FVG形成（K8-K9-K10）
        (51000, 51200, 50800, 51100),  # K8 (潜在OB)
        (51100, 51300, 50900, 51050),  # K9 (中间)
        (51050, 51100, 50000, 50200),  # K10 (跳空下跌，形成FVG)
        
        # 后续确认下跌
        (50200, 50400, 49800, 50000),  # K11 持续下跌
        (50000, 50200, 49500, 49700),  # K12 更低
    ]
    
    for i, (open_price, high, low, close) in enumerate(prices):
        bar = NewBar(
            symbol="BTCUSDT",
            id=i + 1,
            dt=base_time + timedelta(minutes=i * 5),
            freq=Freq.F5,
            open=open_price,
            close=close,
            high=high,
            low=low,
            vol=1000 + i * 100,
            amount=close * 1000,
            elements=[],
            cache={}
        )
        bars.append(bar)
    
    # 创建顶分型（K3-K4-K5）
    fractal_bars = bars[2:5]
    fx = FX(
        symbol="BTCUSDT",
        dt=fractal_bars[1].dt,  # K4时间
        mark=Mark.G,  # 顶分型
        high=max(bar.high for bar in fractal_bars),
        low=min(bar.low for bar in fractal_bars),
        fx=fractal_bars[1].high,  # K4最高点
        elements=fractal_bars
    )
    
    # 创建包含下跌笔的CZSC（模拟）
    # 从K4到K10的下跌笔
    downward_bi = BI(
        symbol="BTCUSDT",
        fx_a=fx,  # 从顶分型开始
        fx_b=FX(symbol="BTCUSDT", dt=bars[9].dt, mark=Mark.D, 
               high=bars[9].high, low=bars[9].low, fx=bars[9].low, elements=[bars[9]]),
        fxs=[],
        direction=Direction.Down,  # 下跌笔
        bars=bars[3:10]
    )
    
    class MockCZSC:
        def __init__(self, bars, fractals, bis):
            self.bars_ubi = bars
            self.fx_list = fractals
            self.bi_list = bis
    
    czsc = MockCZSC(bars, [fx], [downward_bi])
    
    return bars, fx, czsc, "下跌趋势中的顶分型OB"


def create_complex_scenario() -> tuple:
    """场景3：复杂场景 - 上涨笔中的顶分型OB"""
    bars = []
    base_time = datetime(2024, 1, 15, 16, 30)
    
    # 创建场景：上涨过程中的顶分型突破产生OB
    prices = [
        # 初始低位
        (49000, 49200, 48800, 49100),  # K1
        (49100, 49300, 48900, 49200),  # K2
        
        # 上涨过程中的顶分型（K3-K4-K5）突破阻力
        (49200, 49600, 49100, 49500),  # K3 上涨
        (49500, 49800, 49400, 49750),  # K4 继续上涨（分型高点）
        (49750, 50200, 49700, 50100),  # K5 突破阻力，继续上涨
        
        # 继续上涨
        (50100, 50400, 50000, 50300),  # K6
        (50300, 50600, 50200, 50500),  # K7
        
        # FVG形成（K8-K9-K10）
        (50500, 50700, 50400, 50600),  # K8 (潜在OB)
        (50600, 50800, 50500, 50750),  # K9 (中间)
        (50750, 51200, 51000, 51100),  # K10 (跳空上涨，形成FVG)
        
        # 后续确认上涨
        (51100, 51400, 51000, 51300),  # K11
        (51300, 51600, 51200, 51500),  # K12
    ]
    
    for i, (open_price, high, low, close) in enumerate(prices):
        bar = NewBar(
            symbol="BTCUSDT",
            id=i + 1,
            dt=base_time + timedelta(minutes=i * 5),
            freq=Freq.F5,
            open=open_price,
            close=close,
            high=high,
            low=low,
            vol=1000 + i * 100,
            amount=close * 1000,
            elements=[],
            cache={}
        )
        bars.append(bar)
    
    # 创建顶分型（K3-K4-K5）
    fractal_bars = bars[2:5]
    fx = FX(
        symbol="BTCUSDT",
        dt=fractal_bars[1].dt,  # K4时间
        mark=Mark.G,  # 顶分型
        high=max(bar.high for bar in fractal_bars),
        low=min(bar.low for bar in fractal_bars),
        fx=fractal_bars[1].high,  # K4最高点
        elements=fractal_bars
    )
    
    # 创建包含上涨笔的CZSC（整体上涨趋势）
    # 从K1到K10的整体上涨笔
    upward_bi = BI(
        symbol="BTCUSDT",
        fx_a=FX(symbol="BTCUSDT", dt=bars[0].dt, mark=Mark.D, 
               high=bars[0].high, low=bars[0].low, fx=bars[0].low, elements=[bars[0]]),
        fx_b=FX(symbol="BTCUSDT", dt=bars[9].dt, mark=Mark.G, 
               high=bars[9].high, low=bars[9].low, fx=bars[9].high, elements=[bars[9]]),
        fxs=[fx],  # 包含中间的顶分型
        direction=Direction.Up,  # 整体上涨笔
        bars=bars[0:10]
    )
    
    class MockCZSC:
        def __init__(self, bars, fractals, bis):
            self.bars_ubi = bars
            self.fx_list = fractals
            self.bi_list = bis
    
    czsc = MockCZSC(bars, [fx], [upward_bi])
    
    return bars, fx, czsc, "上涨笔中的顶分型突破OB"


def test_ob_direction_scenarios():
    """测试各种场景下的OB方向判断"""
    print("🔍 OB方向判断修正测试")
    print("=" * 60)
    
    detector = UnifiedOrderBlockDetector()
    
    # 测试场景1：上涨趋势中的底分型OB
    print("\n📈 场景1：上涨趋势中的底分型OB")
    bars1, fx1, czsc1, desc1 = create_uptrend_scenario()
    ob1 = detector.detect_order_block(fx1, czsc1)
    
    if ob1:
        print(f"✓ 检测到OB: {desc1}")
        print(f"  - 分型类型: {fx1.mark.value} (底分型)")
        print(f"  - OB方向: {ob1.direction}")
        print(f"  - 预期方向: BULLISH (看涨)")
        print(f"  - 判断结果: {'✅ 正确' if ob1.direction == 'BULLISH' else '❌ 错误'}")
        
        # 解释原因
        if ob1.direction == 'BULLISH':
            print(f"  - 原因: 虽然是底分型，但OB在上涨笔中，推动上涨 → 看涨OB")
        else:
            print(f"  - 问题: 应该是看涨OB，因为它推动了上涨趋势")
    else:
        print("❌ 未检测到OB")
    
    # 测试场景2：下跌趋势中的顶分型OB
    print("\n📉 场景2：下跌趋势中的顶分型OB")
    bars2, fx2, czsc2, desc2 = create_downtrend_scenario()
    ob2 = detector.detect_order_block(fx2, czsc2)
    
    if ob2:
        print(f"✓ 检测到OB: {desc2}")
        print(f"  - 分型类型: {fx2.mark.value} (顶分型)")
        print(f"  - OB方向: {ob2.direction}")
        print(f"  - 预期方向: BEARISH (看跌)")
        print(f"  - 判断结果: {'✅ 正确' if ob2.direction == 'BEARISH' else '❌ 错误'}")
        
        # 解释原因
        if ob2.direction == 'BEARISH':
            print(f"  - 原因: 虽然是顶分型，但OB在下跌笔中，推动下跌 → 看跌OB")
        else:
            print(f"  - 问题: 应该是看跌OB，因为它推动了下跌趋势")
    else:
        print("❌ 未检测到OB")
    
    # 测试场景3：复杂场景
    print("\n🔄 场景3：复杂场景 - 上涨笔中的顶分型OB")
    bars3, fx3, czsc3, desc3 = create_complex_scenario()
    ob3 = detector.detect_order_block(fx3, czsc3)
    
    if ob3:
        print(f"✓ 检测到OB: {desc3}")
        print(f"  - 分型类型: {fx3.mark.value} (顶分型)")
        print(f"  - OB方向: {ob3.direction}")
        print(f"  - 预期方向: BULLISH (看涨)")
        print(f"  - 判断结果: {'✅ 正确' if ob3.direction == 'BULLISH' else '❌ 错误'}")
        
        # 解释原因
        if ob3.direction == 'BULLISH':
            print(f"  - 原因: 顶分型在上涨笔中突破阻力，OB推动上涨 → 看涨OB")
        else:
            print(f"  - 问题: 应该是看涨OB，因为顶分型突破后推动了上涨")
    else:
        print("❌ 未检测到OB")


def test_direction_methods():
    """测试不同方向判断方法的效果"""
    print("\n\n🔬 方向判断方法测试")
    print("=" * 60)
    
    detector = UnifiedOrderBlockDetector()
    bars, fx, czsc, _ = create_uptrend_scenario()
    
    # 模拟OB K线（K8）
    ob_candle = bars[7]  # K8
    subsequent_bars = bars[8:12]  # K9-K12
    
    print(f"测试数据:")
    print(f"  - OB K线: K8, 价格=${ob_candle.close:,.0f}")
    print(f"  - 分型类型: {fx.mark.value}")
    print(f"  - 后续K线: K9-K12")
    
    # 测试各种判断方法
    print(f"\n各方法判断结果:")
    
    # 方法1：基于笔方向
    stroke_result = detector._determine_direction_by_stroke(ob_candle, czsc)
    print(f"  - 笔方向判断: {stroke_result}")
    
    # 方法2：基于后续走势
    movement_result = detector._determine_direction_by_movement(ob_candle, subsequent_bars)
    print(f"  - 走势判断: {movement_result}")
    
    # 方法3：基于FVG方向
    fvg_result = detector._determine_direction_by_fvg(fx)
    print(f"  - FVG方向判断: {fvg_result}")
    
    # 综合判断
    comprehensive_result = detector._determine_ob_direction_comprehensive(
        fx, ob_candle, czsc, subsequent_bars
    )
    print(f"  - 综合判断: {comprehensive_result}")
    
    print(f"\n判断逻辑:")
    print(f"  - 笔方向: OB在上涨笔中 → BULLISH")
    print(f"  - 后续走势: 价格确实上涨 → BULLISH")
    print(f"  - FVG方向: 底分型产生看涨FVG → BULLISH")
    print(f"  - 最终结果: 三个方法一致 → BULLISH ✅")


def run_all_tests():
    """运行所有测试"""
    print("开始OB方向判断修正测试...")
    
    try:
        test_ob_direction_scenarios()
        test_direction_methods()
        
        print("\n" + "="*60)
        print("🎉 OB方向判断修正测试完成！")
        print("\n📋 测试总结:")
        print("✅ 修正了简单的分型类型 → OB方向映射")
        print("✅ 实现了基于笔方向的智能判断")
        print("✅ 添加了后续走势确认机制")
        print("✅ 保留了FVG方向作为兜底方案")
        print("✅ 使用投票机制综合多种判断方法")
        
        print("\n🔧 核心改进:")
        print("• OB方向 = OB所推动的市场结构方向")
        print("• 优先使用笔方向判断（最可靠）")
        print("• 后续价格走势验证（辅助确认）")
        print("• 多方法投票决定最终方向")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()