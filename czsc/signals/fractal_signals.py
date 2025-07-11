# -*- coding: utf-8 -*-
"""
分型单体信号生成器 - 只分析单个分型的各种强弱特征

生成信号类型：
1. power_signal - 力度信号
2. position_signal - 位置信号  
3. timing_signal - 时间信号
4. volume_signal - 成交量信号
"""

from typing import List, Optional
from datetime import datetime, timedelta

from czsc.objects import FX
from czsc.enum import Mark
from czsc.signals.base import (
    ComponentSignal, ComponentSignalGenerator, ComponentSignalStrength, 
    SignalDirection
)
from czsc.signals.adapters import ComponentAdapter


class FractalComponentSignalGenerator(ComponentSignalGenerator):
    """
    分型单体信号生成器 - 只分析单个分型的各种强弱特征
    
    生成信号类型：
    1. power - 力度信号
    2. position - 位置信号  
    3. timing - 时间信号
    4. volume - 成交量信号
    """
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def get_signal_types(self) -> List[str]:
        return ['power', 'position', 'timing', 'volume', 'behavior']
    
    def generate_component_signals(self, fractal: FX) -> List[ComponentSignal]:
        """从单个分型生成多个维度的信号"""
        signals = []
        fractal_props = ComponentAdapter.extract_objective_properties(fractal)
        
        # 1. 力度信号
        power_signal = self._generate_power_signal(fractal, fractal_props)
        if power_signal:
            signals.append(power_signal)
        
        # 2. 位置信号
        position_signal = self._generate_position_signal(fractal, fractal_props)
        if position_signal:
            signals.append(position_signal)
        
        # 3. 时间信号
        timing_signal = self._generate_timing_signal(fractal, fractal_props)
        if timing_signal:
            signals.append(timing_signal)
        
        # 4. 成交量信号
        volume_signal = self._generate_volume_signal(fractal, fractal_props)
        if volume_signal:
            signals.append(volume_signal)
        
        # 5. 行为信号
        behavior_signal = self._generate_behavior_signal(fractal, fractal_props)
        if behavior_signal:
            signals.append(behavior_signal)
        
        return signals
    
    def _generate_power_signal(self, fractal: FX, props: dict) -> Optional[ComponentSignal]:
        """生成力度信号 - 纯粹基于分型自身力度"""
        power_str = props.get('power_str', '弱')
        
        # 力度映射
        strength_map = {
            '强': ComponentSignalStrength.STRONG,
            '中': ComponentSignalStrength.MODERATE,
            '弱': ComponentSignalStrength.WEAK
        }
        
        strength = strength_map.get(power_str, ComponentSignalStrength.WEAK)
        if strength == ComponentSignalStrength.WEAK:
            return None  # 弱力度不产生信号
        
        # 评分计算
        score_map = {'强': 80, '中': 50, '弱': 20}
        score = score_map.get(power_str, 20)
        
        return ComponentSignal(
            component_type='fractal',
            component_id=f"fx_{fractal.dt.isoformat()}",
            signal_type='power',
            strength=strength,
            direction=SignalDirection.BULLISH if fractal.mark == Mark.D else SignalDirection.BEARISH,
            score=score,
            confidence=0.7 if power_str == '强' else 0.5,
            reasons=[f"分型力度{power_str}"],
            properties={
                'power_str': power_str,
                'element_count': props.get('element_count', 0),
                'fractal_type': props.get('mark').value
            },
            created_at=fractal.dt,
            expires_at=fractal.dt + timedelta(hours=4)  # 4小时有效期
        )
    
    def _generate_position_signal(self, fractal: FX, props: dict) -> Optional[ComponentSignal]:
        """生成位置信号 - 基于分型在高概率兴趣区(POI)中的位置"""
        
        # 检查是否在重要的POI区域内
        poi_context = self._analyze_poi_context(fractal)
        
        if poi_context['in_poi']:
            strength = ComponentSignalStrength.STRONG if poi_context['poi_quality'] >= 80 else ComponentSignalStrength.MODERATE
            score = poi_context['poi_quality']
            
            return ComponentSignal(
                component_type='fractal',
                component_id=f"fx_{fractal.dt.isoformat()}",
                signal_type='position',
                strength=strength,
                direction=SignalDirection.BULLISH if fractal.mark == Mark.D else SignalDirection.BEARISH,
                score=score,
                confidence=poi_context['confidence'],
                reasons=poi_context['reasons'],
                properties={
                    'poi_type': poi_context['poi_type'],
                    'poi_quality': poi_context['poi_quality'],
                    'fractal_type': props.get('mark').value
                },
                created_at=fractal.dt,
                expires_at=fractal.dt + timedelta(hours=8)  # POI位置信号有效期更长
            )
        
        return None
    
    def _analyze_poi_context(self, fractal: FX) -> dict:
        """分析分型的POI上下文"""
        # 这里需要访问全局的FVG和OB数据
        # 暂时使用简化逻辑，实际应该从信号管理器传入这些数据
        
        # 检查是否在关键价格位置（简化版本）
        is_boundary = fractal.dt.minute in [0, 30]  # 整点或半点
        is_session_boundary = fractal.dt.hour in [9, 13, 21]  # 交易时段边界
        
        if is_boundary or is_session_boundary:
            return {
                'in_poi': True,
                'poi_type': 'time_boundary',
                'poi_quality': 70.0,
                'confidence': 0.6,
                'reasons': ['关键时间边界分型']
            }
        
        return {
            'in_poi': False,
            'poi_type': None,
            'poi_quality': 0.0,
            'confidence': 0.0,
            'reasons': []
        }
    
    def _generate_timing_signal(self, fractal: FX, props: dict) -> Optional[ComponentSignal]:
        """生成时间信号 - 基于分型出现的时间特征"""
        dt = fractal.dt
        
        # 关键时间点判断
        is_key_time = (
            dt.hour in [9, 10, 13, 14, 15] or  # 开盘、收盘时间
            dt.minute in [0, 30] or             # 整点、半点
            dt.weekday() in [0, 4]              # 周一、周五
        )
        
        if is_key_time:
            return ComponentSignal(
                component_type='fractal',
                component_id=f"fx_{fractal.dt.isoformat()}",
                signal_type='timing',
                strength=ComponentSignalStrength.MODERATE,
                direction=SignalDirection.NEUTRAL,
                score=40,
                confidence=0.4,
                reasons=[f"关键时间点({dt.hour}:{dt.minute:02d})"],
                properties={
                    'hour': dt.hour,
                    'minute': dt.minute,
                    'weekday': dt.weekday()
                },
                created_at=fractal.dt,
                expires_at=fractal.dt + timedelta(hours=2)
            )
        
        return None
    
    def _generate_volume_signal(self, fractal: FX, props: dict) -> Optional[ComponentSignal]:
        """生成成交量信号 - 基于成交量特征"""
        # 这里需要成交量分析逻辑
        # 暂时返回None，待后续实现
        return None
    
    def _generate_behavior_signal(self, fractal: FX, props: dict) -> Optional[ComponentSignal]:
        """生成行为信号 - 基于分型中心K线的流动性扫除行为"""
        
        # 分析流动性扫除行为
        liquidity_sweep = self._analyze_liquidity_sweep(fractal)
        
        if liquidity_sweep['has_sweep']:
            return ComponentSignal(
                component_type='fractal',
                component_id=f"fx_{fractal.dt.isoformat()}",
                signal_type='behavior',
                strength=ComponentSignalStrength.STRONG,  # 流动性扫除是强信号
                direction=SignalDirection.BULLISH if fractal.mark == Mark.D else SignalDirection.BEARISH,
                score=liquidity_sweep['score'],
                confidence=liquidity_sweep['confidence'],
                reasons=liquidity_sweep['reasons'],
                properties={
                    'sweep_type': liquidity_sweep['sweep_type'],
                    'sweep_strength': liquidity_sweep['strength'],
                    'fractal_type': props.get('mark').value
                },
                created_at=fractal.dt,
                expires_at=fractal.dt + timedelta(hours=6)
            )
        
        return None
    
    def _analyze_liquidity_sweep(self, fractal: FX) -> dict:
        """分析流动性扫除模式"""
        
        # 获取分型的构成K线
        if not fractal.elements or len(fractal.elements) < 3:
            return {'has_sweep': False}
        
        center_bar = fractal.elements[1]  # 中心K线
        
        # 简化的流动性扫除检测逻辑
        # 实际应该检查是否突破了前期高点/低点后迅速回撤
        
        # 检查K线形态特征
        body_size = abs(center_bar.close - center_bar.open)
        total_size = center_bar.high - center_bar.low
        
        # 检查是否有长上影线或下影线（可能的扫除特征）
        if fractal.mark == Mark.G:  # 顶分型
            upper_shadow = center_bar.high - max(center_bar.open, center_bar.close)
            shadow_ratio = upper_shadow / total_size if total_size > 0 else 0
            
            if shadow_ratio > 0.4:  # 上影线占总长度40%以上
                return {
                    'has_sweep': True,
                    'sweep_type': 'sell_side_liquidity',
                    'strength': shadow_ratio,
                    'score': 75.0,
                    'confidence': 0.7,
                    'reasons': ['扫除卖方流动性', '长上影线确认']
                }
        
        else:  # 底分型
            lower_shadow = min(center_bar.open, center_bar.close) - center_bar.low
            shadow_ratio = lower_shadow / total_size if total_size > 0 else 0
            
            if shadow_ratio > 0.4:  # 下影线占总长度40%以上
                return {
                    'has_sweep': True,
                    'sweep_type': 'buy_side_liquidity',
                    'strength': shadow_ratio,
                    'score': 75.0,
                    'confidence': 0.7,
                    'reasons': ['扫除买方流动性', '长下影线确认']
                }
        
        return {'has_sweep': False}