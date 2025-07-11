# -*- coding: utf-8 -*-
"""
增强FVG - 基于POI继承架构
author: Claude Code AI Assistant
create_dt: 2025-01-11
describe: 继承BasePOI的FVG实现，具有统一的缓解分析机制
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from czsc.objects import NewBar
from czsc.enum import Direction
from czsc.poi.base_poi import BasePOI
from czsc.poi.mitigation_framework import (
    FVGMitigationAnalyzer, MitigationConfig, UniversalMitigationAnalyzer
)


class EnhancedFVG(BasePOI):
    """增强FVG - 继承BasePOI的统一缓解机制"""
    
    def __init__(self, symbol: str, dt: datetime, high: float, low: float,
                 direction: Direction, poi_type: str, bar1: NewBar, bar2: NewBar, bar3: NewBar,
                 strength: float = 0.0, relative_size: float = 0.0, score: float = 0.0,
                 **kwargs):
        # FVG特有属性
        self.bar1 = bar1
        self.bar2 = bar2
        self.bar3 = bar3
        self.strength = strength
        self.relative_size = relative_size
        self.score = score
        
        # 调用父类初始化
        super().__init__(symbol, dt, high, low, direction, poi_type, **kwargs)
    
    def __post_init__(self):
        """初始化后处理"""
        # 计算FVG特有的属性
        self._calculate_fvg_properties()
        
        # 调用父类初始化
        super().__post_init__()
    
    def _create_mitigation_analyzer(self) -> UniversalMitigationAnalyzer:
        """创建FVG专用的缓解分析器"""
        return FVGMitigationAnalyzer(self.mitigation_config)
    
    def _calculate_fvg_properties(self):
        """计算FVG特有属性"""
        # 计算强度
        body_size = abs(self.bar2.close - self.bar2.open)
        bar_range = self.bar2.high - self.bar2.low
        
        if bar_range == 0:
            self.strength = 0.0
            self.relative_size = 0.0
        else:
            body_ratio = body_size / bar_range
            volume_factor = self.bar2.vol / max(self.bar1.vol, self.bar3.vol, 1)
            self.strength = body_ratio * volume_factor
            self.relative_size = self.size / bar_range
    
    # ============ FVG特有方法 ============
    
    def is_bullish_fvg(self) -> bool:
        """判断是否为看涨FVG"""
        return self.direction == Direction.Up
    
    def is_bearish_fvg(self) -> bool:
        """判断是否为看跌FVG"""
        return self.direction == Direction.Down
    
    # ============ 重写序列化方法添加FVG特有信息 ============
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        
        # 添加FVG特有信息
        fvg_specific = {
            'strength': self.strength,
            'relative_size': self.relative_size,
            'score': self.score,
            'bar1_dt': self.bar1.dt.isoformat(),
            'bar2_dt': self.bar2.dt.isoformat(),
            'bar3_dt': self.bar3.dt.isoformat(),
        }
        
        base_dict.update(fvg_specific)
        return base_dict
    
    def __repr__(self):
        direction_str = "Bullish" if self.direction == Direction.Up else "Bearish"
        status = "Mitigated" if self.is_mitigated else f"Active({self.mitigation_level:.1%})"
        return f"EnhancedFVG({direction_str}, {self.symbol}, {self.dt.strftime('%Y-%m-%d %H:%M')}, " \
               f"[{self.low:.4f}, {self.high:.4f}], {status})"


# ============ 工厂函数 ============

def create_enhanced_fvg_from_bars(bar1: NewBar, bar2: NewBar, bar3: NewBar,
                                 mitigation_config: MitigationConfig = None) -> Optional[EnhancedFVG]:
    """从三根K线创建增强FVG"""
    
    # 检查是否形成FVG
    if bar1.high < bar3.low:
        # 看涨FVG
        direction = Direction.Up
        high = bar3.low
        low = bar1.high
    elif bar1.low > bar3.high:
        # 看跌FVG
        direction = Direction.Down
        high = bar1.low
        low = bar3.high
    else:
        # 不形成FVG
        return None
    
    return EnhancedFVG(
        symbol=bar1.symbol,
        dt=bar2.dt,
        high=high,
        low=low,
        direction=direction,
        poi_type="FVG",
        bar1=bar1,
        bar2=bar2,
        bar3=bar3,
        mitigation_config=mitigation_config or MitigationConfig()
    )


def create_enhanced_fvg_from_basic_fvg(basic_fvg, 
                                      mitigation_config: MitigationConfig = None) -> EnhancedFVG:
    """从基础FVG创建增强版本"""
    
    enhanced_fvg = EnhancedFVG(
        symbol=basic_fvg.symbol,
        dt=basic_fvg.dt,
        high=basic_fvg.high,
        low=basic_fvg.low,
        direction=basic_fvg.direction,
        poi_type="FVG",
        bar1=basic_fvg.bar1,
        bar2=basic_fvg.bar2,
        bar3=basic_fvg.bar3,
        mitigation_config=mitigation_config or MitigationConfig()
    )
    
    # 继承已有的缓解状态
    if hasattr(basic_fvg, 'mitigation_level'):
        enhanced_fvg._mitigation_analysis.current_level = basic_fvg.mitigation_level
        enhanced_fvg._mitigation_analysis.is_tested = getattr(basic_fvg, 'is_tested', False)
        enhanced_fvg._mitigation_analysis.is_mitigated = getattr(basic_fvg, 'is_mitigated', False)
        enhanced_fvg.is_tested = enhanced_fvg._mitigation_analysis.is_tested
        enhanced_fvg.is_mitigated = enhanced_fvg._mitigation_analysis.is_mitigated
    
    # 继承评分信息
    if hasattr(basic_fvg, 'score'):
        enhanced_fvg.score = basic_fvg.score
    
    return enhanced_fvg