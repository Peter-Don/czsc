# -*- coding: utf-8 -*-
"""
author: claude
create_dt: 2025/01/11
describe: Order Block (订单块) 检测与分析
基于CZSC分型的科学订单块定义，融合流动性扫荡和FVG确认
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from ..objects import NewBar, FX, BI
from ..enum import Direction, Mark
from .fvg import FVG, identify_fvg_basic


@dataclass
class LiquiditySweep:
    """流动性扫荡结果"""
    detected: bool
    sweep_type: str  # 'BULLISH_SWEEP', 'BEARISH_SWEEP' 
    target_level: float  # 被扫荡的关键水平
    sweep_distance: float  # 扫荡距离
    reversion_speed: int  # 回撤速度（K线数）
    volume_confirmation: bool  # 成交量确认
    confidence_score: float  # 置信度评分


@dataclass
class OrderBlock:
    """订单块"""
    symbol: str
    dt: datetime
    
    # CZSC核心关联
    source_fractal: FX  # 源分型
    decisive_bars: List[NewBar]  # 决定性K线组
    fractal_strength: int  # 分型强度（构成K线数）
    
    # 区域定义
    high: float
    low: float
    poi_level: float  # 兴趣点价格（Point of Interest）
    
    # 类型分类
    ob_type: str  # DEMAND_ZONE, SUPPLY_ZONE
    sub_type: str  # EXTREME_OB, DECISIONAL_OB, BREAKER_OB
    
    # 科学验证条件
    liquidity_sweep_confirmed: bool = False  # 流动性扫荡确认
    fvg_creation_confirmed: bool = False  # modify: 后续产生明确的FVG确认
    volume_spike_confirmed: bool = False  # 成交量激增确认
    
    # 强度评估
    strength_score: float = 0.0  # 0.0-1.0
    reliability_score: float = 0.0  # 0.0-1.0
    
    # 状态追踪
    mitigation_percentage: float = 0.0  # 0.0-100.0
    is_valid: bool = True
    is_tested: bool = False
    is_mitigated: bool = False
    
    # 相关事件
    liquidity_sweep_event: Optional[LiquiditySweep] = None
    subsequent_fvg: Optional[FVG] = None  # modify: 后续产生的FVG
    
    # 缓存
    cache: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.source_fractal.mark == Mark.D:
            self.ob_type = "DEMAND_ZONE"  # 需求区域（支撑）
            self.poi_level = self.source_fractal.low
        else:
            self.ob_type = "SUPPLY_ZONE"  # 供应区域（阻力）
            self.poi_level = self.source_fractal.high
    
    @property
    def size(self) -> float:
        """订单块大小"""
        return abs(self.high - self.low)
    
    @property
    def center(self) -> float:
        """订单块中心价格"""
        return (self.high + self.low) / 2.0
    
    def contains(self, price: float) -> bool:
        """判断价格是否在订单块范围内"""
        return self.low <= price <= self.high
    
    def distance_to(self, price: float) -> float:
        """计算价格到订单块的距离"""
        if price > self.high:
            return price - self.high
        elif price < self.low:
            return self.low - price
        else:
            return 0.0
    
    def update_mitigation(self, price: float, dt: datetime) -> bool:
        """更新缓解状态"""
        if self.is_mitigated:
            return False
        
        # 检查价格是否进入订单块
        if self.contains(price):
            if not self.is_tested:
                self.is_tested = True
            
            # 计算缓解程度
            if self.ob_type == "DEMAND_ZONE":
                # 需求区域，价格从上方回测
                self.mitigation_percentage = min(100.0, 
                    ((self.high - price) / self.size) * 100)
            else:
                # 供应区域，价格从下方回测
                self.mitigation_percentage = min(100.0, 
                    ((price - self.low) / self.size) * 100)
            
            # 检查是否过度缓解（失效）
            if self.mitigation_percentage >= 70.0:
                self.is_mitigated = True
                self.is_valid = False
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'dt': self.dt.isoformat(),
            'ob_type': self.ob_type,
            'sub_type': self.sub_type,
            'high': self.high,
            'low': self.low,
            'poi_level': self.poi_level,
            'size': self.size,
            'center': self.center,
            'fractal_strength': self.fractal_strength,
            'liquidity_sweep_confirmed': self.liquidity_sweep_confirmed,
            'fvg_creation_confirmed': self.fvg_creation_confirmed,
            'volume_spike_confirmed': self.volume_spike_confirmed,
            'strength_score': self.strength_score,
            'reliability_score': self.reliability_score,
            'mitigation_percentage': self.mitigation_percentage,
            'is_valid': self.is_valid,
            'is_tested': self.is_tested,
            'is_mitigated': self.is_mitigated
        }


class OrderBlockDetector:
    """基于CZSC分型的科学订单块检测器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化订单块检测器
        
        Args:
            config: 检测配置参数
        """
        self.config = config or {}
        
        # 分型强度要求
        self.min_fractal_strength = self.config.get('min_fractal_strength', 3)
        
        # 流动性扫荡参数
        self.sweep_atr_factor = self.config.get('sweep_atr_factor', 0.5)
        self.sweep_reversion_bars = self.config.get('sweep_reversion_bars', 5)
        self.sweep_volume_multiplier = self.config.get('sweep_volume_multiplier', 1.5)
        
        # modify: FVG确认参数
        self.fvg_lookforward_bars = self.config.get('fvg_lookforward_bars', 10)
        self.fvg_min_size_atr = self.config.get('fvg_min_size_atr', 0.3)
        
        # 成交量激增参数
        self.volume_spike_multiplier = self.config.get('volume_spike_multiplier', 2.0)
        self.volume_lookback = self.config.get('volume_lookback', 20)
        
        # 缓解阈值
        self.mitigation_threshold = self.config.get('mitigation_threshold', 0.7)
    
    def detect_order_blocks(self, bars: List[NewBar], fractals: List[FX]) -> List[OrderBlock]:
        """检测科学订单块
        
        Args:
            bars: CZSC处理后的K线列表
            fractals: 分型列表
            
        Returns:
            检测到的订单块列表
        """
        if len(bars) < 50 or len(fractals) < 2:
            return []
        
        order_blocks = []
        
        # 计算ATR用于各种阈值判断
        atr = self._calculate_atr(bars, 14)
        avg_volume = self._calculate_avg_volume(bars, self.volume_lookback)
        
        for i, fx in enumerate(fractals):
            # 检查分型强度要求
            if len(fx.elements) < self.min_fractal_strength:
                continue
            
            # 检查流动性扫荡
            liquidity_sweep = self._check_liquidity_sweep(fx, bars, atr)
            if not liquidity_sweep.detected:
                continue
            
            # modify: 检查后续FVG产生
            subsequent_fvg = self._check_subsequent_fvg_creation(fx, bars)
            if not subsequent_fvg:
                continue  # modify: 必须产生后续FVG才认为是有效订单块
            
            # 检查成交量激增
            volume_spike = self._check_volume_spike(fx, bars, avg_volume)
            
            # 创建订单块
            ob = self._create_order_block(
                fx=fx,
                bars=bars,
                liquidity_sweep=liquidity_sweep,
                subsequent_fvg=subsequent_fvg,
                volume_spike=volume_spike,
                atr=atr
            )
            
            if ob:
                order_blocks.append(ob)
        
        return order_blocks
    
    def _check_liquidity_sweep(self, fx: FX, bars: List[NewBar], atr: float) -> LiquiditySweep:
        """检查分型是否伴随流动性扫荡"""
        # 找到分型在K线中的位置
        fx_index = self._find_bar_index(fx.dt, bars)
        if fx_index == -1 or fx_index < 5:
            return LiquiditySweep(
                detected=False,
                sweep_type="NONE",
                target_level=fx.fx,
                sweep_distance=0.0,
                reversion_speed=0,
                volume_confirmation=False,
                confidence_score=0.0
            )
        
        # 检查分型前后的价格行为
        pre_bars = bars[max(0, fx_index - 5):fx_index]
        post_bars = bars[fx_index:min(len(bars), fx_index + self.sweep_reversion_bars + 1)]
        
        sweep_detected = False
        sweep_distance = 0.0
        reversion_speed = 0
        volume_confirmation = False
        
        if fx.mark == Mark.G:  # 顶分型
            # 检查是否有价格突破然后快速回落
            for i, bar in enumerate(post_bars[1:], 1):  # 跳过分型本身
                if bar.high > fx.fx:
                    sweep_distance = bar.high - fx.fx
                    # 检查后续回撤
                    for j, revert_bar in enumerate(post_bars[i+1:], i+1):
                        if revert_bar.close < fx.fx:
                            sweep_detected = True
                            reversion_speed = j - i
                            break
                    break
            
            # 检查成交量确认
            if sweep_detected:
                sweep_bar_volumes = [bar.vol for bar in post_bars[1:reversion_speed+2]]
                avg_vol = np.mean([bar.vol for bar in pre_bars])
                if max(sweep_bar_volumes) > avg_vol * self.sweep_volume_multiplier:
                    volume_confirmation = True
        
        elif fx.mark == Mark.D:  # 底分型
            # 检查是否有价格跌破然后快速回升
            for i, bar in enumerate(post_bars[1:], 1):  # 跳过分型本身
                if bar.low < fx.fx:
                    sweep_distance = fx.fx - bar.low
                    # 检查后续回撤
                    for j, revert_bar in enumerate(post_bars[i+1:], i+1):
                        if revert_bar.close > fx.fx:
                            sweep_detected = True
                            reversion_speed = j - i
                            break
                    break
            
            # 检查成交量确认
            if sweep_detected:
                sweep_bar_volumes = [bar.vol for bar in post_bars[1:reversion_speed+2]]
                avg_vol = np.mean([bar.vol for bar in pre_bars])
                if max(sweep_bar_volumes) > avg_vol * self.sweep_volume_multiplier:
                    volume_confirmation = True
        
        # 计算置信度评分
        confidence_score = 0.0
        if sweep_detected:
            # 距离评分
            distance_score = min(1.0, sweep_distance / (atr * self.sweep_atr_factor))
            # 速度评分
            speed_score = max(0.0, 1.0 - reversion_speed / self.sweep_reversion_bars)
            # 成交量评分
            volume_score = 1.0 if volume_confirmation else 0.5
            
            confidence_score = (distance_score + speed_score + volume_score) / 3.0
        
        return LiquiditySweep(
            detected=sweep_detected,
            sweep_type=f"{'BEARISH' if fx.mark == Mark.G else 'BULLISH'}_SWEEP",
            target_level=fx.fx,
            sweep_distance=sweep_distance,
            reversion_speed=reversion_speed,
            volume_confirmation=volume_confirmation,
            confidence_score=confidence_score
        )
    
    def _check_subsequent_fvg_creation(self, fx: FX, bars: List[NewBar]) -> Optional[FVG]:
        """modify: 检查订单块后续是否创建了FVG"""
        fx_index = self._find_bar_index(fx.dt, bars)
        if fx_index == -1 or fx_index + self.fvg_lookforward_bars >= len(bars):
            return None
        
        # 获取分型后的K线序列
        post_bars = bars[fx_index + 1:fx_index + self.fvg_lookforward_bars + 1]
        
        # 使用FVG基础识别功能
        fvgs = identify_fvg_basic(post_bars, self.fvg_min_size_atr)
        
        # 找到第一个符合条件的FVG
        for fvg in fvgs:
            # 检查FVG方向是否与预期一致
            if fx.mark == Mark.D and fvg.direction == Direction.Up:
                # 底分型后应该产生看涨FVG
                return fvg
            elif fx.mark == Mark.G and fvg.direction == Direction.Down:
                # 顶分型后应该产生看跌FVG
                return fvg
        
        return None
    
    def _check_volume_spike(self, fx: FX, bars: List[NewBar], avg_volume: float) -> bool:
        """检查分型形成时是否有成交量激增"""
        if not fx.elements or len(fx.elements) < 3:
            return False
        
        # 检查分型构成K线的成交量
        fractal_volumes = [bar.vol for bar in fx.elements]
        max_volume = max(fractal_volumes)
        
        return max_volume > avg_volume * self.volume_spike_multiplier
    
    def _create_order_block(self, fx: FX, bars: List[NewBar], 
                           liquidity_sweep: LiquiditySweep, 
                           subsequent_fvg: FVG,
                           volume_spike: bool,
                           atr: float) -> Optional[OrderBlock]:
        """创建订单块对象"""
        
        # 确定决定性K线（通常是分型的最后一根K线）
        decisive_bars = [fx.elements[-1]] if fx.elements else []
        
        # 确定订单块边界
        if fx.mark == Mark.D:
            # 底分型 -> 需求区域
            high = max([bar.high for bar in fx.elements])
            low = min([bar.low for bar in fx.elements])
            sub_type = "EXTREME_OB" if liquidity_sweep.confidence_score > 0.8 else "DECISIONAL_OB"
        else:
            # 顶分型 -> 供应区域
            high = max([bar.high for bar in fx.elements])
            low = min([bar.low for bar in fx.elements])
            sub_type = "EXTREME_OB" if liquidity_sweep.confidence_score > 0.8 else "DECISIONAL_OB"
        
        # 计算强度评分
        strength_score = self._calculate_strength_score(
            liquidity_sweep, subsequent_fvg, volume_spike, fx, atr
        )
        
        # 计算可靠性评分
        reliability_score = self._calculate_reliability_score(
            liquidity_sweep, subsequent_fvg, volume_spike, fx
        )
        
        ob = OrderBlock(
            symbol=fx.symbol,
            dt=fx.dt,
            source_fractal=fx,
            decisive_bars=decisive_bars,
            fractal_strength=len(fx.elements),
            high=high,
            low=low,
            poi_level=fx.fx,
            ob_type="DEMAND_ZONE" if fx.mark == Mark.D else "SUPPLY_ZONE",
            sub_type=sub_type,
            liquidity_sweep_confirmed=liquidity_sweep.detected,
            fvg_creation_confirmed=subsequent_fvg is not None,
            volume_spike_confirmed=volume_spike,
            strength_score=strength_score,
            reliability_score=reliability_score,
            liquidity_sweep_event=liquidity_sweep,
            subsequent_fvg=subsequent_fvg
        )
        
        return ob
    
    def _calculate_strength_score(self, liquidity_sweep: LiquiditySweep, 
                                 subsequent_fvg: FVG, volume_spike: bool, 
                                 fx: FX, atr: float) -> float:
        """计算订单块强度评分"""
        score = 0.0
        
        # 流动性扫荡强度 (40%)
        if liquidity_sweep.detected:
            score += 0.4 * liquidity_sweep.confidence_score
        
        # 后续FVG强度 (30%)
        if subsequent_fvg:
            fvg_strength = min(1.0, subsequent_fvg.size / atr) if atr > 0 else 0.5
            score += 0.3 * fvg_strength
        
        # 成交量确认 (20%)
        if volume_spike:
            score += 0.2
        
        # 分型强度 (10%)
        fractal_strength = min(1.0, len(fx.elements) / 5.0)  # 5根K线为满分
        score += 0.1 * fractal_strength
        
        return min(1.0, score)
    
    def _calculate_reliability_score(self, liquidity_sweep: LiquiditySweep, 
                                   subsequent_fvg: FVG, volume_spike: bool, 
                                   fx: FX) -> float:
        """计算订单块可靠性评分"""
        score = 0.5  # 基础分数
        
        # 必要条件都满足 (modify: 包括FVG创建)
        if liquidity_sweep.detected and subsequent_fvg and volume_spike:
            score = 0.9
        elif liquidity_sweep.detected and subsequent_fvg:
            score = 0.8  # modify: 流动性扫荡 + FVG创建
        elif liquidity_sweep.detected and volume_spike:
            score = 0.7
        elif subsequent_fvg and volume_spike:
            score = 0.6  # modify: FVG创建 + 成交量
        
        return score
    
    def _calculate_atr(self, bars: List[NewBar], period: int = 14) -> float:
        """计算ATR"""
        if len(bars) < period:
            return np.mean([bar.high - bar.low for bar in bars])
        
        highs = [bar.high for bar in bars[-period:]]
        lows = [bar.low for bar in bars[-period:]]
        closes = [bar.close for bar in bars[-period:]]
        
        tr_values = []
        for i in range(1, len(highs)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr_values.append(max(hl, hc, lc))
        
        return np.mean(tr_values) if tr_values else 0.0
    
    def _calculate_avg_volume(self, bars: List[NewBar], period: int = 20) -> float:
        """计算平均成交量"""
        if len(bars) < period:
            return np.mean([bar.vol for bar in bars])
        
        return np.mean([bar.vol for bar in bars[-period:]])
    
    def _find_bar_index(self, target_dt: datetime, bars: List[NewBar]) -> int:
        """查找指定时间的K线索引"""
        for i, bar in enumerate(bars):
            if bar.dt == target_dt:
                return i
        return -1


def detect_order_blocks_from_czsc(bars: List[NewBar], fractals: List[FX], 
                                  config: Optional[Dict[str, Any]] = None) -> List[OrderBlock]:
    """从CZSC结构中检测订单块
    
    Args:
        bars: CZSC处理后的K线列表
        fractals: 分型列表
        config: 检测配置
        
    Returns:
        检测到的订单块列表
    """
    detector = OrderBlockDetector(config)
    return detector.detect_order_blocks(bars, fractals)