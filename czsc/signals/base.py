# -*- coding: utf-8 -*-
"""
CZSC新信号系统基础类

实现组件与信号分离的基础框架
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta


class ComponentSignalStrength(Enum):
    """单体组件信号强度"""
    NONE = 0        # 无信号
    WEAK = 1        # 弱信号
    MODERATE = 2    # 中等信号
    STRONG = 3      # 强信号
    VERY_STRONG = 4 # 极强信号


class SignalDirection(Enum):
    """信号方向枚举"""
    BULLISH = "看涨"
    BEARISH = "看跌"
    NEUTRAL = "中性"


class CompositeSignalStrength(Enum):
    """组合信号强度"""
    WEAK = "弱信号"
    MODERATE = "中等信号"  
    STRONG = "强信号"
    VERY_STRONG = "极强信号"
    CRITICAL = "关键信号"


class SignalNecessity(Enum):
    """信号必要性"""
    OPTIONAL = "可选"      # 可有可无
    PREFERRED = "建议"     # 建议有
    REQUIRED = "必须"      # 必须有
    CRITICAL = "关键"      # 关键必须


@dataclass
class ComponentSignal:
    """
    单体组件信号 - 单个组件的强弱信号
    """
    component_type: str                      # 组件类型 (fractal, bi, ob, fvg)
    component_id: str                        # 组件唯一标识
    signal_type: str                         # 信号类型 (power, position, timing, etc.)
    strength: ComponentSignalStrength        # 信号强度
    direction: SignalDirection               # 信号方向
    score: float                            # 数值评分 (0-100)
    confidence: float                       # 置信度 (0-1)
    reasons: List[str]                      # 信号产生的原因
    properties: dict                        # 信号的详细属性
    created_at: datetime                    # 信号生成时间
    expires_at: Optional[datetime] = None   # 信号过期时间
    
    def is_valid(self) -> bool:
        """检查信号是否有效"""
        # 对于历史数据测试，不检查过期时间
        # if self.expires_at and datetime.now() > self.expires_at:
        #     return False
        return self.strength != ComponentSignalStrength.NONE


@dataclass
class SignalWeight:
    """信号权重配置"""
    signal_type: str                    # 信号类型
    base_weight: float                  # 基础权重
    necessity: SignalNecessity          # 必要性
    multiplier_conditions: dict         # 乘数条件


@dataclass
class CompositeSignalRule:
    """组合信号规则"""
    name: str
    description: str
    required_signals: List[str]         # 必须信号
    optional_signals: List[str]         # 可选信号
    weights: List[SignalWeight]         # 权重配置
    min_score: float                    # 最低评分
    min_confidence: float               # 最低置信度
    
    def evaluate(self, component_signals: List['ComponentSignal']) -> Optional['CompositeSignal']:
        """评估是否满足规则并生成组合信号"""
        # 这个方法可以在CompositeSignalRule中实现，或者由SignalScoringEngine来处理
        # 这里暂时返回None，实际逻辑在SignalScoringEngine中
        return None


@dataclass
class CompositeSignal:
    """
    组合信号 - 多个单体信号组合的最终交易信号
    """
    name: str                           # 信号名称
    rule_name: str                      # 使用的规则名称
    strength: CompositeSignalStrength   # 组合信号强度
    direction: SignalDirection          # 信号方向
    total_score: float                  # 总评分 (0-1000)
    confidence: float                   # 置信度 (0-1)
    
    # 组成信息
    component_signals: List[ComponentSignal]    # 组成的单体信号
    signal_breakdown: dict                      # 信号评分分解
    weights_applied: dict                       # 应用的权重
    
    # 交易信息
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    priority: int = 0                           # 优先级 (用于排序)
    
    def is_valid(self) -> bool:
        """检查信号是否有效"""
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return self.total_score >= 0 and self.confidence > 0


class ComponentSignalGenerator(ABC):
    """单体组件信号生成器抽象基类"""
    
    @abstractmethod
    def generate_component_signals(self, component: Any) -> List[ComponentSignal]:
        """从单个组件生成信号"""
        pass
    
    @abstractmethod
    def get_signal_types(self) -> List[str]:
        """获取该生成器支持的信号类型"""
        pass