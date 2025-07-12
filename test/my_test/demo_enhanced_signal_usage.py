#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强信号系统使用演示 - 完整的缠论+SMC融合交易信号系统
参照how_to_use_visualization.py的写法

展示如何在实际交易中使用增强信号系统：
1. 基础使用方法
2. 不同市场环境下的配置选择
3. 信号解读和交易决策
4. 可视化分析
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目根路径
project_root = '/home/moses2204/proj/czsc_enhanced'
sys.path.insert(0, project_root)

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq
from czsc.signals import EnhancedSignalManager
from czsc.components.detectors import FVGDetector, OBDetector
from czsc.signals.advanced_rules import ADVANCED_SIGNAL_RULES


def load_sample_data() -> List[RawBar]:
    """加载示例数据"""
    data_file = os.path.join(project_root, "test/data/BTCUSDT_1m_2023-09.csv")
    
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return []
    
    df = pd.read_csv(data_file)
    df['open_time'] = pd.to_datetime(df['open_time'])
    
    # 选择前500根K线用于演示
    df_sample = df.head(500).copy()
    
    bars = []
    for i, (_, row) in enumerate(df_sample.iterrows()):
        bar = RawBar(
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
        bars.append(bar)
    
    return bars


def demo_basic_usage():
    """演示基础使用方法"""
    print("=" * 80)
    print("🚀 增强信号系统基础使用演示")
    print("=" * 80)
    
    # 加载数据
    bars = load_sample_data()
    if not bars:
        return
    
    print(f"✅ 加载示例数据: {len(bars)} 根K线")
    print(f"📅 时间范围: {bars[0].dt.strftime('%Y-%m-%d %H:%M')} - {bars[-1].dt.strftime('%Y-%m-%d %H:%M')}")
    
    print("\n📖 方法1: 快速开始 - 使用默认配置")
    print("```python")
    print("# 创建CZSC分析对象")
    print("czsc = CZSC(bars)")
    print()
    print("# 创建增强信号管理器（使用默认配置）")
    print("manager = EnhancedSignalManager()")
    print()
    print("# 获取最佳信号")
    print("best_signals = manager.get_best_signals(czsc, limit=3)")
    print("```")
    
    # 实际执行
    czsc = CZSC(bars)
    manager = EnhancedSignalManager()
    best_signals = manager.get_best_signals(czsc, limit=3)
    
    print(f"✅ 快速分析完成:")
    print(f"   - 检测到 {len(czsc.fx_list)} 个分型")
    print(f"   - 检测到 {len(czsc.bi_list)} 个笔")
    print(f"   - 生成了 {len(best_signals)} 个高质量组合信号")
    
    for i, signal in enumerate(best_signals, 1):
        print(f"   {i}. {signal.name}: 评分{signal.total_score:.1f}, 置信度{signal.confidence:.2f}")
    
    print("\n📖 方法2: 完整分析 - 获取所有信号详情")
    print("```python")
    print("# 生成所有类型的信号")
    print("all_signals = manager.generate_all_signals(czsc)")
    print()
    print("# 获取市场概览")
    print("overview = manager.get_market_overview(czsc)")
    print("```")
    
    all_signals = manager.generate_all_signals(czsc)
    overview = manager.get_market_overview(czsc)
    
    print(f"✅ 完整分析结果:")
    print(f"   📊 市场结构:")
    print(f"      - 分型: {overview['structure_overview']['geometric']['fractal_count']}个")
    print(f"      - 笔: {overview['structure_overview']['geometric']['stroke_count']}个")
    print(f"      - FVG: {overview['structure_overview']['institutional']['fvg_total']}个")
    print(f"      - OB: {overview['structure_overview']['institutional']['ob_total']}个")
    print(f"   🎯 信号统计:")
    print(f"      - 单体信号: {all_signals['summary']['component_signal_count']}个")
    print(f"      - 组合信号: {all_signals['summary']['composite_signal_count']}个")


def demo_market_scenarios():
    """演示不同市场环境下的配置选择"""
    print("\n" + "=" * 80)
    print("📈 不同市场环境下的配置选择演示")
    print("=" * 80)
    
    bars = load_sample_data()
    if not bars:
        return
    
    czsc = CZSC(bars)
    
    # 定义不同市场环境的配置
    market_configs = {
        '震荡市场': {
            'description': '横盘整理，频繁假突破',
            'config': {
                'fvg_min_gap_size': 0.0001,  # 较高阈值，过滤噪音
                'ob_min_move_strength': 0.005,  # 要求更强的移动
                'ob_require_fvg': True,  # 严格要求FVG确认
                'scoring_config': {
                    'min_composite_score': 80,  # 高评分要求
                    'min_composite_confidence': 0.6,  # 高置信度
                }
            }
        },
        '趋势市场': {
            'description': '明确趋势，动量充足',
            'config': {
                'fvg_min_gap_size': 0.00005,  # 中等阈值
                'ob_min_move_strength': 0.002,  # 适中的移动要求
                'ob_require_fvg': False,  # 不强制要求FVG
                'scoring_config': {
                    'min_composite_score': 50,  # 中等评分
                    'min_composite_confidence': 0.5,  # 中等置信度
                }
            }
        },
        '突破市场': {
            'description': '关键位置突破，需要快速捕捉',
            'config': {
                'fvg_min_gap_size': 0.00001,  # 低阈值，高敏感度
                'ob_min_move_strength': 0.001,  # 低移动要求
                'ob_require_fvg': False,  # 不强制要求
                'scoring_config': {
                    'min_composite_score': 30,  # 低评分，多机会
                    'min_composite_confidence': 0.4,  # 较低置信度
                }
            }
        }
    }
    
    results = {}
    
    for market_type, market_info in market_configs.items():
        print(f"\n🎯 {market_type} 配置测试")
        print(f"📝 特点: {market_info['description']}")
        
        # 创建对应配置的管理器
        manager = EnhancedSignalManager(market_info['config'])
        
        # 分析信号
        signals = manager.generate_all_signals(czsc)
        
        print(f"✅ {market_type} 分析完成:")
        print(f"   🔍 机构足迹: FVG {signals['summary']['fvg_count']}个, OB {signals['summary']['ob_count']}个")
        print(f"   🎯 信号数量: 单体{signals['summary']['component_signal_count']}个, 组合{signals['summary']['composite_signal_count']}个")
        
        if signals['composite_signals']:
            avg_score = sum(s.total_score for s in signals['composite_signals']) / len(signals['composite_signals'])
            print(f"   📊 平均评分: {avg_score:.1f}")
        
        results[market_type] = signals
    
    # 对比分析
    print(f"\n📊 不同市场环境配置对比:")
    print(f"{'市场类型':<10} {'FVG':<6} {'OB':<6} {'单体信号':<8} {'组合信号':<8}")
    print("-" * 50)
    
    for market_type, signals in results.items():
        print(f"{market_type:<10} {signals['summary']['fvg_count']:<6} "
              f"{signals['summary']['ob_count']:<6} {signals['summary']['component_signal_count']:<8} "
              f"{signals['summary']['composite_signal_count']:<8}")


def demo_signal_interpretation():
    """演示信号解读和交易决策"""
    print("\n" + "=" * 80)
    print("🧠 信号解读和交易决策演示")
    print("=" * 80)
    
    bars = load_sample_data()
    if not bars:
        return
    
    czsc = CZSC(bars)
    
    # 使用标准配置
    config = {
        'fvg_min_gap_size': 0.00005,
        'ob_min_move_strength': 0.002,
        'scoring_config': {
            'min_composite_score': 40,
            'min_composite_confidence': 0.4,
        }
    }
    
    manager = EnhancedSignalManager(config)
    all_signals = manager.generate_all_signals(czsc)
    
    print("📋 信号解读指南:")
    print()
    
    # 解读组合信号
    composite_signals = all_signals['composite_signals']
    if composite_signals:
        print("🎯 组合信号解读:")
        
        for i, signal in enumerate(composite_signals[:3], 1):
            print(f"\n   {i}. {signal.name}")
            print(f"      📊 基础信息:")
            print(f"         - 强度: {signal.strength.value} ({signal.strength.name})")
            print(f"         - 方向: {signal.direction.value}")
            print(f"         - 评分: {signal.total_score:.1f}")
            print(f"         - 置信度: {signal.confidence:.2f}")
            
            print(f"      💡 交易建议:")
            
            # 根据强度给出建议
            if signal.total_score >= 100:
                print(f"         🟢 高质量信号，建议重点关注")
                position_size = "标准仓位"
            elif signal.total_score >= 60:
                print(f"         🟡 中等质量信号，适度参与")
                position_size = "轻仓位"
            else:
                print(f"         🟠 较弱信号，谨慎参与或忽略")
                position_size = "极轻仓位"
            
            print(f"         📏 建议仓位: {position_size}")
            
            # 根据信号类型给出策略建议
            if 'HTF_POI' in signal.name:
                print(f"         ⏰ 策略: 高时框确认反转，适合中长期持有")
            elif 'Scalping' in signal.name:
                print(f"         ⚡ 策略: 短期快进快出，严格止损")
            elif 'Swing' in signal.name:
                print(f"         📈 策略: 波段交易，跟随趋势")
            else:
                print(f"         🎯 策略: 标准反转交易，注意确认")
            
            # 显示评分分解
            if signal.signal_breakdown:
                print(f"      📈 评分分解:")
                for component, breakdown in signal.signal_breakdown.items():
                    print(f"         - {component}: {breakdown['contribution']:.1f}分")
    
    # 解读单体信号
    component_signals = all_signals['component_signals']
    signal_types = {}
    
    for signal in component_signals:
        signal_type = f"{signal.component_type}_{signal.signal_type}"
        if signal_type not in signal_types:
            signal_types[signal_type] = []
        signal_types[signal_type].append(signal)
    
    print(f"\n🔍 单体信号类型分析:")
    for signal_type, signals in signal_types.items():
        avg_score = sum(s.score for s in signals) / len(signals)
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        print(f"   📌 {signal_type}: {len(signals)}个")
        print(f"      平均评分: {avg_score:.1f}, 平均置信度: {avg_confidence:.2f}")
        
        # 给出解读
        component_type, signal_type_name = signal_type.split('_', 1)
        
        if component_type == 'fractal':
            if signal_type_name == 'power':
                print(f"      💪 分型力度信号：反映价格反转的强度")
            elif signal_type_name == 'position':
                print(f"      📍 分型位置信号：关键支撑阻力位置")
            elif signal_type_name == 'behavior':
                print(f"      🎭 分型行为信号：流动性扫除等机构行为")
            elif signal_type_name == 'timing':
                print(f"      ⏰ 分型时机信号：最佳入场时间窗口")
        elif component_type == 'fvg':
            print(f"      📊 FVG质量信号：价格缺口的交易价值")
        elif component_type == 'ob':
            print(f"      🏢 OB质量信号：订单块的机构兴趣度")


def demo_visualization_integration():
    """演示可视化集成"""
    print("\n" + "=" * 80)
    print("📊 可视化集成演示")
    print("=" * 80)
    
    bars = load_sample_data()
    if not bars:
        return
    
    czsc = CZSC(bars)
    manager = EnhancedSignalManager()
    
    print("🎨 可视化方法:")
    print()
    print("📖 方法1: 使用内置可视化")
    print("```python")
    print("# 基础图表（包含分型和笔）")
    print("chart = czsc.to_echarts(width='1400px', height='700px')")
    print("chart.render('czsc_analysis.html')")
    print("```")
    
    print("\n📖 方法2: 增强可视化测试")
    print("```python")
    print("# 运行完整的可视化测试")
    print("python test/test_enhanced_signal_visualization.py")
    print("```")
    
    print("\n📖 方法3: 自定义可视化")
    print("```python")
    print("# 获取信号数据")
    print("signals = manager.generate_all_signals(czsc)")
    print()
    print("# 提取可视化数据")
    print("fvgs = signals['market_structure']['institutional_components']['fvgs']")
    print("obs = signals['market_structure']['institutional_components']['obs']")
    print("composite_signals = signals['composite_signals']")
    print()
    print("# 添加自定义标注...")
    print("```")
    
    # 生成基础图表演示
    print("\n🎯 正在生成演示图表...")
    
    try:
        result_dir = os.path.join(project_root, "test", "result")
        os.makedirs(result_dir, exist_ok=True)
        
        # 基础CZSC图表
        chart = czsc.to_echarts(width="1400px", height="700px")
        chart_path = os.path.join(result_dir, "demo_basic_czsc.html")
        chart.render(chart_path)
        
        print(f"✅ 基础CZSC图表已生成: test/result/demo_basic_czsc.html")
        
        # 获取信号数据用于演示
        signals = manager.generate_all_signals(czsc)
        
        print(f"📊 当前数据包含:")
        print(f"   - FVG: {signals['summary']['fvg_count']}个")
        print(f"   - OB: {signals['summary']['ob_count']}个")
        print(f"   - 组合信号: {signals['summary']['composite_signal_count']}个")
        
        print(f"\n💡 提示: 运行以下命令查看完整的增强可视化:")
        print(f"   python test/test_enhanced_signal_visualization.py")
        
    except Exception as e:
        print(f"❌ 图表生成失败: {e}")


def demo_advanced_features():
    """演示高级功能"""
    print("\n" + "=" * 80)
    print("🚀 高级功能演示")
    print("=" * 80)
    
    print("🎯 高级组合信号规则:")
    
    for rule_name, rule in ADVANCED_SIGNAL_RULES.items():
        print(f"\n📋 {rule.name}")
        print(f"   📝 描述: {rule.description}")
        print(f"   📊 权重配置: {len(rule.weights)}个权重")
        print(f"   🎯 最低评分: {rule.min_score}")
        print(f"   🎲 最低置信度: {rule.min_confidence}")
        
        print(f"   💡 适用场景:")
        if 'HTF_POI' in rule.name:
            print(f"      - 高时框POI区域的反转确认")
            print(f"      - 适合中长期波段交易")
        elif 'Multi_Theory' in rule.name:
            print(f"      - 多理论汇聚的高概率区域")
            print(f"      - 缠论几何 + SMC机构分析融合")
        elif 'Scalping' in rule.name:
            print(f"      - 短期快速入场信号")
            print(f"      - 适合剥头皮交易策略")
        elif 'Swing' in rule.name:
            print(f"      - 波段交易确认信号")
            print(f"      - 适合中期趋势跟随")
    
    print(f"\n🔧 自定义配置示例:")
    print("```python")
    print("# 自定义增强信号管理器配置")
    print("custom_config = {")
    print("    'fvg_min_gap_size': 0.00005,  # FVG最小缺口")
    print("    'ob_min_move_strength': 0.002,  # OB最小移动强度")
    print("    'ob_require_fvg': False,  # 是否要求FVG确认")
    print("    'enable_signal_filtering': True,  # 启用信号过滤")
    print("    'fractal_config': {")
    print("        'min_strength_threshold': 0.4,  # 分型最小强度")
    print("        'position_weight': 1.0  # 位置权重")
    print("    },")
    print("    'scoring_config': {")
    print("        'min_composite_score': 50,  # 组合信号最低评分")
    print("        'min_composite_confidence': 0.4,  # 最低置信度")
    print("        'max_signals_per_timeframe': 5  # 每个时框最大信号数")
    print("    }")
    print("}")
    print()
    print("manager = EnhancedSignalManager(custom_config)")
    print("```")


def main():
    """主演示函数"""
    print("🎯 增强信号系统完整使用指南")
    print("基于缠论几何分析 + SMC/ICT机构足迹分析的融合交易信号系统")
    print()
    
    try:
        # 基础使用演示
        demo_basic_usage()
        
        # 不同市场环境配置演示
        demo_market_scenarios()
        
        # 信号解读演示
        demo_signal_interpretation()
        
        # 可视化集成演示
        demo_visualization_integration()
        
        # 高级功能演示
        demo_advanced_features()
        
        print("\n" + "=" * 80)
        print("🎉 增强信号系统演示完成！")
        print("=" * 80)
        
        print("\n📚 快速参考:")
        print("   📖 基础教程: demo_enhanced_signal_usage.py（本文件）")
        print("   🧪 完整测试: test/test_enhanced_signal_system.py")
        print("   📊 可视化测试: test/test_enhanced_signal_visualization.py")
        print("   📁 结果查看: test/result/ 目录")
        
        print("\n💡 下一步建议:")
        print("   1. 运行可视化测试，查看实际图表效果")
        print("   2. 根据自己的交易风格调整配置参数")
        print("   3. 在模拟环境中验证信号效果")
        print("   4. 逐步应用到实际交易中")
        
        print("\n⚠️  风险提示:")
        print("   - 任何技术分析都不能保证交易成功")
        print("   - 请在充分测试后再用于实际交易")
        print("   - 合理控制仓位和风险")
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()