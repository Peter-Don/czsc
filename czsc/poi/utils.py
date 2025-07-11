# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2024/12/28
describe: POI工具函数
"""
from typing import List, Optional, Tuple
from ..objects import NewBar, FX
from ..enum import Direction, Mark


def check_liquidity_sweep(bars: List[NewBar], price_level: float, direction: Direction, 
                         lookback_bars: int = 20, sweep_threshold: float = 0.001) -> bool:
    """检查流动性扫荡
    
    Args:
        bars: K线列表
        price_level: 价格水平
        direction: 扫荡方向
        lookback_bars: 回溯K线数量
        sweep_threshold: 扫荡阈值（价格比例）
        
    Returns:
        是否发生流动性扫荡
    """
    if len(bars) < 2:
        return False
    
    # 取最近的K线
    recent_bars = bars[-lookback_bars:] if len(bars) > lookback_bars else bars
    
    for bar in recent_bars:
        if direction == Direction.Up:
            # 向上扫荡：价格突破上方阻力位后回落
            if bar.high > price_level * (1 + sweep_threshold) and bar.close < price_level:
                return True
        else:
            # 向下扫荡：价格突破下方支撑位后回升
            if bar.low < price_level * (1 - sweep_threshold) and bar.close > price_level:
                return True
    
    return False


def check_body_break(bar: NewBar, price_level: float, direction: Direction, 
                    body_break_threshold: float = 0.5) -> bool:
    """检查实体突破
    
    Args:
        bar: K线
        price_level: 价格水平
        direction: 突破方向
        body_break_threshold: 实体突破阈值（实体需要突破多少比例）
        
    Returns:
        是否发生实体突破
    """
    body_size = abs(bar.close - bar.open)
    
    if direction == Direction.Up:
        # 向上实体突破：收盘价明显高于价格水平
        body_break_distance = bar.close - price_level
        return body_break_distance > body_size * body_break_threshold
    else:
        # 向下实体突破：收盘价明显低于价格水平
        body_break_distance = price_level - bar.close
        return body_break_distance > body_size * body_break_threshold


def check_wick_rejection(bar: NewBar, price_level: float, direction: Direction,
                        wick_ratio_threshold: float = 0.3) -> bool:
    """检查影线拒绝
    
    Args:
        bar: K线
        price_level: 价格水平
        direction: 拒绝方向
        wick_ratio_threshold: 影线比例阈值
        
    Returns:
        是否发生影线拒绝
    """
    bar_range = bar.high - bar.low
    if bar_range <= 0:
        return False
    
    if direction == Direction.Up:
        # 向上拒绝：上影线长，价格触及水平后回落
        upper_wick = bar.high - max(bar.open, bar.close)
        return (bar.high >= price_level and 
                bar.close < price_level and 
                upper_wick / bar_range >= wick_ratio_threshold)
    else:
        # 向下拒绝：下影线长，价格触及水平后回升
        lower_wick = min(bar.open, bar.close) - bar.low
        return (bar.low <= price_level and 
                bar.close > price_level and 
                lower_wick / bar_range >= wick_ratio_threshold)


def calculate_interaction_strength(bars: List[NewBar], price_level: float, 
                                 interaction_type: str) -> float:
    """计算交互强度
    
    Args:
        bars: K线列表
        price_level: 价格水平
        interaction_type: 交互类型
        
    Returns:
        交互强度评分 (0-1)
    """
    if not bars:
        return 0.0
    
    strength_score = 0.0
    
    # 基于交互类型计算强度
    if interaction_type == "body_break":
        # 实体突破的强度
        for bar in bars[-3:]:  # 最近3根K线
            if check_body_break(bar, price_level, Direction.Up) or \
               check_body_break(bar, price_level, Direction.Down):
                body_size = abs(bar.close - bar.open)
                bar_range = bar.high - bar.low
                if bar_range > 0:
                    strength_score += (body_size / bar_range) * 0.3
    
    elif interaction_type == "wick_rejection":
        # 影线拒绝的强度
        for bar in bars[-3:]:
            if check_wick_rejection(bar, price_level, Direction.Up) or \
               check_wick_rejection(bar, price_level, Direction.Down):
                strength_score += 0.4
    
    elif interaction_type == "liquidity_sweep":
        # 流动性扫荡的强度
        if check_liquidity_sweep(bars, price_level, Direction.Up) or \
           check_liquidity_sweep(bars, price_level, Direction.Down):
            strength_score += 0.6
    
    return min(1.0, strength_score)


def get_mitigation_level(bars: List[NewBar], fvg_high: float, fvg_low: float, 
                        direction: Direction) -> float:
    """计算FVG的缓解程度
    
    Args:
        bars: K线列表
        fvg_high: FVG上边界
        fvg_low: FVG下边界
        direction: FVG方向
        
    Returns:
        缓解程度 (0-1)
    """
    if not bars:
        return 0.0
    
    fvg_size = fvg_high - fvg_low
    if fvg_size <= 0:
        return 0.0
    
    max_mitigation = 0.0
    
    for bar in bars:
        # 检查K线是否与FVG有交集
        if bar.low <= fvg_high and bar.high >= fvg_low:
            if direction == Direction.Up:
                # 看涨FVG，价格从上往下进入
                if bar.low <= fvg_low:
                    # 完全缓解
                    max_mitigation = 1.0
                else:
                    # 部分缓解
                    mitigation = (fvg_high - bar.low) / fvg_size
                    max_mitigation = max(max_mitigation, mitigation)
            else:
                # 看跌FVG，价格从下往上进入
                if bar.high >= fvg_high:
                    # 完全缓解
                    max_mitigation = 1.0
                else:
                    # 部分缓解
                    mitigation = (bar.high - fvg_low) / fvg_size
                    max_mitigation = max(max_mitigation, mitigation)
    
    return min(1.0, max_mitigation)


def find_nearest_fx_levels(fxs: List[FX], current_price: float, 
                          max_distance: float = 0.05) -> List[FX]:
    """找到最近的分型水平
    
    Args:
        fxs: 分型列表
        current_price: 当前价格
        max_distance: 最大距离比例
        
    Returns:
        最近的分型列表
    """
    if not fxs:
        return []
    
    nearby_fxs = []
    
    for fx in fxs:
        # 计算分型与当前价格的距离
        distance = abs(fx.fx - current_price) / current_price
        
        if distance <= max_distance:
            nearby_fxs.append(fx)
    
    # 按距离排序
    nearby_fxs.sort(key=lambda x: abs(x.fx - current_price))
    
    return nearby_fxs


def calculate_atr(bars: List[NewBar], period: int = 14) -> float:
    """计算平均真实波动率
    
    Args:
        bars: K线列表
        period: 计算周期
        
    Returns:
        ATR值
    """
    if len(bars) < period:
        # 数据不足，使用简单的平均价格范围
        return sum(bar.high - bar.low for bar in bars) / len(bars) if bars else 0.0
    
    tr_values = []
    for i in range(1, len(bars)):
        tr = max(
            bars[i].high - bars[i].low,
            abs(bars[i].high - bars[i-1].close),
            abs(bars[i].low - bars[i-1].close)
        )
        tr_values.append(tr)
    
    if len(tr_values) < period:
        return sum(tr_values) / len(tr_values) if tr_values else 0.0
    
    return sum(tr_values[-period:]) / period