# -*- coding: utf-8 -*-
"""
POI (Point of Interest) 基类
author: Claude Code AI Assistant
create_dt: 2025-01-11
describe: FVG和Order Block的共同基类，提供统一的缓解分析机制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from czsc.objects import NewBar
from czsc.enum import Direction
from czsc.poi.mitigation_framework import (
    MitigationAnalysis, MitigationConfig, MitigationMethod,
    UniversalMitigationAnalyzer, ZoneDefinition
)


class BasePOI(ABC):
    """POI基类 - 提供所有POI的通用功能"""
    
    def __init__(self, symbol: str, dt: datetime, high: float, low: float, 
                 direction: Direction, poi_type: str,
                 is_valid: bool = True, is_tested: bool = False, is_mitigated: bool = False,
                 mitigation_config: MitigationConfig = None,
                 cache: Dict[str, Any] = None):
        # 基础属性
        self.symbol = symbol
        self.dt = dt
        self.high = high
        self.low = low
        self.direction = direction
        self.poi_type = poi_type
        
        # 状态
        self.is_valid = is_valid
        self.is_tested = is_tested
        self.is_mitigated = is_mitigated
        
        # 缓解分析（通用框架）
        self.mitigation_config = mitigation_config or MitigationConfig()
        self._mitigation_analyzer: Optional[UniversalMitigationAnalyzer] = None
        self._mitigation_analysis: Optional[MitigationAnalysis] = None
        
        # 缓存
        self.cache = cache or {}
        
        # 初始化
        self.__post_init__()
    
    def __post_init__(self):
        """初始化后处理 - 设置缓解分析器"""
        if self._mitigation_analyzer is None:
            self._mitigation_analyzer = self._create_mitigation_analyzer()
        if self._mitigation_analysis is None:
            self._mitigation_analysis = MitigationAnalysis(config=self.mitigation_config)
    
    @abstractmethod
    def _create_mitigation_analyzer(self) -> UniversalMitigationAnalyzer:
        """创建专用的缓解分析器（子类实现）"""
        pass
    
    # ============ 通用属性 ============
    
    @property
    def size(self) -> float:
        """POI大小"""
        return abs(self.high - self.low)
    
    @property
    def center(self) -> float:
        """POI中心价格"""
        return (self.high + self.low) / 2.0
    
    @property
    def midpoint(self) -> float:
        """POI中点（与center相同）"""
        return self.center
    
    # ============ 缓解分析接口（统一） ============
    
    @property
    def mitigation_level(self) -> float:
        """当前缓解程度"""
        return self._mitigation_analysis.current_level if self._mitigation_analysis else 0.0
    
    @property
    def max_mitigation_level(self) -> float:
        """历史最大缓解程度"""
        return self._mitigation_analysis.max_mitigation_level if self._mitigation_analysis else 0.0
    
    @property
    def interaction_history(self) -> List[Dict[str, Any]]:
        """交互历史（统一格式）"""
        if not self._mitigation_analysis:
            return []
        
        history = []
        for event in self._mitigation_analysis.interaction_history:
            history.append({
                'dt': event.timestamp,
                'type': event.event_type,
                'price': event.price,
                'mitigation_level': event.mitigation_level,
                'method': event.method_used.value
            })
        return history
    
    def get_mitigation_type(self) -> str:
        """获取缓解类型"""
        if not self._mitigation_analysis:
            return "NONE"
        return self._mitigation_analysis.mitigation_type.value
    
    def get_mitigation_description(self) -> str:
        """获取缓解描述"""
        if not self._mitigation_analysis:
            return "无缓解(0.0%)"
        return self._mitigation_analysis.get_mitigation_description()
    
    def is_effective_for_trading(self) -> bool:
        """判断是否具有交易价值"""
        return self._mitigation_analysis.is_effective_for_trading if self._mitigation_analysis else True
    
    # ============ 缓解更新方法 ============
    
    def update_mitigation(self, price: float, dt: datetime) -> bool:
        """更新缓解状态"""
        if not self._mitigation_analyzer or not self._mitigation_analysis:
            return False
        
        # 创建虚拟K线
        fake_bar = NewBar(
            symbol=self.symbol,
            id=0,
            dt=dt,
            freq=None,
            open=price,
            close=price,
            high=price,
            low=price,
            vol=0,
            amount=0,
            elements=[],
            cache={}
        )
        
        # 创建区域定义
        zone = ZoneDefinition(
            high=self.high,
            low=self.low,
            direction=self.direction,
            zone_type=self.poi_type
        )
        
        # 更新缓解分析
        updated = self._mitigation_analyzer.update_single_bar(self._mitigation_analysis, zone, fake_bar)
        
        # 同步状态到基础属性
        if updated:
            self.is_tested = self._mitigation_analysis.is_tested
            self.is_mitigated = self._mitigation_analysis.is_mitigated
            self.is_valid = self._mitigation_analysis.is_valid
        
        return updated
    
    def batch_update_mitigation(self, bars: List[NewBar]) -> bool:
        """批量更新缓解状态"""
        if not self._mitigation_analyzer or not self._mitigation_analysis:
            return False
        
        zone = ZoneDefinition(
            high=self.high,
            low=self.low,
            direction=self.direction,
            zone_type=self.poi_type
        )
        
        # 使用通用框架批量分析
        updated_analysis = self._mitigation_analyzer.analyze_zone_mitigation(
            zone, bars, self._mitigation_analysis
        )
        
        # 检查是否有更新
        if updated_analysis.current_level != self._mitigation_analysis.current_level:
            self._mitigation_analysis = updated_analysis
            
            # 同步状态
            self.is_tested = self._mitigation_analysis.is_tested
            self.is_mitigated = self._mitigation_analysis.is_mitigated
            self.is_valid = self._mitigation_analysis.is_valid
            
            return True
        
        return False
    
    # ============ 配置管理 ============
    
    def set_mitigation_method(self, method: MitigationMethod):
        """设置缓解判断方法"""
        self.mitigation_config.method = method
        if self._mitigation_analyzer:
            self._mitigation_analyzer.config.method = method
    
    def set_mitigation_thresholds(self, mitigation_threshold: float = None,
                                 trading_threshold: float = None):
        """设置缓解阈值"""
        if mitigation_threshold is not None:
            self.mitigation_config.mitigation_threshold = mitigation_threshold
            if self._mitigation_analyzer:
                self._mitigation_analyzer.config.mitigation_threshold = mitigation_threshold
        
        if trading_threshold is not None:
            self.mitigation_config.trading_effectiveness_threshold = trading_threshold
            if self._mitigation_analyzer:
                self._mitigation_analyzer.config.trading_effectiveness_threshold = trading_threshold
    
    # ============ 几何计算 ============
    
    def contains(self, price: float) -> bool:
        """判断价格是否在POI范围内"""
        return self.low <= price <= self.high
    
    def distance_to(self, price: float) -> float:
        """计算价格到POI的距离"""
        if price > self.high:
            return price - self.high
        elif price < self.low:
            return self.low - price
        else:
            return 0.0
    
    def overlaps_with(self, other: 'BasePOI') -> bool:
        """判断是否与另一个POI重叠"""
        return not (self.high < other.low or self.low > other.high)
    
    def overlap_percentage(self, other: 'BasePOI') -> float:
        """计算与另一个POI的重叠百分比"""
        if not self.overlaps_with(other):
            return 0.0
        
        overlap_low = max(self.low, other.low)
        overlap_high = min(self.high, other.high)
        overlap_size = overlap_high - overlap_low
        
        return overlap_size / self.size if self.size > 0 else 0.0
    
    # ============ 统计和状态 ============
    
    def get_mitigation_statistics(self) -> Dict[str, Any]:
        """获取缓解统计信息"""
        if not self._mitigation_analysis:
            return {}
        
        return {
            'test_count': self._mitigation_analysis.test_count,
            'first_test_time': self._mitigation_analysis.first_test_time,
            'full_mitigation_time': self._mitigation_analysis.full_mitigation_time,
            'max_mitigation_level': self._mitigation_analysis.max_mitigation_level,
            'interaction_count': len(self._mitigation_analysis.interaction_history),
            'mitigation_type': self.get_mitigation_type(),
            'effectiveness': self.is_effective_for_trading()
        }
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """获取详细状态"""
        if not self._mitigation_analysis:
            return {}
        
        return self._mitigation_analysis.get_status_summary()
    
    # ============ 序列化 ============
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（基础版本）"""
        base_dict = {
            'symbol': self.symbol,
            'dt': self.dt.isoformat(),
            'poi_type': self.poi_type,
            'direction': self.direction.value,
            'high': self.high,
            'low': self.low,
            'size': self.size,
            'center': self.center,
            
            # 状态
            'is_valid': self.is_valid,
            'is_tested': self.is_tested,
            'is_mitigated': self.is_mitigated,
            
            # 缓解分析
            'mitigation_level': self.mitigation_level,
            'mitigation_type': self.get_mitigation_type(),
            'mitigation_description': self.get_mitigation_description(),
            'is_effective': self.is_effective_for_trading(),
            'interaction_count': len(self.interaction_history)
        }
        
        # 添加统计信息
        base_dict.update(self.get_mitigation_statistics())
        
        return base_dict
    
    def __repr__(self):
        return (f"{self.__class__.__name__}(symbol={self.symbol}, type={self.poi_type}, "
                f"size={self.size:.2f}, mitigation={self.mitigation_level:.1%}, "
                f"effective={self.is_effective_for_trading()})")


# ============ 具体POI类型的便捷属性 ============

@property 
def mitigation_percentage(self) -> float:
    """缓解百分比（兼容旧接口）"""
    return self.mitigation_level * 100.0

# 添加到BasePOI类
BasePOI.mitigation_percentage = mitigation_percentage