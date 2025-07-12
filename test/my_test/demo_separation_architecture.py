# -*- coding: utf-8 -*-
"""
分离架构演示文件
author: Claude Code AI Assistant
create_dt: 2025-01-11
describe: 演示分型和Order Block的分离架构设计和多理论评分系统
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List

# 添加项目根目录到路径
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from czsc.objects import NewBar, FX
from czsc.objects_enhanced import (
    BasicFractal, BasicOrderBlock, 
    FractalAnalysis, OrderBlockAnalysis,
    FractalAnalyzer, OrderBlockAnalyzer,
    UnifiedOrderBlockDetector
)
from czsc.enum import Mark, Direction, Freq


class SeparationArchitectureDemo:
    """分离架构演示类"""
    
    def __init__(self):
        self.detector = UnifiedOrderBlockDetector()
        self.fractal_analyzer = FractalAnalyzer()
        self.ob_analyzer = OrderBlockAnalyzer()
    
    def create_realistic_market_data(self) -> List[NewBar]:
        """创建更真实的市场数据"""
        bars = []
        base_time = datetime(2024, 1, 15, 9, 30)  # 交易日早上
        
        # 模拟一个完整的市场形态：下跌 → 底分型 → 反弹 → FVG形成
        prices = [
            # 下跌阶段
            (50000, 50200, 49800, 49850),  # K1 下跌
            (49850, 50000, 49600, 49700),  # K2 继续下跌
            (49700, 49800, 49400, 49450),  # K3 底部区域
            
            # 底分型形成 (K4-K5-K6)
            (49450, 49600, 49200, 49300),  # K4 探底回升
            (49300, 49350, 49000, 49050),  # K5 再次探底（分型最低点）
            (49050, 49400, 49000, 49350),  # K6 反弹开始
            
            # 反弹阶段
            (49350, 49800, 49300, 49750),  # K7 强势反弹
            (49750, 50200, 49700, 50150),  # K8 持续上涨
            
            # FVG形成阶段 (K9-K10-K11)
            (50150, 50300, 50100, 50250),  # K9 (FVG第一根，潜在OB)
            (50250, 50400, 50200, 50350),  # K10 (FVG中间)
            (50350, 50800, 50600, 50750),  # K11 (跳空上涨，形成FVG)
            
            # 后续走势
            (50750, 51000, 50700, 50950),  # K12 继续上涨
            (50950, 51200, 50900, 51100),  # K13 冲高
            (51100, 51150, 50800, 50850),  # K14 回调测试OB
        ]
        
        for i, (open_price, high, low, close) in enumerate(prices):
            # 模拟真实的成交量模式
            if i in [4, 5, 6]:  # 分型区域成交量放大
                volume = 2000 + i * 200
            elif i in [9, 10, 11]:  # FVG区域成交量再次放大
                volume = 2500 + i * 150
            else:
                volume = 1000 + i * 100
            
            bar = NewBar(
                symbol="BTCUSDT",
                id=i + 1,
                dt=base_time + timedelta(minutes=i * 5),  # 5分钟K线
                freq=Freq.F5,
                open=open_price,
                close=close,
                high=high,
                low=low,
                vol=volume,
                amount=close * volume * 0.001,  # 模拟成交额
                elements=[],
                cache={}
            )
            bars.append(bar)
        
        return bars
    
    def create_bottom_fractal(self, bars: List[NewBar]) -> FX:
        """创建底分型（K4-K5-K6）"""
        fractal_bars = bars[3:6]  # K4, K5, K6
        
        fx = FX(
            symbol="BTCUSDT",
            dt=fractal_bars[1].dt,  # K5的时间
            mark=Mark.D,  # 底分型
            high=max(bar.high for bar in fractal_bars),
            low=min(bar.low for bar in fractal_bars),
            fx=fractal_bars[1].low,  # K5的最低点
            elements=fractal_bars
        )
        
        return fx
    
    def create_mock_czsc(self, bars: List[NewBar], fractals: List[FX]):
        """创建模拟的CZSC对象"""
        class MockCZSC:
            def __init__(self, bars, fractals):
                self.bars_ubi = bars
                self.fx_list = fractals
        
        return MockCZSC(bars, fractals)
    
    def create_comprehensive_market_context(self, bars: List[NewBar]) -> dict:
        """创建全面的市场上下文"""
        avg_volume = sum(bar.vol for bar in bars) / len(bars)
        atr = self._calculate_atr(bars)
        
        return {
            # 基础市场数据
            'avg_volume': avg_volume,
            'atr': atr,
            'current_price': bars[-1].close,
            
            # SMC相关上下文
            'at_key_level': True,  # 在关键技术位
            'at_daily_level': True,  # 在日线级别位置
            'major_liquidity_pool': True,  # 主要流动性池
            'high_market_attention': True,  # 高市场关注度
            'fibonacci_confluence': True,  # 斐波那契汇合
            'multi_tf_alignment': True,  # 多时间框架对齐
            'volume_confirmation': True,  # 成交量确认
            'wyckoff_confluence': False,  # Wyckoff汇合
            
            # ICT相关上下文
            'liquidity_sweep_detected': True,  # 检测到流动性扫荡
            'sweep_distance': atr * 0.8,  # 扫荡距离
            'reversion_speed': 3,  # 回撤速度（K线数）
            'breaks_structure': True,  # 突破结构
            'continues_trend': True,  # 延续趋势
            'reversal_potential': False,  # 反转潜力
            'high_price_efficiency': True,  # 高价格效率
            'precise_timing': True,  # 精确时机
            'algorithmic_execution': True,  # 算法执行特征
            
            # TradinghHub相关上下文
            'retest_history': 2,  # 重测历史次数
            'distance_factor': 0.4,  # 距离因子
            'favorable_market_condition': True,  # 有利市场条件
            'historical_reaction_strength': 0.75,  # 历史反应强度
            'strong_market_sentiment': True,  # 强市场情绪
            'technical_confluence': True,  # 技术汇合
            'clear_boundaries': True,  # 清晰边界
            'clear_invalidation': True,  # 清晰失效点
            'potential_reward': 2.5,  # 潜在收益
            'potential_risk': 1.0,  # 潜在风险
            
            # 分型分析上下文
            'structure_significance': True,  # 结构重要性
            'trend_alignment': True,  # 趋势一致性
            'market_phase': 'TRENDING',  # 市场阶段
            'clean_environment': True,  # 清洁环境
        }
    
    def _calculate_atr(self, bars: List[NewBar], period: int = 14) -> float:
        """计算ATR"""
        if len(bars) < period:
            return 100.0  # 默认值
        
        true_ranges = []
        for i in range(1, len(bars)):
            tr = max(
                bars[i].high - bars[i].low,
                abs(bars[i].high - bars[i-1].close),
                abs(bars[i].low - bars[i-1].close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / min(len(true_ranges), period)
    
    def demonstrate_separation_architecture(self):
        """演示分离架构的完整流程"""
        print("🎯 分离架构演示 - CZSC增强多理论融合系统")
        print("=" * 60)
        
        # 1. 创建市场数据
        print("\n📊 步骤1：创建真实市场数据")
        bars = self.create_realistic_market_data()
        print(f"✓ 创建了 {len(bars)} 根K线数据")
        print(f"✓ 时间范围: {bars[0].dt} 到 {bars[-1].dt}")
        print(f"✓ 价格范围: ${bars[0].open:,.0f} - ${max(bar.high for bar in bars):,.0f}")
        
        # 2. 基础组件识别（第一阶段）
        print("\n🔍 步骤2：基础组件识别（纯客观）")
        
        # 创建分型
        fx = self.create_bottom_fractal(bars)
        print(f"✓ 识别底分型: 时间={fx.dt}, 价格=${fx.fx:,.0f}")
        
        # 转换为BasicFractal
        basic_fractal = BasicFractal(
            symbol=fx.symbol,
            dt=fx.dt,
            mark=fx.mark,
            high=fx.high,
            low=fx.low,
            fx=fx.fx,
            elements=fx.elements
        )
        print(f"✓ 基础分型属性: 强度={basic_fractal.strength}, 成交量={basic_fractal.vol:,.0f}")
        
        # 检测Order Block
        czsc = self.create_mock_czsc(bars, [fx])
        basic_ob = self.detector.detect_order_block(fx, czsc)
        
        if basic_ob:
            ob_index = bars.index(basic_ob.ob_candle) + 1
            print(f"✓ 检测到Order Block: K{ob_index}, 价格=${basic_ob.ob_candle.close:,.0f}")
            print(f"  - 边界: ${basic_ob.lower_boundary:,.0f} - ${basic_ob.upper_boundary:,.0f}")
            print(f"  - 大小: ${basic_ob.size:,.0f}")
        else:
            print("❌ 未检测到Order Block")
            return
        
        # 3. 分析评分（第二阶段）
        print("\n📈 步骤3：分析评分（主观评估）")
        
        # 创建市场上下文
        market_context = self.create_comprehensive_market_context(bars)
        
        # 分型分析
        fractal_analysis = self.fractal_analyzer.analyze_fractal(basic_fractal, market_context)
        print(f"\n🔸 分型分析结果:")
        print(f"  - 等级: {fractal_analysis.level} 级 ({fractal_analysis.description})")
        print(f"  - 综合评分: {fractal_analysis.comprehensive_score:.2f}")
        print(f"  - 重要性: {fractal_analysis.importance_score:.2f}")
        print(f"  - 可靠性: {fractal_analysis.reliability_score:.2f}")
        print(f"  - 时间重要性: {fractal_analysis.time_significance:.2f}")
        print(f"  - 级别原因: {', '.join(fractal_analysis.level_reasons)}")
        
        # Order Block分析
        ob_analysis = self.ob_analyzer.analyze_order_block(basic_ob, market_context)
        print(f"\n🔸 Order Block分析结果:")
        print(f"  - 总体评级: {ob_analysis.overall_grade}")
        print(f"  - 综合评分: {ob_analysis.composite_score:.2f}")
        print(f"  - 交易适用性: {ob_analysis.trading_suitability}")
        print(f"  - 置信度: {ob_analysis.confidence_level:.2f}")
        
        # 4. 多理论评分详情
        print("\n🌟 步骤4：多理论评分详情")
        
        print(f"\n📊 SMC (Smart Money Concepts) 维度:")
        print(f"  - 机构强度: {ob_analysis.institutional_strength:.2f}")
        print(f"  - 智能钱足迹: {ob_analysis.smart_money_footprint:.2f}")
        print(f"  - 流动性重要性: {ob_analysis.liquidity_significance:.2f}")
        print(f"  - 汇合因素: {ob_analysis.confluence_score:.2f}")
        
        print(f"\n⏰ ICT (Inner Circle Trader) 维度:")
        print(f"  - 流动性扫荡质量: {ob_analysis.liquidity_sweep_quality:.2f}")
        print(f"  - Kill Zone对齐: {ob_analysis.kill_zone_alignment:.2f}")
        print(f"  - 市场结构作用: {ob_analysis.market_structure_role:.2f}")
        print(f"  - 算法交易概率: {ob_analysis.algorithm_probability:.2f}")
        
        print(f"\n💼 TradinghHub 实战维度:")
        print(f"  - 重测概率: {ob_analysis.retest_probability:.2f}")
        print(f"  - 反应强度: {ob_analysis.reaction_strength:.2f}")
        print(f"  - 入场精确度: {ob_analysis.entry_precision:.2f}")
        print(f"  - 风险收益比: {ob_analysis.risk_reward_ratio:.2f}")
        
        # 5. 交易建议
        print("\n💡 步骤5：交易建议")
        
        if ob_analysis.strength_factors:
            print(f"✅ 优势因素: {', '.join(ob_analysis.strength_factors)}")
        
        if ob_analysis.weakness_factors:
            print(f"⚠️  需注意因素: {', '.join(ob_analysis.weakness_factors)}")
        
        # 根据评分给出建议
        if ob_analysis.composite_score >= 0.7:
            print("🚀 交易建议: 高质量信号，建议重点关注")
        elif ob_analysis.composite_score >= 0.5:
            print("👍 交易建议: 中等质量信号，可考虑参与")
        else:
            print("🤔 交易建议: 质量一般，建议观望")
        
        # 6. 架构优势总结
        print("\n🏗️ 步骤6：分离架构优势")
        print("✓ 职责清晰: 基础识别与分析评分完全分离")
        print("✓ 客观可验证: 基础组件基于数学定义，可重现")
        print("✓ 灵活扩展: 分析维度可独立调整和优化")
        print("✓ 多理论融合: 有机整合SMC/ICT/TradinghHub理论")
        print("✓ 实战导向: 提供具体的交易评级和建议")
        
        return basic_fractal, fractal_analysis, basic_ob, ob_analysis
    
    def demonstrate_theory_integration(self):
        """演示多理论融合的深度"""
        print("\n\n🔬 深度理论融合演示")
        print("=" * 60)
        
        print("\n📚 理论映射关系:")
        
        print("\n🔹 SMC理论 → CZSC映射:")
        print("  • FVG (Fair Value Gap) → CZSC包含处理后K线缺口")
        print("  • Order Block → 分型关联的决定性K线区域")
        print("  • Structure Break → CZSC笔的突破确认")
        print("  • Liquidity Sweep → 分型点位的短暂突破回撤")
        
        print("\n🔹 ICT理论 → CZSC增强:")
        print("  • Kill Zones → 时间维度的分型和OB加权")
        print("  • Algorithm Price Delivery → 笔的效率分析")
        print("  • Manipulation → 流动性扫荡的模式识别")
        print("  • Market Structure → 基于笔序列的结构分析")
        
        print("\n🔹 TradinghHub → 实战应用:")
        print("  • Retest Analysis → OB区域的历史表现统计")
        print("  • Reaction Strength → 基于成交量的反应预期")
        print("  • Entry Precision → OB边界的清晰度评估")
        print("  • Risk/Reward → 基于ATR的风险收益计算")
        
        print("\n🔗 融合评分公式:")
        print("  综合评分 = SMC评分×0.35 + ICT评分×0.35 + 实战评分×0.30")
        print("  其中每个维度都包含4个子评分指标")
        
        print("\n⭐ 评级体系:")
        print("  • PREMIUM (0.85+): 顶级交易机会")
        print("  • EXCELLENT (0.70+): 优秀交易机会") 
        print("  • GOOD (0.55+): 良好交易机会")
        print("  • AVERAGE (0.40+): 平均交易机会")
        print("  • BASIC (0.40-): 基础交易机会")


def main():
    """主演示函数"""
    demo = SeparationArchitectureDemo()
    
    # 执行完整演示
    results = demo.demonstrate_separation_architecture()
    
    # 深度理论融合演示
    demo.demonstrate_theory_integration()
    
    print("\n" + "="*60)
    print("🎉 分离架构演示完成！")
    print("📄 详细文档请参考: docs/改动设计/20250711/分离架构重新设计方案.md")
    print("🔧 实现代码请参考: czsc/objects_enhanced.py")
    print("🧪 测试代码请参考: test/test_separation_architecture.py")


if __name__ == "__main__":
    main()