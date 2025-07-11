# -*- coding: utf-8 -*-
"""
author: claude
create_dt: 2025/01/11
describe: 市场结构突破检测 (BOS/CHOCH)
ADD: 实现分型判断(BOS_FX/CHOCH_FX)和笔判断(BOS_BI/CHOCH_BI)两种类型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from ..objects import NewBar, FX, BI
from ..enum import Direction, Mark
from ..utils.ta import ATR


@dataclass
class StructureBreak:
    """市场结构突破"""
    symbol: str
    dt: datetime
    
    # 突破类型
    break_type: str  # BOS_FX, CHOCH_FX, BOS_BI, CHOCH_BI
    direction: Direction  # UP, DOWN
    
    # 基础信息
    broken_level: float  # 被突破的水平
    break_price: float  # 突破价格
    break_distance: float  # 突破距离
    
    # 结构关联 (根据类型不同)
    breaking_fractal: Optional[FX] = None  # FX类型时的突破分型
    broken_fractal: Optional[FX] = None    # FX类型时的被突破分型
    breaking_stroke: Optional[BI] = None   # BI类型时的突破笔
    broken_stroke: Optional[BI] = None     # BI类型时的被突破笔
    
    # 确认指标
    atr_multiple: float = 0.0  # 突破距离的ATR倍数
    volume_confirmation: bool = False  # 成交量确认
    time_efficiency: float = 0.0  # 时间效率
    momentum_alignment: bool = False  # 动量对齐
    
    # 质量评估
    conviction_score: float = 0.0  # 0.0-1.0 确信度评分
    false_break_probability: float = 0.0  # 假突破概率
    follow_through_potential: float = 0.0  # 跟进潜力
    
    # 状态
    is_confirmed: bool = False
    is_failed: bool = False
    
    # 缓存
    cache: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'dt': self.dt.isoformat(),
            'break_type': self.break_type,
            'direction': self.direction.value,
            'broken_level': self.broken_level,
            'break_price': self.break_price,
            'break_distance': self.break_distance,
            'atr_multiple': self.atr_multiple,
            'volume_confirmation': self.volume_confirmation,
            'time_efficiency': self.time_efficiency,
            'momentum_alignment': self.momentum_alignment,
            'conviction_score': self.conviction_score,
            'false_break_probability': self.false_break_probability,
            'follow_through_potential': self.follow_through_potential,
            'is_confirmed': self.is_confirmed,
            'is_failed': self.is_failed
        }


class StructureBreakDetector:
    """市场结构突破检测器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化结构突破检测器
        
        Args:
            config: 检测配置参数
        """
        self.config = config or {}
        
        # 基础突破条件
        self.min_atr_multiple = self.config.get('min_atr_multiple', 1.0)
        self.min_volume_ratio = self.config.get('min_volume_ratio', 1.2)
        self.max_time_bars = self.config.get('max_time_bars', 10)
        
        # FX类型检测参数
        self.fx_lookback = self.config.get('fx_lookback', 20)  # 向前寻找分型的范围
        self.fx_min_strength = self.config.get('fx_min_strength', 3)
        
        # BI类型检测参数
        self.bi_lookback = self.config.get('bi_lookback', 10)  # 向前寻找笔的范围
        self.bi_min_power = self.config.get('bi_min_power', 0.0)
        
        # CHOCH检测参数
        self.choch_momentum_required = self.config.get('choch_momentum_required', True)
        self.choch_internal_structure_required = self.config.get('choch_internal_structure_required', True)
    
    def detect_all_structure_breaks(self, bars: List[NewBar], 
                                   fractals: List[FX], 
                                   strokes: List[BI]) -> List[StructureBreak]:
        """检测所有类型的市场结构突破
        
        Args:
            bars: CZSC处理后的K线列表
            fractals: 分型列表
            strokes: 笔列表
            
        Returns:
            检测到的结构突破列表
        """
        all_breaks = []
        
        # 计算ATR
        atr = self._calculate_atr(bars, 14)
        avg_volume = self._calculate_avg_volume(bars, 20)
        
        # 检测基于分型的突破 (BOS_FX, CHOCH_FX)
        fx_breaks = self.detect_fractal_structure_breaks(bars, fractals, atr, avg_volume)
        all_breaks.extend(fx_breaks)
        
        # 检测基于笔的突破 (BOS_BI, CHOCH_BI)
        bi_breaks = self.detect_stroke_structure_breaks(bars, strokes, atr, avg_volume)
        all_breaks.extend(bi_breaks)
        
        # 按时间排序
        all_breaks.sort(key=lambda x: x.dt)
        
        return all_breaks
    
    def detect_fractal_structure_breaks(self, bars: List[NewBar], 
                                       fractals: List[FX], 
                                       atr: float, 
                                       avg_volume: float) -> List[StructureBreak]:
        """检测基于分型的结构突破 (BOS_FX, CHOCH_FX)
        
        Args:
            bars: K线列表
            fractals: 分型列表
            atr: ATR值
            avg_volume: 平均成交量
            
        Returns:
            分型结构突破列表
        """
        breaks = []
        
        if len(fractals) < 3:
            return breaks
        
        # 遍历分型，检查是否形成突破
        for i in range(2, len(fractals)):
            current_fx = fractals[i]
            
            # 寻找之前的关键分型作为突破目标
            target_fx = self._find_target_fractal_for_break(current_fx, fractals[:i])
            if not target_fx:
                continue
            
            # 检查是否确实形成突破
            break_info = self._check_fractal_break(current_fx, target_fx, bars, atr)
            if not break_info['is_break']:
                continue
            
            # 确定突破类型 (BOS_FX vs CHOCH_FX)
            break_type = self._determine_fractal_break_type(
                current_fx, target_fx, fractals[:i]
            )
            
            # 计算确认指标
            confirmations = self._calculate_fractal_confirmations(
                current_fx, target_fx, bars, atr, avg_volume
            )
            
            # 创建结构突破对象
            structure_break = StructureBreak(
                symbol=current_fx.symbol,
                dt=current_fx.dt,
                break_type=break_type,
                direction=Direction.Up if current_fx.mark == Mark.G else Direction.Down,
                broken_level=target_fx.fx,
                break_price=current_fx.fx,
                break_distance=break_info['distance'],
                breaking_fractal=current_fx,
                broken_fractal=target_fx,
                atr_multiple=break_info['distance'] / atr if atr > 0 else 0,
                volume_confirmation=confirmations['volume_confirmed'],
                time_efficiency=confirmations['time_efficiency'],
                momentum_alignment=confirmations['momentum_aligned'],
                conviction_score=confirmations['conviction_score'],
                false_break_probability=confirmations['false_break_prob'],
                follow_through_potential=confirmations['follow_through_potential'],
                is_confirmed=confirmations['conviction_score'] >= 0.7
            )
            
            breaks.append(structure_break)
        
        return breaks
    
    def detect_stroke_structure_breaks(self, bars: List[NewBar], 
                                     strokes: List[BI], 
                                     atr: float, 
                                     avg_volume: float) -> List[StructureBreak]:
        """检测基于笔的结构突破 (BOS_BI, CHOCH_BI)
        
        Args:
            bars: K线列表
            strokes: 笔列表
            atr: ATR值
            avg_volume: 平均成交量
            
        Returns:
            笔结构突破列表
        """
        breaks = []
        
        if len(strokes) < 3:
            return breaks
        
        # 遍历笔，检查是否形成突破
        for i in range(2, len(strokes)):
            current_bi = strokes[i]
            
            # 寻找之前的关键笔作为突破目标
            target_bi = self._find_target_stroke_for_break(current_bi, strokes[:i])
            if not target_bi:
                continue
            
            # 检查是否确实形成突破
            break_info = self._check_stroke_break(current_bi, target_bi, atr)
            if not break_info['is_break']:
                continue
            
            # 确定突破类型 (BOS_BI vs CHOCH_BI)
            break_type = self._determine_stroke_break_type(
                current_bi, target_bi, strokes[:i]
            )
            
            # 计算确认指标
            confirmations = self._calculate_stroke_confirmations(
                current_bi, target_bi, bars, atr, avg_volume
            )
            
            # 创建结构突破对象
            structure_break = StructureBreak(
                symbol=current_bi.symbol,
                dt=current_bi.edt,
                break_type=break_type,
                direction=current_bi.direction,
                broken_level=target_bi.high if current_bi.direction == Direction.Up else target_bi.low,
                break_price=current_bi.high if current_bi.direction == Direction.Up else current_bi.low,
                break_distance=break_info['distance'],
                breaking_stroke=current_bi,
                broken_stroke=target_bi,
                atr_multiple=break_info['distance'] / atr if atr > 0 else 0,
                volume_confirmation=confirmations['volume_confirmed'],
                time_efficiency=confirmations['time_efficiency'],
                momentum_alignment=confirmations['momentum_aligned'],
                conviction_score=confirmations['conviction_score'],
                false_break_probability=confirmations['false_break_prob'],
                follow_through_potential=confirmations['follow_through_potential'],
                is_confirmed=confirmations['conviction_score'] >= 0.7
            )
            
            breaks.append(structure_break)
        
        return breaks
    
    def _find_target_fractal_for_break(self, current_fx: FX, 
                                     previous_fractals: List[FX]) -> Optional[FX]:
        """寻找作为突破目标的分型"""
        if not previous_fractals:
            return None
        
        # 寻找相同类型的最近分型
        same_type_fractals = [fx for fx in previous_fractals 
                             if fx.mark == current_fx.mark]
        
        if not same_type_fractals:
            return None
        
        # 返回最近的同类型分型
        return same_type_fractals[-1]
    
    def _find_target_stroke_for_break(self, current_bi: BI, 
                                    previous_strokes: List[BI]) -> Optional[BI]:
        """寻找作为突破目标的笔"""
        if not previous_strokes:
            return None
        
        # 寻找相同方向的最近笔
        same_direction_strokes = [bi for bi in previous_strokes 
                                 if bi.direction == current_bi.direction]
        
        if not same_direction_strokes:
            return None
        
        # 返回最近的同方向笔
        return same_direction_strokes[-1]
    
    def _check_fractal_break(self, current_fx: FX, target_fx: FX, 
                           bars: List[NewBar], atr: float) -> Dict[str, Any]:
        """检查分型是否确实突破了目标分型"""
        is_break = False
        distance = 0.0
        
        if current_fx.mark == Mark.G:  # 顶分型
            if current_fx.fx > target_fx.fx:
                is_break = True
                distance = current_fx.fx - target_fx.fx
        else:  # 底分型
            if current_fx.fx < target_fx.fx:
                is_break = True
                distance = target_fx.fx - current_fx.fx
        
        # 检查突破幅度是否足够
        if is_break and atr > 0:
            atr_multiple = distance / atr
            if atr_multiple < self.min_atr_multiple:
                is_break = False
        
        return {
            'is_break': is_break,
            'distance': distance,
            'atr_multiple': distance / atr if atr > 0 else 0
        }
    
    def _check_stroke_break(self, current_bi: BI, target_bi: BI, 
                          atr: float) -> Dict[str, Any]:
        """检查笔是否确实突破了目标笔"""
        is_break = False
        distance = 0.0
        
        if current_bi.direction == Direction.Up:
            if current_bi.high > target_bi.high:
                is_break = True
                distance = current_bi.high - target_bi.high
        else:
            if current_bi.low < target_bi.low:
                is_break = True
                distance = target_bi.low - current_bi.low
        
        # 检查突破幅度是否足够
        if is_break and atr > 0:
            atr_multiple = distance / atr
            if atr_multiple < self.min_atr_multiple:
                is_break = False
        
        return {
            'is_break': is_break,
            'distance': distance,
            'atr_multiple': distance / atr if atr > 0 else 0
        }
    
    def _determine_fractal_break_type(self, current_fx: FX, target_fx: FX, 
                                    previous_fractals: List[FX]) -> str:
        """确定分型突破类型 (BOS_FX vs CHOCH_FX)"""
        # 简化逻辑：如果前面有反向分型，则认为是CHOCH，否则是BOS
        recent_fractals = previous_fractals[-5:] if len(previous_fractals) >= 5 else previous_fractals
        
        # 检查是否有方向改变
        has_opposite_fractal = any(fx.mark != current_fx.mark for fx in recent_fractals)
        
        if has_opposite_fractal:
            return "CHOCH_FX"  # Change of Character
        else:
            return "BOS_FX"    # Break of Structure
    
    def _determine_stroke_break_type(self, current_bi: BI, target_bi: BI, 
                                   previous_strokes: List[BI]) -> str:
        """确定笔突破类型 (BOS_BI vs CHOCH_BI)"""
        # 简化逻辑：如果前面有反向笔，则认为是CHOCH，否则是BOS
        recent_strokes = previous_strokes[-3:] if len(previous_strokes) >= 3 else previous_strokes
        
        # 检查是否有方向改变
        has_opposite_stroke = any(bi.direction != current_bi.direction for bi in recent_strokes)
        
        if has_opposite_stroke:
            return "CHOCH_BI"  # Change of Character
        else:
            return "BOS_BI"    # Break of Structure
    
    def _calculate_fractal_confirmations(self, current_fx: FX, target_fx: FX, 
                                       bars: List[NewBar], atr: float, 
                                       avg_volume: float) -> Dict[str, Any]:
        """计算分型突破的确认指标"""
        # 成交量确认
        fractal_volumes = [bar.vol for bar in current_fx.elements]
        max_volume = max(fractal_volumes) if fractal_volumes else 0
        volume_confirmed = max_volume > avg_volume * self.min_volume_ratio
        
        # 时间效率（分型形成的时间跨度）
        time_span = (current_fx.dt - target_fx.dt).total_seconds() / 3600  # 小时
        time_efficiency = max(0.0, 1.0 - time_span / 240)  # 240小时为基准
        
        # 动量对齐（简化版本）
        momentum_aligned = len(current_fx.elements) >= self.fx_min_strength
        
        # 综合确信度评分
        conviction_factors = [
            1.0 if volume_confirmed else 0.5,
            time_efficiency,
            1.0 if momentum_aligned else 0.7
        ]
        conviction_score = np.mean(conviction_factors)
        
        # 假突破概率（基于历史突破后的行为）
        false_break_prob = max(0.0, 1.0 - conviction_score)
        
        # 跟进潜力
        follow_through_potential = conviction_score * 0.8 + time_efficiency * 0.2
        
        return {
            'volume_confirmed': volume_confirmed,
            'time_efficiency': time_efficiency,
            'momentum_aligned': momentum_aligned,
            'conviction_score': conviction_score,
            'false_break_prob': false_break_prob,
            'follow_through_potential': follow_through_potential
        }
    
    def _calculate_stroke_confirmations(self, current_bi: BI, target_bi: BI, 
                                      bars: List[NewBar], atr: float, 
                                      avg_volume: float) -> Dict[str, Any]:
        """计算笔突破的确认指标"""
        # 成交量确认
        volume_confirmed = current_bi.power_volume > avg_volume * self.min_volume_ratio
        
        # 时间效率
        time_efficiency = min(1.0, current_bi.length / self.max_time_bars)
        
        # 动量对齐
        momentum_aligned = current_bi.power_price >= self.bi_min_power
        
        # 综合确信度评分
        conviction_factors = [
            1.0 if volume_confirmed else 0.5,
            time_efficiency,
            1.0 if momentum_aligned else 0.7
        ]
        conviction_score = np.mean(conviction_factors)
        
        # 假突破概率
        false_break_prob = max(0.0, 1.0 - conviction_score)
        
        # 跟进潜力
        follow_through_potential = conviction_score * 0.8 + time_efficiency * 0.2
        
        return {
            'volume_confirmed': volume_confirmed,
            'time_efficiency': time_efficiency,
            'momentum_aligned': momentum_aligned,
            'conviction_score': conviction_score,
            'false_break_prob': false_break_prob,
            'follow_through_potential': follow_through_potential
        }
    
    def _calculate_atr(self, bars: List[NewBar], period: int = 14) -> float:
        """计算ATR"""
        if len(bars) < period:
            return np.mean([bar.high - bar.low for bar in bars])
        
        recent_bars = bars[-period:]
        tr_values = []
        
        for i in range(1, len(recent_bars)):
            current = recent_bars[i]
            previous = recent_bars[i-1]
            
            hl = current.high - current.low
            hc = abs(current.high - previous.close)
            lc = abs(current.low - previous.close)
            
            tr_values.append(max(hl, hc, lc))
        
        return np.mean(tr_values) if tr_values else 0.0
    
    def _calculate_avg_volume(self, bars: List[NewBar], period: int = 20) -> float:
        """计算平均成交量"""
        if len(bars) < period:
            return np.mean([bar.vol for bar in bars])
        
        return np.mean([bar.vol for bar in bars[-period:]])


def detect_structure_breaks_from_czsc(bars: List[NewBar], 
                                     fractals: List[FX], 
                                     strokes: List[BI],
                                     config: Optional[Dict[str, Any]] = None) -> List[StructureBreak]:
    """从CZSC结构中检测市场结构突破
    
    Args:
        bars: CZSC处理后的K线列表
        fractals: 分型列表
        strokes: 笔列表
        config: 检测配置
        
    Returns:
        检测到的结构突破列表
    """
    detector = StructureBreakDetector(config)
    return detector.detect_all_structure_breaks(bars, fractals, strokes)


def detect_fractal_breaks_only(bars: List[NewBar], 
                              fractals: List[FX],
                              config: Optional[Dict[str, Any]] = None) -> List[StructureBreak]:
    """仅检测基于分型的结构突破 (BOS_FX, CHOCH_FX)
    
    Args:
        bars: CZSC处理后的K线列表
        fractals: 分型列表
        config: 检测配置
        
    Returns:
        检测到的分型结构突破列表
    """
    detector = StructureBreakDetector(config)
    atr = detector._calculate_atr(bars, 14)
    avg_volume = detector._calculate_avg_volume(bars, 20)
    return detector.detect_fractal_structure_breaks(bars, fractals, atr, avg_volume)


def detect_stroke_breaks_only(bars: List[NewBar], 
                             strokes: List[BI],
                             config: Optional[Dict[str, Any]] = None) -> List[StructureBreak]:
    """仅检测基于笔的结构突破 (BOS_BI, CHOCH_BI)
    
    Args:
        bars: CZSC处理后的K线列表
        strokes: 笔列表
        config: 检测配置
        
    Returns:
        检测到的笔结构突破列表
    """
    detector = StructureBreakDetector(config)
    atr = detector._calculate_atr(bars, 14)
    avg_volume = detector._calculate_avg_volume(bars, 20)
    return detector.detect_stroke_structure_breaks(bars, strokes, atr, avg_volume)