# -*- coding: utf-8 -*-
"""
增强Order Block - 使用统一缓解分析框架
author: Claude Code AI Assistant
create_dt: 2025-01-11  
describe: 为Order Block实现与FVG相同级别的缓解分析功能
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from czsc.objects import NewBar, FX
from czsc.enum import Direction, Mark
from czsc.poi.mitigation_framework import (
    OrderBlockMitigationAnalyzer, MitigationAnalysis, MitigationConfig,
    MitigationMethod, ZoneDefinition
)


@dataclass
class EnhancedOrderBlock:
    """增强Order Block - 集成通用缓解分析框架"""
    
    # 基础属性
    symbol: str
    dt: datetime
    source_fractal: FX
    
    # 区域定义
    high: float
    low: float
    poi_level: float  # Point of Interest
    
    # 类型和方向
    ob_type: str  # DEMAND_ZONE, SUPPLY_ZONE
    direction: Direction  # UP, DOWN
    
    # 验证条件
    liquidity_sweep_confirmed: bool = False
    fvg_creation_confirmed: bool = False
    volume_spike_confirmed: bool = False
    
    # 缓解分析（使用通用框架）
    mitigation_config: MitigationConfig = field(default_factory=lambda: MitigationConfig(
        method=MitigationMethod.CLOSE,
        mitigation_threshold=0.7,
        trading_effectiveness_threshold=0.7
    ))
    _mitigation_analyzer: Optional[OrderBlockMitigationAnalyzer] = field(default=None, init=False)
    _mitigation_analysis: Optional[MitigationAnalysis] = field(default=None, init=False)
    
    # 缓存
    cache: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 设置方向和类型
        if self.source_fractal.mark == Mark.D:
            self.ob_type = "DEMAND_ZONE"
            self.direction = Direction.Up
            self.poi_level = self.source_fractal.low
        else:
            self.ob_type = "SUPPLY_ZONE" 
            self.direction = Direction.Down
            self.poi_level = self.source_fractal.high
        
        # 初始化缓解分析器
        self._mitigation_analyzer = OrderBlockMitigationAnalyzer(self.mitigation_config)
        self._mitigation_analysis = MitigationAnalysis(config=self.mitigation_config)
    
    @property
    def size(self) -> float:
        """OB大小"""
        return abs(self.high - self.low)
    
    @property 
    def center(self) -> float:
        """OB中心价格"""
        return (self.high + self.low) / 2.0
    
    # ============ 缓解分析接口（与FVG统一） ============
    
    @property
    def mitigation_level(self) -> float:
        """当前缓解程度"""
        return self._mitigation_analysis.current_level if self._mitigation_analysis else 0.0
    
    @property
    def is_tested(self) -> bool:
        """是否被测试过"""
        return self._mitigation_analysis.is_tested if self._mitigation_analysis else False
    
    @property
    def is_mitigated(self) -> bool:
        """是否被缓解"""
        return self._mitigation_analysis.is_mitigated if self._mitigation_analysis else False
    
    @property
    def is_valid(self) -> bool:
        """是否仍然有效"""
        return self._mitigation_analysis.is_valid if self._mitigation_analysis else True
    
    @property
    def interaction_history(self) -> List[Dict[str, Any]]:
        """交互历史"""
        if not self._mitigation_analysis:
            return []
        
        # 转换为与FVG兼容的格式
        history = []
        for event in self._mitigation_analysis.interaction_history:
            history.append({
                'dt': event.timestamp,
                'type': event.event_type,
                'price': event.price,
                'mitigation_level': event.mitigation_level
            })
        return history
    
    def get_mitigation_type(self) -> str:
        """获取缓解类型（与FVG统一接口）"""
        if not self._mitigation_analysis:
            return "NONE"
        return self._mitigation_analysis.mitigation_type.value
    
    def get_mitigation_description(self) -> str:
        """获取缓解描述（与FVG统一接口）"""
        if not self._mitigation_analysis:
            return "无缓解(0.0%)"
        return self._mitigation_analysis.get_mitigation_description()
    
    def is_effective_for_trading(self) -> bool:
        """判断是否具有交易价值（与FVG统一接口）"""
        return self._mitigation_analysis.is_effective_for_trading if self._mitigation_analysis else True
    
    def update_mitigation(self, price: float, dt: datetime) -> bool:
        """更新缓解状态（与FVG统一接口）"""
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
            zone_type="ORDER_BLOCK"
        )
        
        # 更新缓解分析
        return self._mitigation_analyzer.update_single_bar(self._mitigation_analysis, zone, fake_bar)
    
    def batch_update_mitigation(self, bars: List[NewBar]) -> bool:
        """批量更新缓解状态"""
        if not self._mitigation_analyzer or not self._mitigation_analysis:
            return False
        
        zone = ZoneDefinition(
            high=self.high,
            low=self.low,
            direction=self.direction,
            zone_type="ORDER_BLOCK"
        )
        
        # 使用通用框架批量分析
        updated_analysis = self._mitigation_analyzer.analyze_zone_mitigation(
            zone, bars, self._mitigation_analysis
        )
        
        # 检查是否有更新
        if updated_analysis.current_level != self._mitigation_analysis.current_level:
            self._mitigation_analysis = updated_analysis
            return True
        
        return False
    
    # ============ 高级缓解分析方法 ============
    
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
        """获取详细状态（调试用）"""
        if not self._mitigation_analysis:
            return {}
        
        return self._mitigation_analysis.get_status_summary()
    
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
    
    # ============ 兼容性方法 ============
    
    def contains(self, price: float) -> bool:
        """判断价格是否在OB范围内"""
        return self.low <= price <= self.high
    
    def distance_to(self, price: float) -> float:
        """计算价格到OB的距离"""
        if price > self.high:
            return price - self.high
        elif price < self.low:
            return self.low - price
        else:
            return 0.0
    
    @property
    def mitigation_percentage(self) -> float:
        """缓解百分比（兼容旧接口）"""
        return self.mitigation_level * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = {
            'symbol': self.symbol,
            'dt': self.dt.isoformat(),
            'ob_type': self.ob_type,
            'direction': self.direction.value,
            'high': self.high,
            'low': self.low,
            'poi_level': self.poi_level,
            'size': self.size,
            'center': self.center,
            
            # 验证条件
            'liquidity_sweep_confirmed': self.liquidity_sweep_confirmed,
            'fvg_creation_confirmed': self.fvg_creation_confirmed,
            'volume_spike_confirmed': self.volume_spike_confirmed,
            
            # 缓解状态（使用通用框架）
            'mitigation_level': self.mitigation_level,
            'mitigation_percentage': self.mitigation_percentage,
            'mitigation_type': self.get_mitigation_type(),
            'mitigation_description': self.get_mitigation_description(),
            'is_tested': self.is_tested,
            'is_mitigated': self.is_mitigated,
            'is_valid': self.is_valid,
            'is_effective': self.is_effective_for_trading(),
            'interaction_count': len(self.interaction_history)
        }
        
        # 添加统计信息
        base_dict.update(self.get_mitigation_statistics())
        
        return base_dict
    
    def __repr__(self):
        return (f"EnhancedOrderBlock(symbol={self.symbol}, type={self.ob_type}, "
                f"size={self.size:.2f}, mitigation={self.mitigation_level:.1%}, "
                f"effective={self.is_effective_for_trading()})")


# ============ 工厂函数 ============

def create_enhanced_order_block_from_basic(basic_ob, 
                                          mitigation_config: MitigationConfig = None) -> EnhancedOrderBlock:
    """从基础Order Block创建增强版本"""
    
    # 从BasicOrderBlock或OrderBlock转换
    enhanced_ob = EnhancedOrderBlock(
        symbol=getattr(basic_ob, 'symbol', 'UNKNOWN'),
        dt=getattr(basic_ob, 'dt', datetime.now()),
        source_fractal=getattr(basic_ob, 'source_fractal', None) or getattr(basic_ob, 'related_fractal', None),
        high=basic_ob.high if hasattr(basic_ob, 'high') else basic_ob.upper_boundary,
        low=basic_ob.low if hasattr(basic_ob, 'low') else basic_ob.lower_boundary,
        poi_level=getattr(basic_ob, 'poi_level', (basic_ob.high + basic_ob.low) / 2),
        liquidity_sweep_confirmed=getattr(basic_ob, 'liquidity_sweep_confirmed', False),
        fvg_creation_confirmed=getattr(basic_ob, 'fvg_creation_confirmed', False),
        volume_spike_confirmed=getattr(basic_ob, 'volume_spike_confirmed', False),
        mitigation_config=mitigation_config or MitigationConfig()
    )
    
    return enhanced_ob


def create_enhanced_order_block_from_fractal(fractal: FX, 
                                           ob_bars: List[NewBar],
                                           mitigation_config: MitigationConfig = None) -> EnhancedOrderBlock:
    """从分型直接创建增强Order Block"""
    
    # 确定OB边界
    if fractal.mark == Mark.D:  # 底分型
        high = max(bar.high for bar in fractal.elements)
        low = min(bar.low for bar in fractal.elements)
    else:  # 顶分型
        high = max(bar.high for bar in fractal.elements)
        low = min(bar.low for bar in fractal.elements)
    
    enhanced_ob = EnhancedOrderBlock(
        symbol=fractal.symbol,
        dt=fractal.dt,
        source_fractal=fractal,
        high=high,
        low=low,
        poi_level=fractal.fx,
        ob_type="DEMAND_ZONE" if fractal.mark == Mark.D else "SUPPLY_ZONE",
        direction=Direction.Up if fractal.mark == Mark.D else Direction.Down,
        mitigation_config=mitigation_config or MitigationConfig()
    )
    
    # 如果提供了后续K线数据，进行批量缓解分析
    if ob_bars:
        enhanced_ob.batch_update_mitigation(ob_bars)
    
    return enhanced_ob