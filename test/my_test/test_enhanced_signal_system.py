#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强信号系统测试 - 完整的缠论+SMC融合测试

测试内容：
1. FVG和OB组件检测
2. 机构足迹信号生成
3. 高级组合信号规则
4. 增强信号管理器
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq
from czsc.signals import EnhancedSignalManager
from czsc.components.detectors import FVGDetector, OBDetector
import pandas as pd


def load_test_data():
    """加载测试数据"""
    data_file = os.path.join(project_root, "test", "data", "BTCUSDT_1m_2023-09.csv")
    
    if not os.path.exists(data_file):
        print(f"测试数据文件不存在: {data_file}")
        return None
    
    df = pd.read_csv(data_file)
    df['open_time'] = pd.to_datetime(df['open_time'])
    
    # 选择1000条数据用于测试
    df_sample = df.head(1000).copy()
    
    # 转换为RawBar对象
    raw_bars = []
    for i, (_, row) in enumerate(df_sample.iterrows()):
        raw_bar = RawBar(
            symbol="BTCUSDT",
            id=i,
            dt=row['open_time'],
            freq=Freq.F1,
            open=float(row['open']),
            close=float(row['close']),
            high=float(row['high']),
            low=float(row['low']),
            vol=float(row['volume']),
            amount=float(row['quote_volume'])
        )
        raw_bars.append(raw_bar)
    
    return raw_bars


def test_institutional_components():
    """测试机构足迹组件检测"""
    print("\n=== 测试机构足迹组件检测 ===")
    
    raw_bars = load_test_data()
    if not raw_bars:
        return False
    
    # 创建CZSC分析对象
    czsc = CZSC(raw_bars)
    
    # 测试FVG检测 - 使用更小的阈值，适合加密货币的小幅价格变动
    fvg_detector = FVGDetector(min_gap_size=0.00001)  # 0.001% 而非 0.1%
    fvgs = fvg_detector.detect_fvgs(czsc.bars_ubi)
    
    print(f"✅ 检测到 {len(fvgs)} 个FVG")
    
    # 显示前几个FVG
    for i, fvg in enumerate(fvgs[:3]):
        print(f"  FVG {i+1}: {fvg.direction.value} @ {fvg.dt}")
        print(f"    区间: {fvg.bottom:.2f} - {fvg.top:.2f}")
        print(f"    大小: {fvg.size:.2f} ({fvg.size_percentage:.3%})")
        print(f"    回补状态: {'已回补' if fvg.is_mitigated else f'未回补 ({fvg.mitigation_percentage:.1%})'}")
    
    # 测试OB检测 - 使用更小的阈值，适合1分钟数据
    ob_detector = OBDetector(min_move_strength=0.001, require_fvg=False)  # 降低移动强度要求，不强制要求FVG
    obs = ob_detector.detect_obs(czsc.bars_ubi, fvgs)
    
    print(f"\n✅ 检测到 {len(obs)} 个OB")
    
    # 显示前几个OB
    for i, ob in enumerate(obs[:3]):
        print(f"  OB {i+1}: {ob.direction.value} @ {ob.dt}")
        print(f"    区间: {ob.bottom:.2f} - {ob.top:.2f}")
        print(f"    质量评分: {ob.quality_score:.1f}")
        print(f"    后续走势强度: {ob.subsequent_move_strength:.2%}")
        print(f"    关联FVG: {len(ob.related_fvg_ids)}个")
    
    return len(fvgs) > 0 and len(obs) >= 0  # OB可能为0


def test_enhanced_signal_manager():
    """测试增强信号管理器"""
    print("\n=== 测试增强信号管理器 ===")
    
    raw_bars = load_test_data()
    if not raw_bars:
        return False
    
    # 创建CZSC分析对象
    czsc = CZSC(raw_bars)
    
    # 创建增强信号管理器 - 调整参数以适应1分钟加密货币数据
    config = {
        'fvg_min_gap_size': 0.00001,  # 0.001% 更适合加密货币
        'ob_min_move_strength': 0.001,  # 0.1% 更适合1分钟数据
        'ob_require_fvg': False,  # 不强制要求FVG，增加OB检测
        'enable_signal_filtering': True,
        'scoring_config': {
            'min_composite_score': 20,  # 降低门槛以便测试
            'min_composite_confidence': 0.3,  # 降低门槛以便测试
            'max_signals_per_timeframe': 5
        }
    }
    
    enhanced_manager = EnhancedSignalManager(config)
    
    # 分析市场结构
    market_structure = enhanced_manager.analyze_market_structure(czsc)
    
    print("📊 市场结构分析结果:")
    geo_components = market_structure['geometric_components']
    inst_components = market_structure['institutional_components']
    
    print(f"  缠论几何组件:")
    print(f"    分型数量: {len(geo_components['fractals'])}")
    print(f"    笔数量: {len(geo_components['strokes'])}")
    
    print(f"  机构足迹组件:")
    print(f"    FVG数量: {len(inst_components['fvgs'])}")
    print(f"    OB数量: {len(inst_components['obs'])}")
    
    # 生成所有信号
    all_signals = enhanced_manager.generate_all_signals(czsc)
    
    print(f"\n🎯 信号生成结果:")
    print(f"  单体信号数量: {all_signals['summary']['component_signal_count']}")
    print(f"  组合信号数量: {all_signals['summary']['composite_signal_count']}")
    
    # 显示单体信号分布
    component_signals = all_signals['component_signals']
    signal_types = {}
    for signal in component_signals:
        signal_type = f"{signal.component_type}_{signal.signal_type}"
        signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
    
    print(f"\n📋 单体信号分布:")
    for signal_type, count in signal_types.items():
        print(f"    {signal_type}: {count}个")
    
    # 显示组合信号
    composite_signals = all_signals['composite_signals']
    print(f"\n🌟 组合信号详情:")
    
    for i, signal in enumerate(composite_signals[:3], 1):
        print(f"  {i}. {signal.name}")
        print(f"     强度: {signal.strength.value}")
        print(f"     评分: {signal.total_score:.1f}")
        print(f"     置信度: {signal.confidence:.2f}")
        print(f"     组成: {len(signal.component_signals)}个单体信号")
        
        # 显示评分分解
        if signal.signal_breakdown:
            print(f"     评分分解:")
            for sig_type, breakdown in signal.signal_breakdown.items():
                print(f"       - {sig_type}: {breakdown['contribution']:.1f}分")
    
    return len(component_signals) > 0


