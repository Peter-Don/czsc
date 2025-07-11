# -*- coding: utf-8 -*-
"""
机构足迹组件 - SMC/ICT理论核心组件

这些组件基于机构交易行为理论，用于识别市场中的高概率区域：
- FVG (Fair Value Gap): 价格价值缺口
- OB (Order Block): 订单块
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from czsc.enum import Direction


class FVGDirection(Enum):
    """FVG方向枚举"""
    BULLISH = "看涨"
    BEARISH = "看跌"


class OBDirection(Enum):
    """订单块方向枚举"""
    BULLISH = "需求区"    # 看涨订单块
    BEARISH = "供给区"    # 看跌订单块


@dataclass
class FVG:
    """
    价格价值缺口 (Fair Value Gap)
    
    定义: 由三根连续K线构成的价格缺口
    - 看涨FVG: 第一根K线的高点 < 第三根K线的低点
    - 看跌FVG: 第一根K线的低点 > 第三根K线的高点
    """
    # 基础属性
    id: str                           # 唯一标识
    symbol: str                       # 交易对
    dt: datetime                      # 形成时间（中间K线时间）
    direction: FVGDirection           # 方向
    
    # 价格属性
    top: float                        # 缺口上边界
    bottom: float                     # 缺口下边界
    midpoint_ce: float                # 50%位置 (Consequent Encroachment)
    
    # 状态属性
    is_mitigated: bool = False        # 是否被完全回补
    mitigation_percentage: float = 0.0  # 已回补百分比 (0-1)
    mitigation_dt: Optional[datetime] = None  # 回补时间
    
    # 构成K线信息
    first_bar_dt: Optional[datetime] = None     # 第一根K线时间
    second_bar_dt: Optional[datetime] = None    # 第二根K线时间（中心）
    third_bar_dt: Optional[datetime] = None     # 第三根K线时间
    
    # 缓存和扩展
    cache: dict = field(default_factory=dict)
    
    @property
    def size(self) -> float:
        """缺口大小（点数）"""
        return self.top - self.bottom
    
    @property
    def size_percentage(self) -> float:
        """缺口大小（相对于中心价格的百分比）"""
        center_price = (self.top + self.bottom) / 2
        return self.size / center_price if center_price > 0 else 0
    
    def update_mitigation(self, current_price: float, current_dt: datetime):
        """更新回补状态"""
        if self.direction == FVGDirection.BULLISH:
            # 看涨FVG，价格回到缺口内即为回补
            if current_price <= self.top:
                if current_price <= self.bottom:
                    # 完全回补
                    self.mitigation_percentage = 1.0
                    self.is_mitigated = True
                else:
                    # 部分回补
                    self.mitigation_percentage = (self.top - current_price) / self.size
                
                if self.mitigation_dt is None:
                    self.mitigation_dt = current_dt
        
        else:  # BEARISH
            # 看跌FVG，价格回到缺口内即为回补
            if current_price >= self.bottom:
                if current_price >= self.top:
                    # 完全回补
                    self.mitigation_percentage = 1.0
                    self.is_mitigated = True
                else:
                    # 部分回补
                    self.mitigation_percentage = (current_price - self.bottom) / self.size
                
                if self.mitigation_dt is None:
                    self.mitigation_dt = current_dt


@dataclass
class OB:
    """
    订单块 (Order Block)
    
    定义: 在强劲趋势行情发起前的最后一根反向K线
    这是机构在该区域留下大量订单的证据
    """
    # 基础属性
    id: str                           # 唯一标识
    symbol: str                       # 交易对
    dt: datetime                      # 订单块K线时间
    direction: OBDirection            # 方向（需求区/供给区）
    
    # 价格属性
    top: float                        # OB上边界（该K线最高价）
    bottom: float                     # OB下边界（该K线最低价）
    open_price: float                 # 开盘价
    close_price: float                # 收盘价
    
    # 状态属性
    is_mitigated: bool = False        # 是否被缓解
    mitigation_dt: Optional[datetime] = None  # 缓解时间
    
    # 关联信息
    related_move_has_fvg: bool = False  # 后续走势是否包含FVG
    related_fvg_ids: list = field(default_factory=list)  # 关联的FVG ID列表
    
    # 强度指标
    subsequent_move_strength: float = 0.0  # 后续走势强度
    volume_profile: dict = field(default_factory=dict)  # 成交量特征
    
    # 缓存和扩展
    cache: dict = field(default_factory=dict)
    
    @property
    def size(self) -> float:
        """订单块大小（点数）"""
        return self.top - self.bottom
    
    @property
    def body_size(self) -> float:
        """实体大小"""
        return abs(self.close_price - self.open_price)
    
    @property
    def is_bullish_candle(self) -> bool:
        """是否为阳线"""
        return self.close_price > self.open_price
    
    def update_mitigation(self, current_price: float, current_dt: datetime):
        """更新缓解状态"""
        if self.direction == OBDirection.BULLISH:
            # 看涨订单块，价格跌破底部即为缓解
            if current_price < self.bottom:
                self.is_mitigated = True
                if self.mitigation_dt is None:
                    self.mitigation_dt = current_dt
        
        else:  # BEARISH
            # 看跌订单块，价格突破顶部即为缓解
            if current_price > self.top:
                self.is_mitigated = True
                if self.mitigation_dt is None:
                    self.mitigation_dt = current_dt
    
    @property
    def quality_score(self) -> float:
        """订单块质量评分 (0-100)"""
        score = 50.0  # 基础分数
        
        # 后续走势强度加分
        if self.subsequent_move_strength > 0.5:
            score += 20
        elif self.subsequent_move_strength > 0.3:
            score += 10
        
        # 包含FVG加分
        if self.related_move_has_fvg:
            score += 15
        
        # 成交量特征加分
        volume_multiplier = self.volume_profile.get('volume_multiplier', 1.0)
        if volume_multiplier > 2.0:
            score += 15
        elif volume_multiplier > 1.5:
            score += 10
        
        return min(100.0, score)