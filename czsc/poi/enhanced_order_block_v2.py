# -*- coding: utf-8 -*-
"""
增强Order Block v2 - 基于POI继承架构
author: Claude Code AI Assistant
create_dt: 2025-01-11
describe: 继承BasePOI的Order Block实现，具有统一的缓解分析机制
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from czsc.objects import NewBar, FX
from czsc.enum import Direction, Mark
from czsc.poi.base_poi import BasePOI
from czsc.poi.mitigation_framework import (
    OrderBlockMitigationAnalyzer, MitigationConfig, UniversalMitigationAnalyzer
)


class EnhancedOrderBlockV2(BasePOI):
    """增强Order Block v2 - 继承BasePOI的统一缓解机制"""
    
    def __init__(self, symbol: str, dt: datetime, high: float, low: float,
                 direction: Direction, poi_type: str, source_fractal: FX, poi_level: float,
                 ob_type: str = "", sub_type: str = "BASIC_OB",
                 liquidity_sweep_confirmed: bool = False, fvg_creation_confirmed: bool = False,
                 volume_spike_confirmed: bool = False,
                 strength_score: float = 0.0, reliability_score: float = 0.0,
                 smc_score: float = 0.0, ict_score: float = 0.0, tradinghub_score: float = 0.0,
                 **kwargs):
        # Order Block特有属性
        self.source_fractal = source_fractal
        self.poi_level = poi_level
        self.ob_type = ob_type
        self.sub_type = sub_type
        
        # 验证条件
        self.liquidity_sweep_confirmed = liquidity_sweep_confirmed
        self.fvg_creation_confirmed = fvg_creation_confirmed
        self.volume_spike_confirmed = volume_spike_confirmed
        
        # 评分系统
        self.strength_score = strength_score
        self.reliability_score = reliability_score
        self.smc_score = smc_score
        self.ict_score = ict_score
        self.tradinghub_score = tradinghub_score
        
        # 调用父类初始化
        super().__init__(symbol, dt, high, low, direction, poi_type, **kwargs)
    
    def __post_init__(self):
        """初始化后处理"""
        # 根据分型设置OB属性（如果未明确设置）
        if not self.ob_type:
            if self.source_fractal.mark == Mark.D:
                self.ob_type = "DEMAND_ZONE"
            else:
                self.ob_type = "SUPPLY_ZONE"
        
        # 调用父类初始化
        super().__post_init__()
    
    def _create_mitigation_analyzer(self) -> UniversalMitigationAnalyzer:
        """创建Order Block专用的缓解分析器"""
        return OrderBlockMitigationAnalyzer(self.mitigation_config)
    
    # ============ Order Block特有方法 ============
    
    def is_demand_zone(self) -> bool:
        """判断是否为需求区域（看涨OB）"""
        return self.ob_type == "DEMAND_ZONE"
    
    def is_supply_zone(self) -> bool:
        """判断是否为供应区域（看跌OB）"""
        return self.ob_type == "SUPPLY_ZONE"
    
    def get_fractal_strength(self) -> int:
        """获取分型强度"""
        return len(self.source_fractal.elements) if self.source_fractal.elements else 0
    
    def calculate_comprehensive_score(self) -> float:
        """计算综合评分"""
        # 基础评分权重
        base_weight = 0.3
        strength_weight = 0.25
        reliability_weight = 0.25
        theory_weight = 0.2
        
        # 理论评分（SMC + ICT + TradinghHub）
        theory_score = (self.smc_score + self.ict_score + self.tradinghub_score) / 3.0
        
        # 综合评分
        total_score = (
            base_weight * (1.0 if self.is_valid else 0.0) +
            strength_weight * self.strength_score +
            reliability_weight * self.reliability_score +
            theory_weight * theory_score
        )
        
        return min(1.0, total_score)
    
    # ============ SMC/ICT/TradinghHub评分方法 ============
    
    def calculate_smc_score(self, market_structure_context: Dict[str, Any] = None) -> float:
        """计算SMC（Smart Money Concepts）评分"""
        score = 0.0
        
        # 流动性扫荡确认 (40%)
        if self.liquidity_sweep_confirmed:
            score += 0.4
        
        # 订单流失衡 (30%)
        if self.volume_spike_confirmed:
            score += 0.3
        
        # 市场结构变化 (30%)
        if market_structure_context:
            # 检查是否在关键结构位置
            if market_structure_context.get('at_structure_break', False):
                score += 0.3
            elif market_structure_context.get('near_key_level', False):
                score += 0.15
        
        self.smc_score = score
        return score
    
    def calculate_ict_score(self, session_context: Dict[str, Any] = None) -> float:
        """计算ICT（Inner Circle Trader）评分"""
        score = 0.0
        
        # Kill Zone确认 (35%)
        if session_context and session_context.get('in_kill_zone', False):
            score += 0.35
        
        # FVG创建确认 (35%) - ICT重视FVG
        if self.fvg_creation_confirmed:
            score += 0.35
        
        # 算法价格交付 (30%)
        if self.liquidity_sweep_confirmed and self.volume_spike_confirmed:
            score += 0.3
        
        self.ict_score = score
        return score
    
    def calculate_tradinghub_score(self, risk_reward_context: Dict[str, Any] = None) -> float:
        """计算TradinghHub评分"""
        score = 0.0
        
        # 重测概率评估 (40%)
        if not self.is_tested:
            score += 0.4  # 未测试的OB具有更高价值
        elif self.mitigation_level < 0.3:
            score += 0.2  # 轻度测试仍有价值
        
        # 风险回报比 (30%)
        if risk_reward_context:
            rr_ratio = risk_reward_context.get('risk_reward_ratio', 0)
            if rr_ratio >= 3.0:
                score += 0.3
            elif rr_ratio >= 2.0:
                score += 0.2
            elif rr_ratio >= 1.5:
                score += 0.1
        
        # 确认条件 (30%)
        confirmation_count = sum([
            self.liquidity_sweep_confirmed,
            self.fvg_creation_confirmed,
            self.volume_spike_confirmed
        ])
        score += (confirmation_count / 3.0) * 0.3
        
        self.tradinghub_score = score
        return score
    
    def update_all_scores(self, market_context: Dict[str, Any] = None):
        """更新所有评分"""
        market_context = market_context or {}
        
        self.calculate_smc_score(market_context.get('smc_context'))
        self.calculate_ict_score(market_context.get('ict_context'))
        self.calculate_tradinghub_score(market_context.get('tradinghub_context'))
    
    # ============ 重写序列化方法添加OB特有信息 ============
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        
        # 添加Order Block特有信息
        ob_specific = {
            'ob_type': self.ob_type,
            'sub_type': self.sub_type,
            'poi_level': self.poi_level,
            'fractal_strength': self.get_fractal_strength(),
            
            # 验证条件
            'liquidity_sweep_confirmed': self.liquidity_sweep_confirmed,
            'fvg_creation_confirmed': self.fvg_creation_confirmed,
            'volume_spike_confirmed': self.volume_spike_confirmed,
            
            # 评分
            'strength_score': self.strength_score,
            'reliability_score': self.reliability_score,
            'smc_score': self.smc_score,
            'ict_score': self.ict_score,
            'tradinghub_score': self.tradinghub_score,
            'comprehensive_score': self.calculate_comprehensive_score(),
            
            # 分型信息
            'source_fractal_type': self.source_fractal.mark.value,
            'source_fractal_dt': self.source_fractal.dt.isoformat(),
            'source_fractal_price': self.source_fractal.fx
        }
        
        base_dict.update(ob_specific)
        return base_dict
    
    def __repr__(self):
        return (f"EnhancedOrderBlockV2(symbol={self.symbol}, type={self.ob_type}, "
                f"size={self.size:.2f}, mitigation={self.mitigation_level:.1%}, "
                f"comprehensive_score={self.calculate_comprehensive_score():.1%})")


# ============ 工厂函数 ============

def create_enhanced_ob_v2_from_fractal(fractal: FX, 
                                      ob_bars: List[NewBar] = None,
                                      mitigation_config: MitigationConfig = None) -> EnhancedOrderBlockV2:
    """从分型创建增强Order Block v2"""
    
    # 确定OB边界
    if fractal.elements:
        high = max(bar.high for bar in fractal.elements)
        low = min(bar.low for bar in fractal.elements)
    else:
        # 使用分型的高低点作为边界
        high = fractal.high if hasattr(fractal, 'high') else fractal.fx
        low = fractal.low if hasattr(fractal, 'low') else fractal.fx
    
    enhanced_ob = EnhancedOrderBlockV2(
        symbol=fractal.symbol,
        dt=fractal.dt,
        high=high,
        low=low,
        direction=Direction.Up if fractal.mark == Mark.D else Direction.Down,
        poi_type="ORDER_BLOCK",
        source_fractal=fractal,
        poi_level=fractal.fx,
        mitigation_config=mitigation_config or MitigationConfig()
    )
    
    # 如果提供了后续K线数据，进行批量缓解分析
    if ob_bars:
        enhanced_ob.batch_update_mitigation(ob_bars)
    
    return enhanced_ob


def create_enhanced_ob_v2_from_basic_ob(basic_ob,
                                       mitigation_config: MitigationConfig = None) -> EnhancedOrderBlockV2:
    """从基础Order Block创建增强版本v2"""
    
    enhanced_ob = EnhancedOrderBlockV2(
        symbol=getattr(basic_ob, 'symbol', 'UNKNOWN'),
        dt=getattr(basic_ob, 'dt', datetime.now()),
        high=getattr(basic_ob, 'high', 0.0),
        low=getattr(basic_ob, 'low', 0.0),
        direction=Direction.Up if getattr(basic_ob, 'ob_type', '') == 'DEMAND_ZONE' else Direction.Down,
        poi_type="ORDER_BLOCK",
        source_fractal=getattr(basic_ob, 'source_fractal', None),
        poi_level=getattr(basic_ob, 'poi_level', 0.0),
        mitigation_config=mitigation_config or MitigationConfig()
    )
    
    # 继承已有的验证条件
    if hasattr(basic_ob, 'liquidity_sweep_confirmed'):
        enhanced_ob.liquidity_sweep_confirmed = basic_ob.liquidity_sweep_confirmed
    if hasattr(basic_ob, 'fvg_creation_confirmed'):
        enhanced_ob.fvg_creation_confirmed = basic_ob.fvg_creation_confirmed
    if hasattr(basic_ob, 'volume_spike_confirmed'):
        enhanced_ob.volume_spike_confirmed = basic_ob.volume_spike_confirmed
    
    # 继承评分信息
    if hasattr(basic_ob, 'strength_score'):
        enhanced_ob.strength_score = basic_ob.strength_score
    if hasattr(basic_ob, 'reliability_score'):
        enhanced_ob.reliability_score = basic_ob.reliability_score
    
    return enhanced_ob