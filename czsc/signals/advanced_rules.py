# -*- coding: utf-8 -*-
"""
高级组合信号规则 - 融合缠论与SMC/ICT理论的复合策略

实现文档中提到的高概率反转信号规则：
- HTF_POI_Reversal_Confirmation: 高时框POI区域的反转确认
- Multi_Theory_Confluence: 多理论汇聚信号
"""

from czsc.signals.base import (
    CompositeSignalRule, SignalWeight, SignalNecessity
)


def create_htf_poi_reversal_rule() -> CompositeSignalRule:
    """
    创建HTF POI反转确认规则
    
    规则逻辑：
    1. 必要条件：当前价格在HTF的高质量POI区域（OB或FVG）
    2. 必要条件：LTF出现分型
    3. 评分项：分型力度、行为确认、位置确认
    """
    return CompositeSignalRule(
        name="HTF_POI_Reversal_Confirmation",
        description="高时框POI区域的多重确认反转信号",
        required_signals=[],  # 不强制要求，通过权重控制
        optional_signals=["power", "position", "behavior", "quality"],
        weights=[
            # 分型力度信号（30%权重）
            SignalWeight("power", 0.30, SignalNecessity.PREFERRED, {
                "strong_fractal": 1.3,        # 强分型权重提升
                "multiple_fractals": 1.2      # 多分型汇聚提升
            }),
            
            # 分型行为信号（40%权重）- 关键确认项
            SignalWeight("behavior", 0.40, SignalNecessity.CRITICAL, {
                "liquidity_sweep": 1.5,       # 流动性扫除大幅提升
                "institutional_pattern": 1.3   # 机构模式确认
            }),
            
            # 位置信号（20%权重）
            SignalWeight("position", 0.20, SignalNecessity.PREFERRED, {
                "htf_poi": 1.4,               # HTF POI区域权重提升
                "key_level": 1.3,             # 关键位置提升
                "confluence_zone": 1.2        # 汇聚区域提升
            }),
            
            # 机构足迹质量信号（10%权重）
            SignalWeight("quality", 0.10, SignalNecessity.OPTIONAL, {
                "high_quality_ob": 1.3,       # 高质量OB提升
                "fresh_fvg": 1.2              # 新鲜FVG提升
            })
        ],
        min_score=200,                         # 高门槛评分
        min_confidence=0.7                     # 高置信度要求
    )


def create_multi_theory_confluence_rule() -> CompositeSignalRule:
    """
    创建多理论汇聚规则
    
    融合缠论几何分析与SMC机构分析的综合信号
    """
    return CompositeSignalRule(
        name="Multi_Theory_Confluence",
        description="缠论几何与SMC机构分析的多理论汇聚信号",
        required_signals=[],
        optional_signals=["power", "position", "behavior", "timing", "quality"],
        weights=[
            # 缠论几何强度（35%权重）
            SignalWeight("power", 0.35, SignalNecessity.REQUIRED, {
                "geometric_confluence": 1.4,   # 几何汇聚提升
                "strong_structure": 1.2       # 强结构提升
            }),
            
            # 机构行为确认（30%权重）
            SignalWeight("behavior", 0.30, SignalNecessity.PREFERRED, {
                "sweep_and_reverse": 1.5,     # 扫除后反转
                "institutional_footprint": 1.3 # 机构足迹确认
            }),
            
            # 关键位置确认（25%权重）
            SignalWeight("position", 0.25, SignalNecessity.PREFERRED, {
                "multi_timeframe_poi": 1.4,   # 多时框POI
                "high_probability_zone": 1.3  # 高概率区域
            }),
            
            # 时间窗口（5%权重）
            SignalWeight("timing", 0.05, SignalNecessity.OPTIONAL, {
                "optimal_timing": 1.2         # 最佳时间窗口
            }),
            
            # 机构足迹质量（5%权重）
            SignalWeight("quality", 0.05, SignalNecessity.OPTIONAL, {
                "premium_quality": 1.3        # 顶级质量
            })
        ],
        min_score=180,
        min_confidence=0.65
    )


def create_scalping_entry_rule() -> CompositeSignalRule:
    """
    创建剥头皮入场规则
    
    适用于短期交易的快速确认信号
    """
    return CompositeSignalRule(
        name="Scalping_Entry_Signal",
        description="基于快速确认的剥头皮入场信号",
        required_signals=[],
        optional_signals=["power", "behavior", "timing"],
        weights=[
            # 行为确认（50%权重）- 主要依据
            SignalWeight("behavior", 0.50, SignalNecessity.CRITICAL, {
                "quick_reversal": 1.4,        # 快速反转
                "momentum_shift": 1.3         # 动量转换
            }),
            
            # 分型力度（30%权重）
            SignalWeight("power", 0.30, SignalNecessity.PREFERRED, {
                "immediate_power": 1.3,       # 即时力度
                "clear_structure": 1.2        # 清晰结构
            }),
            
            # 时间确认（20%权重）
            SignalWeight("timing", 0.20, SignalNecessity.OPTIONAL, {
                "market_session": 1.2,        # 活跃时段
                "news_window": 0.8            # 新闻窗口期降权
            })
        ],
        min_score=100,                         # 较低门槛，适合快速决策
        min_confidence=0.6
    )


def create_swing_trading_rule() -> CompositeSignalRule:
    """
    创建波段交易规则
    
    适用于中期持仓的波段交易信号
    """
    return CompositeSignalRule(
        name="Swing_Trading_Signal",
        description="基于中期结构确认的波段交易信号",
        required_signals=["power", "position"],  # 必须有力度和位置确认
        optional_signals=["behavior", "quality", "timing"],
        weights=[
            # 位置确认（40%权重）- 波段交易的关键
            SignalWeight("position", 0.40, SignalNecessity.CRITICAL, {
                "major_structure": 1.5,       # 主要结构位置
                "trend_continuation": 1.3,     # 趋势延续位置
                "support_resistance": 1.2     # 支撑阻力位置
            }),
            
            # 结构力度（30%权重）
            SignalWeight("power", 0.30, SignalNecessity.REQUIRED, {
                "structural_break": 1.4,      # 结构性突破
                "volume_confirmation": 1.3,    # 成交量确认
                "momentum_alignment": 1.2     # 动量对齐
            }),
            
            # 机构足迹（20%权重）
            SignalWeight("quality", 0.20, SignalNecessity.PREFERRED, {
                "institutional_interest": 1.3, # 机构兴趣
                "liquidity_zones": 1.2        # 流动性区域
            }),
            
            # 行为确认（10%权重）
            SignalWeight("behavior", 0.10, SignalNecessity.OPTIONAL, {
                "sustained_move": 1.2         # 持续性走势
            })
        ],
        min_score=250,                         # 高门槛，确保质量
        min_confidence=0.75
    )


# 规则库
ADVANCED_SIGNAL_RULES = {
    'htf_poi_reversal': create_htf_poi_reversal_rule(),
    'multi_theory_confluence': create_multi_theory_confluence_rule(),
    'scalping_entry': create_scalping_entry_rule(),
    'swing_trading': create_swing_trading_rule()
}


def get_rule_by_name(rule_name: str) -> CompositeSignalRule:
    """根据名称获取规则"""
    return ADVANCED_SIGNAL_RULES.get(rule_name)


def get_all_advanced_rules() -> list:
    """获取所有高级规则"""
    return list(ADVANCED_SIGNAL_RULES.values())