# -*- coding: utf-8 -*-
"""
机构足迹信号生成器 - FVG和OB的单体信号生成

基于SMC/ICT理论，为机构足迹组件生成量化信号：
- FVGSignalGenerator: FVG质量信号
- OBSignalGenerator: OB质量信号
"""

from typing import List, Optional
from datetime import datetime, timedelta

from czsc.components.institutional import FVG, OB, FVGDirection, OBDirection
from czsc.signals.base import (
    ComponentSignal, ComponentSignalGenerator, ComponentSignalStrength, 
    SignalDirection
)


class FVGSignalGenerator(ComponentSignalGenerator):
    """
    FVG单体信号生成器
    
    分析单个FVG的质量特征，生成质量信号
    """
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def get_signal_types(self) -> List[str]:
        return ['quality']
    
    def generate_component_signals(self, fvg: FVG) -> List[ComponentSignal]:
        """从单个FVG生成质量信号"""
        signals = []
        
        # 生成质量信号
        quality_signal = self._generate_quality_signal(fvg)
        if quality_signal:
            signals.append(quality_signal)
        
        return signals
    
    def _generate_quality_signal(self, fvg: FVG) -> Optional[ComponentSignal]:
        """生成FVG质量信号"""
        
        # 分析FVG质量
        quality_analysis = self._analyze_fvg_quality(fvg)
        
        if quality_analysis['score'] >= 50:  # 最低质量阈值
            return ComponentSignal(
                component_type='fvg',
                component_id=fvg.id,
                signal_type='quality',
                strength=quality_analysis['strength'],
                direction=SignalDirection.BULLISH if fvg.direction == FVGDirection.BULLISH else SignalDirection.BEARISH,
                score=quality_analysis['score'],
                confidence=quality_analysis['confidence'],
                reasons=quality_analysis['reasons'],
                properties={
                    'fvg_size': fvg.size,
                    'size_percentage': fvg.size_percentage,
                    'mitigation_status': fvg.is_mitigated,
                    'mitigation_percentage': fvg.mitigation_percentage
                },
                created_at=fvg.dt,
                expires_at=fvg.dt + timedelta(hours=24)  # FVG信号有效期24小时
            )
        
        return None
    
    def _analyze_fvg_quality(self, fvg: FVG) -> dict:
        """分析FVG质量"""
        score = 50.0  # 基础分数
        reasons = []
        
        # 1. 大小评估（30%权重）
        size_score = self._evaluate_fvg_size(fvg)
        score += size_score * 0.3
        if size_score > 20:
            reasons.append(f"FVG大小显著({fvg.size_percentage:.2%})")
        
        # 2. 完整性评估（40%权重）
        integrity_score = self._evaluate_fvg_integrity(fvg)
        score += integrity_score * 0.4
        if integrity_score > 15:
            reasons.append("FVG结构完整")
        
        # 3. 时间因素（20%权重）
        time_score = self._evaluate_fvg_timing(fvg)
        score += time_score * 0.2
        if time_score > 10:
            reasons.append("关键时间窗口")
        
        # 4. 回补状态（10%权重）
        mitigation_score = self._evaluate_mitigation_status(fvg)
        score += mitigation_score * 0.1
        if fvg.is_mitigated:
            reasons.append("已被回补")
        elif fvg.mitigation_percentage > 0:
            reasons.append(f"部分回补({fvg.mitigation_percentage:.1%})")
        
        # 确定信号强度
        if score >= 80:
            strength = ComponentSignalStrength.STRONG
            confidence = 0.8
        elif score >= 65:
            strength = ComponentSignalStrength.MODERATE
            confidence = 0.65
        else:
            strength = ComponentSignalStrength.WEAK
            confidence = 0.5
        
        return {
            'score': min(100.0, score),
            'strength': strength,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def _evaluate_fvg_size(self, fvg: FVG) -> float:
        """评估FVG大小"""
        # 基于相对大小给分
        size_pct = fvg.size_percentage
        
        if size_pct >= 0.005:  # 0.5%以上
            return 30.0
        elif size_pct >= 0.003:  # 0.3%以上
            return 20.0
        elif size_pct >= 0.002:  # 0.2%以上
            return 15.0
        elif size_pct >= 0.001:  # 0.1%以上
            return 10.0
        else:
            return 5.0
    
    def _evaluate_fvg_integrity(self, fvg: FVG) -> float:
        """评估FVG结构完整性"""
        # 简化评估：检查FVG是否清晰且完整
        # 实际应该检查形成FVG的K线是否符合标准模式
        
        # 基础结构完整性
        if fvg.top > fvg.bottom and fvg.size > 0:
            return 25.0
        
        return 10.0
    
    def _evaluate_fvg_timing(self, fvg: FVG) -> float:
        """评估FVG形成时间"""
        # 检查是否在关键时间窗口形成
        hour = fvg.dt.hour
        minute = fvg.dt.minute
        
        score = 5.0  # 基础分数
        
        # 关键小时
        if hour in [9, 10, 13, 14, 15, 21, 22]:  # 重要交易时段
            score += 10.0
        
        # 整点或半点
        if minute in [0, 30]:
            score += 5.0
        
        return score
    
    def _evaluate_mitigation_status(self, fvg: FVG) -> float:
        """评估回补状态"""
        if fvg.is_mitigated:
            # 已完全回补的FVG质量降低
            return -10.0
        elif fvg.mitigation_percentage > 0.5:
            # 回补超过50%
            return -5.0
        elif fvg.mitigation_percentage > 0:
            # 轻微回补
            return 0.0
        else:
            # 未回补
            return 5.0


class OBSignalGenerator(ComponentSignalGenerator):
    """
    OB单体信号生成器
    
    分析单个OB的质量特征，生成质量信号
    """
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def get_signal_types(self) -> List[str]:
        return ['quality']
    
    def generate_component_signals(self, ob: OB) -> List[ComponentSignal]:
        """从单个OB生成质量信号"""
        signals = []
        
        # 生成质量信号
        quality_signal = self._generate_quality_signal(ob)
        if quality_signal:
            signals.append(quality_signal)
        
        return signals
    
    def _generate_quality_signal(self, ob: OB) -> Optional[ComponentSignal]:
        """生成OB质量信号"""
        
        # 使用OB自带的质量评分
        quality_score = ob.quality_score
        
        if quality_score >= 60:  # 最低质量阈值
            # 确定信号强度
            if quality_score >= 85:
                strength = ComponentSignalStrength.STRONG
                confidence = 0.85
            elif quality_score >= 70:
                strength = ComponentSignalStrength.MODERATE
                confidence = 0.7
            else:
                strength = ComponentSignalStrength.WEAK
                confidence = 0.6
            
            # 生成原因列表
            reasons = []
            if ob.related_move_has_fvg:
                reasons.append("后续走势包含FVG")
            if ob.subsequent_move_strength > 0.03:
                reasons.append(f"强劲后续走势({ob.subsequent_move_strength:.1%})")
            if ob.volume_profile.get('volume_multiplier', 1.0) > 1.5:
                reasons.append("成交量异常")
            if not reasons:
                reasons.append("基础订单块结构")
            
            return ComponentSignal(
                component_type='ob',
                component_id=ob.id,
                signal_type='quality',
                strength=strength,
                direction=SignalDirection.BULLISH if ob.direction == OBDirection.BULLISH else SignalDirection.BEARISH,
                score=quality_score,
                confidence=confidence,
                reasons=reasons,
                properties={
                    'ob_size': ob.size,
                    'body_size': ob.body_size,
                    'is_bullish_candle': ob.is_bullish_candle,
                    'mitigation_status': ob.is_mitigated,
                    'subsequent_move_strength': ob.subsequent_move_strength,
                    'related_fvg_count': len(ob.related_fvg_ids)
                },
                created_at=ob.dt,
                expires_at=ob.dt + timedelta(hours=48)  # OB信号有效期48小时
            )
        
        return None