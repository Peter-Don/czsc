# -*- coding: utf-8 -*-
"""
通用缓解分析框架
author: Claude Code AI Assistant  
create_dt: 2025-01-11
describe: 为FVG和Order Block提供统一的缓解分析机制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from czsc.objects import NewBar
from czsc.enum import Direction


class MitigationType(Enum):
    """缓解类型"""
    NONE = "NONE"                # 无缓解 (<25%)
    PARTIAL = "PARTIAL"          # 部分缓解 (25-50%)  
    SIGNIFICANT = "SIGNIFICANT"  # 显著缓解 (50-90%)
    COMPLETE = "COMPLETE"        # 完全缓解 (90-150%)
    OVERSHOOT = "OVERSHOOT"      # 超调缓解 (≥150%)


class MitigationMethod(Enum):
    """缓解判断方法"""
    WICK = "WICK"        # 影线触及即缓解
    CLOSE = "CLOSE"      # 收盘价进入才缓解
    BODY = "BODY"        # 实体进入才缓解
    MIDPOINT = "MIDPOINT"  # 中点进入才缓解


@dataclass
class MitigationEvent:
    """缓解事件记录"""
    timestamp: datetime
    price: float
    mitigation_level: float
    event_type: str  # 'first_test', 'partial_mitigated', 'fully_mitigated', 'overshoot'
    bar_data: NewBar
    method_used: MitigationMethod


@dataclass
class ZoneDefinition:
    """区域定义"""
    high: float
    low: float
    direction: Direction  # 区域的方向性
    zone_type: str       # "FVG", "ORDER_BLOCK", "CUSTOM"
    
    @property
    def size(self) -> float:
        """区域大小"""
        return abs(self.high - self.low)
    
    @property
    def midpoint(self) -> float:
        """区域中点"""
        return (self.high + self.low) / 2.0


@dataclass
class MitigationConfig:
    """缓解配置"""
    method: MitigationMethod = MitigationMethod.CLOSE
    mitigation_threshold: float = 0.5  # 缓解阈值 (50%)
    invalidation_threshold: float = 1.0  # 失效阈值 (100%)
    
    # 缓解类型阈值
    partial_threshold: float = 0.25      # 25%
    significant_threshold: float = 0.50  # 50% 
    complete_threshold: float = 0.90     # 90%
    overshoot_threshold: float = 1.50    # 150%
    
    # 交易有效性阈值
    trading_effectiveness_threshold: float = 0.70  # 70%


@dataclass 
class MitigationAnalysis:
    """通用缓解分析结果"""
    
    # 基础状态
    current_level: float = 0.0           # 当前缓解程度 0.0-N.0 (支持超调)
    max_mitigation_level: float = 0.0    # 历史最大缓解程度
    mitigation_type: MitigationType = MitigationType.NONE
    
    # 状态标记
    is_tested: bool = False
    is_mitigated: bool = False
    is_valid: bool = True
    is_effective_for_trading: bool = True
    
    # 历史记录
    interaction_history: List[MitigationEvent] = field(default_factory=list)
    
    # 统计信息
    test_count: int = 0
    first_test_time: Optional[datetime] = None
    full_mitigation_time: Optional[datetime] = None
    last_interaction_time: Optional[datetime] = None
    
    # 配置
    config: MitigationConfig = field(default_factory=MitigationConfig)
    
    def get_mitigation_description(self) -> str:
        """获取缓解描述"""
        descriptions = {
            MitigationType.NONE: f"无缓解 ({self.current_level:.1%})",
            MitigationType.PARTIAL: f"部分缓解 ({self.current_level:.1%})",
            MitigationType.SIGNIFICANT: f"显著缓解 ({self.current_level:.1%})",
            MitigationType.COMPLETE: f"完全缓解 ({self.current_level:.1%})",
            MitigationType.OVERSHOOT: f"超调缓解 ({self.current_level:.1%})"
        }
        return descriptions.get(self.mitigation_type, f"未知状态 ({self.current_level:.1%})")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "mitigation_level": self.current_level,
            "mitigation_type": self.mitigation_type.value,
            "description": self.get_mitigation_description(),
            "is_tested": self.is_tested,
            "is_mitigated": self.is_mitigated,
            "is_valid": self.is_valid,
            "is_effective": self.is_effective_for_trading,
            "test_count": self.test_count,
            "interaction_count": len(self.interaction_history)
        }


class UniversalMitigationAnalyzer:
    """通用缓解分析器"""
    
    def __init__(self, config: MitigationConfig = None):
        self.config = config or MitigationConfig()
    
    def analyze_zone_mitigation(self, zone: ZoneDefinition, bars: List[NewBar], 
                               existing_analysis: MitigationAnalysis = None) -> MitigationAnalysis:
        """分析区域缓解"""
        
        if existing_analysis:
            analysis = existing_analysis
        else:
            analysis = MitigationAnalysis(config=self.config)
        
        for bar in bars:
            self._update_analysis_with_bar(analysis, zone, bar)
        
        return analysis
    
    def update_single_bar(self, analysis: MitigationAnalysis, zone: ZoneDefinition, 
                         bar: NewBar) -> bool:
        """用单根K线更新缓解分析"""
        return self._update_analysis_with_bar(analysis, zone, bar)
    
    def _update_analysis_with_bar(self, analysis: MitigationAnalysis, 
                                 zone: ZoneDefinition, bar: NewBar) -> bool:
        """用K线数据更新分析"""
        
        # 检查是否与区域有交互
        interaction_price = self._check_zone_interaction(bar, zone, self.config.method)
        if interaction_price is None:
            return False
        
        # 计算缓解程度
        mitigation_level = self._calculate_mitigation_level(interaction_price, zone)
        
        # 更新分析状态
        updated = False
        if mitigation_level > analysis.current_level:
            analysis.current_level = mitigation_level
            analysis.max_mitigation_level = max(analysis.max_mitigation_level, mitigation_level)
            updated = True
            
            # 记录交互事件
            event = self._create_mitigation_event(bar, interaction_price, mitigation_level, analysis)
            analysis.interaction_history.append(event)
            analysis.last_interaction_time = bar.dt
            
            # 更新状态
            if not analysis.is_tested:
                analysis.is_tested = True
                analysis.first_test_time = bar.dt
                analysis.test_count = 1
            else:
                analysis.test_count += 1
            
            # 检查缓解状态
            self._update_mitigation_status(analysis, mitigation_level)
        
        return updated
    
    def _check_zone_interaction(self, bar: NewBar, zone: ZoneDefinition, 
                               method: MitigationMethod) -> Optional[float]:
        """检查K线是否与区域有交互"""
        
        if method == MitigationMethod.WICK:
            # 影线触及即算交互
            if bar.low <= zone.high and bar.high >= zone.low:
                if zone.direction == Direction.Up:
                    return min(bar.low, zone.high)  # 从上方进入
                else:
                    return max(bar.high, zone.low)  # 从下方进入
        
        elif method == MitigationMethod.CLOSE:
            # 收盘价进入才算交互
            if zone.low <= bar.close <= zone.high:
                return bar.close
        
        elif method == MitigationMethod.BODY:
            # 实体进入才算交互
            body_top = max(bar.open, bar.close)
            body_bottom = min(bar.open, bar.close)
            if not (body_top < zone.low or body_bottom > zone.high):
                return bar.close
        
        elif method == MitigationMethod.MIDPOINT:
            # 价格触及中点才算交互
            if bar.low <= zone.midpoint <= bar.high:
                return zone.midpoint
        
        return None
    
    def _calculate_mitigation_level(self, price: float, zone: ZoneDefinition) -> float:
        """计算缓解程度"""
        
        if zone.size == 0:
            return 0.0
        
        if zone.direction == Direction.Up:
            # 看涨区域：价格从上方进入
            if price >= zone.high:
                return 0.0  # 未进入
            elif price >= zone.low:
                return (zone.high - price) / zone.size  # 正常缓解
            else:
                return 1.0 + (zone.low - price) / zone.size  # 超调缓解
        
        else:
            # 看跌区域：价格从下方进入
            if price <= zone.low:
                return 0.0  # 未进入
            elif price <= zone.high:
                return (price - zone.low) / zone.size  # 正常缓解
            else:
                return 1.0 + (price - zone.high) / zone.size  # 超调缓解
    
    def _create_mitigation_event(self, bar: NewBar, price: float, mitigation_level: float,
                                analysis: MitigationAnalysis) -> MitigationEvent:
        """创建缓解事件"""
        
        # 确定事件类型
        if not analysis.is_tested:
            event_type = "first_test"
        elif mitigation_level >= self.config.overshoot_threshold:
            event_type = "overshoot"
        elif mitigation_level >= self.config.complete_threshold:
            event_type = "fully_mitigated"
        elif mitigation_level >= self.config.partial_threshold:
            event_type = "partial_mitigated"
        else:
            event_type = "minor_test"
        
        return MitigationEvent(
            timestamp=bar.dt,
            price=price,
            mitigation_level=mitigation_level,
            event_type=event_type,
            bar_data=bar,
            method_used=self.config.method
        )
    
    def _update_mitigation_status(self, analysis: MitigationAnalysis, mitigation_level: float):
        """更新缓解状态"""
        
        # 更新缓解类型
        if mitigation_level >= self.config.overshoot_threshold:
            analysis.mitigation_type = MitigationType.OVERSHOOT
        elif mitigation_level >= self.config.complete_threshold:
            analysis.mitigation_type = MitigationType.COMPLETE
        elif mitigation_level >= self.config.significant_threshold:
            analysis.mitigation_type = MitigationType.SIGNIFICANT
        elif mitigation_level >= self.config.partial_threshold:
            analysis.mitigation_type = MitigationType.PARTIAL
        else:
            analysis.mitigation_type = MitigationType.NONE
        
        # 更新是否缓解
        if mitigation_level >= self.config.mitigation_threshold and not analysis.is_mitigated:
            analysis.is_mitigated = True
            analysis.full_mitigation_time = analysis.last_interaction_time
        
        # 更新是否失效
        if mitigation_level >= self.config.invalidation_threshold:
            analysis.is_valid = False
        
        # 更新交易有效性
        analysis.is_effective_for_trading = mitigation_level < self.config.trading_effectiveness_threshold


class FVGMitigationAnalyzer(UniversalMitigationAnalyzer):
    """FVG专用缓解分析器"""
    
    def __init__(self, config: MitigationConfig = None):
        if config is None:
            config = MitigationConfig(
                method=MitigationMethod.CLOSE,
                mitigation_threshold=0.5,
                trading_effectiveness_threshold=0.7
            )
        super().__init__(config)
    
    def analyze_fvg_mitigation(self, fvg_high: float, fvg_low: float, 
                              direction: Direction, bars: List[NewBar]) -> MitigationAnalysis:
        """分析FVG缓解"""
        
        zone = ZoneDefinition(
            high=fvg_high,
            low=fvg_low,
            direction=direction,
            zone_type="FVG"
        )
        
        return self.analyze_zone_mitigation(zone, bars)


class OrderBlockMitigationAnalyzer(UniversalMitigationAnalyzer):
    """Order Block专用缓解分析器"""
    
    def __init__(self, config: MitigationConfig = None):
        if config is None:
            config = MitigationConfig(
                method=MitigationMethod.CLOSE,
                mitigation_threshold=0.7,  # OB通常使用更高的阈值
                trading_effectiveness_threshold=0.7,
                complete_threshold=0.85    # OB的完全缓解阈值更高
            )
        super().__init__(config)
    
    def analyze_order_block_mitigation(self, ob_high: float, ob_low: float,
                                     direction: Direction, bars: List[NewBar]) -> MitigationAnalysis:
        """分析Order Block缓解"""
        
        zone = ZoneDefinition(
            high=ob_high,
            low=ob_low,
            direction=direction,
            zone_type="ORDER_BLOCK"
        )
        
        analysis = self.analyze_zone_mitigation(zone, bars)
        
        # OB特有的增强分析
        analysis = self._enhance_ob_analysis(analysis, zone, bars)
        
        return analysis
    
    def _enhance_ob_analysis(self, analysis: MitigationAnalysis, zone: ZoneDefinition, 
                           bars: List[NewBar]) -> MitigationAnalysis:
        """增强OB分析"""
        
        # 可以添加OB特有的分析逻辑：
        # 1. 机构订单消耗分析
        # 2. 流动性扫荡确认  
        # 3. 成交量异常检测
        # 4. 反应强度分析
        
        return analysis


# 工具函数
def create_mitigation_analyzer(zone_type: str, config: MitigationConfig = None) -> UniversalMitigationAnalyzer:
    """创建缓解分析器工厂函数"""
    
    if zone_type.upper() == "FVG":
        return FVGMitigationAnalyzer(config)
    elif zone_type.upper() == "ORDER_BLOCK":
        return OrderBlockMitigationAnalyzer(config)
    else:
        return UniversalMitigationAnalyzer(config)


def get_default_mitigation_config(zone_type: str) -> MitigationConfig:
    """获取默认缓解配置"""
    
    if zone_type.upper() == "FVG":
        return MitigationConfig(
            method=MitigationMethod.CLOSE,
            mitigation_threshold=0.5,
            trading_effectiveness_threshold=0.7
        )
    elif zone_type.upper() == "ORDER_BLOCK":
        return MitigationConfig(
            method=MitigationMethod.CLOSE,
            mitigation_threshold=0.7,
            trading_effectiveness_threshold=0.7,
            complete_threshold=0.85
        )
    else:
        return MitigationConfig()