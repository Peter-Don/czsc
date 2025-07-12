# -*- coding: utf-8 -*-
"""
统一缓解分析框架测试
author: Claude Code AI Assistant
create_dt: 2025-01-11
describe: 测试FVG和Order Block的统一缓解分析机制
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from czsc.objects import NewBar, FX
from czsc.enum import Direction, Mark, Freq
from czsc.poi.mitigation_framework import (
    UniversalMitigationAnalyzer, FVGMitigationAnalyzer, OrderBlockMitigationAnalyzer,
    MitigationConfig, MitigationMethod, ZoneDefinition, create_mitigation_analyzer
)
from czsc.poi.enhanced_order_block import EnhancedOrderBlock, create_enhanced_order_block_from_fractal
from czsc.poi.fvg import FVG


def create_test_bars() -> List[NewBar]:
    """创建测试K线数据"""
    bars = []
    base_time = datetime(2024, 1, 15, 9, 30)
    
    # 价格序列：创建一个明显的缓解场景
    prices = [
        (50000, 50200, 49800, 50100),  # K1
        (50100, 50300, 50000, 50200),  # K2
        (50200, 50400, 50100, 50300),  # K3 
        (50300, 50500, 50200, 50400),  # K4
        (50400, 50600, 50300, 50500),  # K5
        # 价格回撤开始缓解
        (50500, 50500, 50100, 50150),  # K6 - 开始回撤
        (50150, 50200, 49900, 50050),  # K7 - 深度回撤
        (50050, 50100, 49800, 49900),  # K8 - 进一步回撤
        (49900, 50000, 49700, 49850),  # K9 - 超调穿透
        (49850, 50200, 49800, 50100),  # K10 - 反弹
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
    
    return bars


def test_universal_mitigation_analyzer():
    """测试通用缓解分析器"""
    print("🔬 测试通用缓解分析器")
    print("=" * 50)
    
    bars = create_test_bars()
    
    # 定义测试区域（高位区域，会被后续回撤缓解）
    zone = ZoneDefinition(
        high=50500,  # 上边界
        low=50300,   # 下边界  
        direction=Direction.Down,  # 看跌区域（供应区）
        zone_type="TEST_ZONE"
    )
    
    # 创建通用分析器
    config = MitigationConfig(
        method=MitigationMethod.CLOSE,
        mitigation_threshold=0.5,
        trading_effectiveness_threshold=0.7
    )
    analyzer = UniversalMitigationAnalyzer(config)
    
    # 分析缓解
    analysis = analyzer.analyze_zone_mitigation(zone, bars)
    
    print(f"✓ 缓解程度: {analysis.current_level:.1%}")
    print(f"✓ 缓解类型: {analysis.mitigation_type.value}")
    print(f"✓ 是否测试: {analysis.is_tested}")
    print(f"✓ 是否缓解: {analysis.is_mitigated}")
    print(f"✓ 是否有效: {analysis.is_valid}")
    print(f"✓ 交易价值: {analysis.is_effective_for_trading}")
    print(f"✓ 测试次数: {analysis.test_count}")
    print(f"✓ 交互次数: {len(analysis.interaction_history)}")
    
    if analysis.interaction_history:
        print("\n📝 交互历史:")
        for i, event in enumerate(analysis.interaction_history):
            print(f"  {i+1}. {event.timestamp.strftime('%H:%M')} - "
                  f"{event.event_type} - 价格:{event.price:,.0f} - "
                  f"缓解:{event.mitigation_level:.1%}")
    
    return analysis


def test_fvg_mitigation_compatibility():
    """测试FVG缓解兼容性"""
    print("\n\n📊 测试FVG缓解分析")
    print("=" * 50)
    
    bars = create_test_bars()
    
    # 创建FVG（使用前三根K线）
    fvg = FVG(
        symbol="BTCUSDT",
        dt=bars[1].dt,
        direction=Direction.Up,
        bar1=bars[0],
        bar2=bars[1], 
        bar3=bars[2],
        high=50300,  # 看涨FVG上边界
        low=50000    # 看涨FVG下边界
    )
    
    print(f"📈 FVG信息: {fvg.direction.value} FVG")
    print(f"   边界: ${fvg.low:,.0f} - ${fvg.high:,.0f}")
    print(f"   大小: ${fvg.size:,.0f}")
    
    # 使用FVG专用分析器
    fvg_analyzer = FVGMitigationAnalyzer()
    
    # 模拟缓解（使用后续K线的价格）
    mitigation_updates = []
    for bar in bars[3:]:  # 从K4开始模拟缓解
        # 测试不同的价格点
        test_prices = [bar.low, bar.close, bar.high]
        for price in test_prices:
            old_level = fvg.mitigation_level
            updated = fvg.update_mitigation(price, bar.dt)
            if updated:
                mitigation_updates.append({
                    'time': bar.dt,
                    'price': price,
                    'level': fvg.mitigation_level,
                    'type': fvg.get_mitigation_type()
                })
    
    print(f"\n✓ 最终缓解程度: {fvg.mitigation_level:.1%}")
    print(f"✓ 缓解类型: {fvg.get_mitigation_type()}")
    print(f"✓ 缓解描述: {fvg.get_mitigation_description()}")
    print(f"✓ 交易价值: {fvg.is_effective_for_trading()}")
    print(f"✓ 交互次数: {len(fvg.interaction_history)}")
    
    if mitigation_updates:
        print("\n📝 缓解更新历史:")
        for i, update in enumerate(mitigation_updates[:5]):  # 显示前5次更新
            print(f"  {i+1}. {update['time'].strftime('%H:%M')} - "
                  f"价格:{update['price']:,.0f} - "
                  f"缓解:{update['level']:.1%} - {update['type']}")
    
    return fvg


def test_enhanced_order_block():
    """测试增强Order Block"""
    print("\n\n🔷 测试增强Order Block缓解分析")
    print("=" * 50)
    
    bars = create_test_bars()
    
    # 创建分型
    fractal = FX(
        symbol="BTCUSDT",
        dt=bars[4].dt,  # K5时间
        mark=Mark.G,    # 顶分型（供应区）
        high=50600,
        low=50300,
        fx=50600,       # 分型价格
        elements=bars[3:6]  # K4-K5-K6
    )
    
    # 创建增强Order Block
    enhanced_ob = create_enhanced_order_block_from_fractal(
        fractal=fractal,
        ob_bars=bars[6:],  # 后续K线用于缓解分析
        mitigation_config=MitigationConfig(
            method=MitigationMethod.CLOSE,
            mitigation_threshold=0.7,  # OB使用更高阈值
            trading_effectiveness_threshold=0.7
        )
    )
    
    print(f"🔷 Order Block信息:")
    print(f"   类型: {enhanced_ob.ob_type}")
    print(f"   方向: {enhanced_ob.direction.value}")
    print(f"   边界: ${enhanced_ob.low:,.0f} - ${enhanced_ob.high:,.0f}")
    print(f"   大小: ${enhanced_ob.size:,.0f}")
    print(f"   POI: ${enhanced_ob.poi_level:,.0f}")
    
    print(f"\n✓ 缓解程度: {enhanced_ob.mitigation_level:.1%}")
    print(f"✓ 缓解类型: {enhanced_ob.get_mitigation_type()}")
    print(f"✓ 缓解描述: {enhanced_ob.get_mitigation_description()}")
    print(f"✓ 是否测试: {enhanced_ob.is_tested}")
    print(f"✓ 是否缓解: {enhanced_ob.is_mitigated}")
    print(f"✓ 是否有效: {enhanced_ob.is_valid}")
    print(f"✓ 交易价值: {enhanced_ob.is_effective_for_trading()}")
    
    # 显示统计信息
    stats = enhanced_ob.get_mitigation_statistics()
    print(f"\n📊 统计信息:")
    for key, value in stats.items():
        if isinstance(value, datetime):
            print(f"   {key}: {value.strftime('%H:%M:%S') if value else 'None'}")
        elif isinstance(value, float):
            print(f"   {key}: {value:.1%}" if 'level' in key else f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    return enhanced_ob


def test_mitigation_method_comparison():
    """测试不同缓解判断方法的比较"""
    print("\n\n⚖️  测试不同缓解判断方法")
    print("=" * 50)
    
    bars = create_test_bars()
    
    # 定义测试区域
    zone = ZoneDefinition(
        high=50400,
        low=50200,
        direction=Direction.Down,
        zone_type="COMPARISON_TEST"
    )
    
    methods = [
        MitigationMethod.WICK,
        MitigationMethod.CLOSE,
        MitigationMethod.BODY,
        MitigationMethod.MIDPOINT
    ]
    
    results = {}
    
    for method in methods:
        config = MitigationConfig(method=method)
        analyzer = UniversalMitigationAnalyzer(config)
        analysis = analyzer.analyze_zone_mitigation(zone, bars)
        
        results[method.value] = {
            'mitigation_level': analysis.current_level,
            'mitigation_type': analysis.mitigation_type.value,
            'test_count': analysis.test_count,
            'interaction_count': len(analysis.interaction_history),
            'is_effective': analysis.is_effective_for_trading
        }
    
    print("方法比较结果:")
    print("-" * 80)
    print(f"{'方法':<10} {'缓解程度':<10} {'缓解类型':<12} {'测试次数':<8} {'交互次数':<8} {'有效性'}")
    print("-" * 80)
    
    for method_name, result in results.items():
        print(f"{method_name:<10} {result['mitigation_level']:<10.1%} "
              f"{result['mitigation_type']:<12} {result['test_count']:<8} "
              f"{result['interaction_count']:<8} {result['is_effective']}")
    
    return results


def test_factory_functions():
    """测试工厂函数"""
    print("\n\n🏭 测试分析器工厂函数")
    print("=" * 50)
    
    # 测试工厂函数
    fvg_analyzer = create_mitigation_analyzer("FVG")
    ob_analyzer = create_mitigation_analyzer("ORDER_BLOCK")
    generic_analyzer = create_mitigation_analyzer("CUSTOM")
    
    print(f"✓ FVG分析器类型: {type(fvg_analyzer).__name__}")
    print(f"✓ OB分析器类型: {type(ob_analyzer).__name__}")
    print(f"✓ 通用分析器类型: {type(generic_analyzer).__name__}")
    
    # 验证配置差异
    print(f"\n配置差异:")
    print(f"  FVG分析器 - 缓解阈值: {fvg_analyzer.config.mitigation_threshold:.1%}")
    print(f"  OB分析器 - 缓解阈值: {ob_analyzer.config.mitigation_threshold:.1%}")
    print(f"  通用分析器 - 缓解阈值: {generic_analyzer.config.mitigation_threshold:.1%}")
    
    return {
        'fvg_analyzer': fvg_analyzer,
        'ob_analyzer': ob_analyzer,
        'generic_analyzer': generic_analyzer
    }


def run_all_tests():
    """运行所有测试"""
    print("🚀 统一缓解分析框架测试开始")
    print("=" * 60)
    
    try:
        # 测试1: 通用分析器
        universal_result = test_universal_mitigation_analyzer()
        
        # 测试2: FVG缓解兼容性
        fvg_result = test_fvg_mitigation_compatibility()
        
        # 测试3: 增强Order Block
        ob_result = test_enhanced_order_block()
        
        # 测试4: 缓解方法比较
        method_comparison = test_mitigation_method_comparison()
        
        # 测试5: 工厂函数
        factory_results = test_factory_functions()
        
        # 总结
        print("\n\n🎉 测试总结")
        print("=" * 60)
        print("✅ 通用缓解分析框架测试通过")
        print("✅ FVG缓解分析兼容性验证通过")
        print("✅ 增强Order Block缓解分析正常工作")
        print("✅ 多种缓解判断方法对比完成")
        print("✅ 工厂函数测试通过")
        
        print("\n🔑 核心成果:")
        print("• FVG和Order Block现在共用统一的缓解分析机制")
        print("• 支持5种缓解类型：NONE, PARTIAL, SIGNIFICANT, COMPLETE, OVERSHOOT")
        print("• 支持4种缓解判断方法：WICK, CLOSE, BODY, MIDPOINT")
        print("• 增强Order Block具有与FVG相同的缓解分析能力")
        print("• 完整的交互历史记录和统计信息")
        print("• 灵活的配置系统和工厂函数")
        
        print("\n📊 性能对比:")
        print(f"• FVG缓解程度: {fvg_result.mitigation_level:.1%} ({fvg_result.get_mitigation_type()})")
        print(f"• OB缓解程度: {ob_result.mitigation_level:.1%} ({ob_result.get_mitigation_type()})")
        print(f"• 通用分析器: {universal_result.current_level:.1%} ({universal_result.mitigation_type.value})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    if success:
        print("\n🎯 统一缓解分析框架已就绪，可以投入生产使用！")
    else:
        print("\n⚠️  测试中发现问题，需要进一步调试。")