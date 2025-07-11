# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2024/12/28
describe: POI (Points of Interest) 基类
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..enum import Direction, Mark


class POIBase:
    """POI基础类，定义所有POI共有的属性和方法"""
    
    def __init__(self, symbol: str, poi_type: str, dt: datetime, high: float, low: float, 
                 direction: Direction, **kwargs):
        # 基本信息
        self.symbol = symbol                              # 交易品种
        self.poi_type = poi_type                          # POI类型，如 "FVG", "OB", "Support", "Resistance"
        self.dt = dt                                      # 形成时间
        
        # 价格信息
        self.high = high                                  # 上边界
        self.low = low                                    # 下边界
        
        # 方向信息
        self.direction = direction                        # 方向，如 Direction.Up, Direction.Down
        
        # 状态信息
        self.is_valid = kwargs.get('is_valid', True)                    # 是否有效
        self.is_tested = kwargs.get('is_tested', False)                 # 是否被测试过
        self.test_count = kwargs.get('test_count', 0)                   # 测试次数
        self.last_test_dt = kwargs.get('last_test_dt', None)            # 最后测试时间
        
        # 缓解信息
        self.mitigation_level = kwargs.get('mitigation_level', 0.0)     # 缓解程度 0-1
        self.is_mitigated = kwargs.get('is_mitigated', False)           # 是否已缓解
        self.mitigation_threshold = kwargs.get('mitigation_threshold', 0.5)  # 缓解阈值
        
        # 评分信息
        self.score = kwargs.get('score', 0.0)                          # 综合评分
        
        # 辅助信息
        self.cache = kwargs.get('cache', {})                            # 缓存字典
        
        # 价格边界校正
        if self.high < self.low:
            self.high, self.low = self.low, self.high
    
    
    @property
    def size(self) -> float:
        """获取POI的大小"""
        return abs(self.high - self.low)
    
    @property 
    def center(self) -> float:
        """获取POI的中心价格"""
        return (self.high + self.low) / 2.0
    
    @property
    def upper_quarter(self) -> float:
        """获取POI的上四分位价格"""
        return self.low + (self.high - self.low) * 0.75
    
    @property
    def lower_quarter(self) -> float:
        """获取POI的下四分位价格"""
        return self.low + (self.high - self.low) * 0.25
    
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
    
    def update_mitigation(self, price: float, dt: datetime) -> bool:
        """更新缓解状态
        
        Args:
            price: 当前价格
            dt: 当前时间
            
        Returns:
            是否状态有更新
        """
        if self.is_mitigated:
            return False
            
        # 如果价格进入POI范围，更新缓解程度
        if self.contains(price):
            old_mitigation = self.mitigation_level
            
            # 计算当前缓解程度
            if self.direction == Direction.Up:
                # 看涨POI，价格从上往下进入，计算进入程度
                current_mitigation = (self.high - price) / self.size
            else:
                # 看跌POI，价格从下往上进入，计算进入程度
                current_mitigation = (price - self.low) / self.size
            
            current_mitigation = max(0.0, min(1.0, current_mitigation))
            
            # 更新最大缓解程度
            self.mitigation_level = max(self.mitigation_level, current_mitigation)
            
            # 更新测试状态
            if not self.is_tested:
                self.is_tested = True
                self.test_count = 1
                self.last_test_dt = dt
            else:
                self.test_count += 1
                self.last_test_dt = dt
            
            # 检查是否达到缓解阈值
            if self.mitigation_level >= self.mitigation_threshold:
                self.is_mitigated = True
            
            return old_mitigation != self.mitigation_level
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'poi_type': self.poi_type,
            'dt': self.dt.isoformat(),
            'high': self.high,
            'low': self.low,
            'direction': self.direction.value,
            'is_valid': self.is_valid,
            'is_tested': self.is_tested,
            'test_count': self.test_count,
            'last_test_dt': self.last_test_dt.isoformat() if self.last_test_dt else None,
            'mitigation_level': self.mitigation_level,
            'is_mitigated': self.is_mitigated,
            'mitigation_threshold': self.mitigation_threshold,
            'score': self.score,
            'size': self.size,
            'center': self.center
        }
    
    def __repr__(self):
        return f"{self.poi_type}(symbol={self.symbol}, dt={self.dt}, range=[{self.low:.4f}, {self.high:.4f}], " \
               f"direction={self.direction.value}, valid={self.is_valid}, tested={self.is_tested})"