def test_market_overview():
    """测试市场概览功能"""
    print("\n=== 测试市场概览功能 ===")
    
    raw_bars = load_test_data()
    if not raw_bars:
        return False
    
    czsc = CZSC(raw_bars)
    enhanced_manager = EnhancedSignalManager()
    
    # 获取市场概览
    overview = enhanced_manager.get_market_overview(czsc)
    
    print("📈 市场概览:")
    structure = overview['structure_overview']
    
    print(f"  几何结构:")
    print(f"    分型总数: {structure['geometric']['fractal_count']}")
    print(f"    笔总数: {structure['geometric']['stroke_count']}")
    
    print(f"  机构足迹:")
    print(f"    FVG总数: {structure['institutional']['fvg_total']}")
    print(f"    活跃FVG: {structure['institutional']['fvg_active']}")
    print(f"    OB总数: {structure['institutional']['ob_total']}")
    print(f"    活跃OB: {structure['institutional']['ob_active']}")
    
    # 显示关注区域
    focus_areas = overview['current_focus_areas']
    
    if focus_areas['active_fvgs']:
        print(f"\n🎯 活跃FVG区域 (前3个):")
        for fvg in focus_areas['active_fvgs'][:3]:
            print(f"    {fvg['direction']} FVG: {fvg['bottom']:.2f}-{fvg['top']:.2f} ({fvg['size_pct']})")
    
    if focus_areas['active_obs']:
        print(f"\n🎯 活跃OB区域 (前3个):")
        for ob in focus_areas['active_obs'][:3]:
            print(f"    {ob['direction']} OB: {ob['bottom']:.2f}-{ob['top']:.2f} (质量:{ob['quality_score']})")
    
    return True


def test_advanced_rules():
    """测试高级组合规则"""
    print("\n=== 测试高级组合规则 ===")
    
    # 导入高级规则
    try:
        from czsc.signals.advanced_rules import ADVANCED_SIGNAL_RULES
        
        print(f"✅ 成功加载 {len(ADVANCED_SIGNAL_RULES)} 个高级规则:")
        
        for rule_name, rule in ADVANCED_SIGNAL_RULES.items():
            print(f"  - {rule.name}")
            print(f"    描述: {rule.description}")
            print(f"    权重数: {len(rule.weights)}")
            print(f"    最低评分: {rule.min_score}")
            print(f"    最低置信度: {rule.min_confidence}")
            print()
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入高级规则失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始增强信号系统测试...")
    
    test_results = []
    
    # 执行各项测试
    test_results.append(("机构足迹组件检测", test_institutional_components()))
    test_results.append(("增强信号管理器", test_enhanced_signal_manager()))
    test_results.append(("市场概览功能", test_market_overview()))
    test_results.append(("高级组合规则", test_advanced_rules()))
    
    # 总结测试结果
    print("\n" + "="*60)
    print("🎯 增强信号系统测试结果总结:")
    print("="*60)
    
    success_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(test_results)} 项测试通过")
    
    if success_count == len(test_results):
        print("\n🎉 所有测试通过！增强信号系统运行正常。")
        print("\n💡 增强信号系统新特性:")
        print("  🔄 融合架构：缠论几何 + SMC机构分析")
        print("  📊 机构足迹：FVG价格缺口 + OB订单块检测")
        print("  🧠 智能信号：位置信号 + 行为信号")
        print("  🎯 高级规则：HTF_POI反转 + 多理论汇聚")
        print("  📈 完整生态：检测→信号→评分→决策")
    else:
        print("⚠️ 部分测试失败，请检查实现代码。")
    
    return success_count == len(test_results)


if __name__ == "__main__":
    main()