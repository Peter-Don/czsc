# -*- coding: utf-8 -*-
"""
组合信号层 - 多个单体信号组合的最终交易信号
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta

from czsc.signals.base import (
    ComponentSignal, CompositeSignal, CompositeSignalStrength, 
    SignalDirection, SignalNecessity, SignalWeight, CompositeSignalRule
)


class SignalScoringEngine:
    """
    信号评分引擎 - 实现复杂的评分、权重、排序逻辑
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.rules = self._load_signal_rules()
    
    def evaluate_signals(self, component_signals: List[ComponentSignal]) -> List[CompositeSignal]:
        """评估所有组合信号可能性"""
        composite_signals = []
        
        # 按规则逐一评估
        for rule in self.rules:
            signal = self._evaluate_rule(rule, component_signals)
            if signal:
                composite_signals.append(signal)
        
        # 排序和过滤
        return self._rank_and_filter(composite_signals)
    
    def _load_signal_rules(self) -> List[CompositeSignalRule]:
        """加载信号规则"""
        rules = [
            self._get_fractal_reversal_rule(),
            self._get_fractal_confluence_rule()
        ]
        
        # 加载高级规则
        try:
            from czsc.signals.advanced_rules import get_all_advanced_rules
            advanced_rules = get_all_advanced_rules()
            rules.extend(advanced_rules)
        except ImportError:
            pass  # 如果高级规则模块不可用，继续使用基础规则
        
        return rules
    
    def _get_fractal_reversal_rule(self) -> CompositeSignalRule:
        """分型反转信号规则"""
        return CompositeSignalRule(
            name="分型反转信号",
            description="基于分型的反转交易信号",
            required_signals=[],                 # 不强制要求任何信号
            optional_signals=["power", "position", "timing", "volume"],
            weights=[
                SignalWeight("power", 0.4, SignalNecessity.OPTIONAL, {
                    "strong_power": 1.2,         # 强力度时权重x1.2
                    "multiple_fractals": 1.1     # 多分型汇聚时权重x1.1
                }),
                SignalWeight("position", 0.3, SignalNecessity.PREFERRED, {
                    "key_level": 1.5,            # 关键位置权重x1.5
                    "htf_poi": 1.3               # HTF POI区域权重x1.3
                }),
                SignalWeight("timing", 0.2, SignalNecessity.OPTIONAL, {
                    "market_open": 1.2,          # 开盘时间权重x1.2
                    "news_event": 0.8            # 新闻事件时间权重x0.8
                }),
                SignalWeight("volume", 0.1, SignalNecessity.OPTIONAL, {
                    "volume_spike": 1.4,         # 成交量激增权重x1.4
                    "volume_dry": 0.9            # 成交量枯竭权重x0.9
                })
            ],
            min_score=30,                        # 最低30分
            min_confidence=0.4                   # 最低40%置信度
        )
    
    def _get_fractal_confluence_rule(self) -> CompositeSignalRule:
        """分型汇聚信号规则"""
        return CompositeSignalRule(
            name="分型汇聚信号",
            description="多个分型汇聚的强势信号",
            required_signals=[],
            optional_signals=["power", "position", "timing"],
            weights=[
                SignalWeight("power", 0.5, SignalNecessity.OPTIONAL, {
                    "very_strong": 1.5
                }),
                SignalWeight("position", 0.4, SignalNecessity.OPTIONAL, {
                    "confluence_zone": 1.3
                }),
                SignalWeight("timing", 0.1, SignalNecessity.OPTIONAL, {
                    "perfect_timing": 1.2
                })
            ],
            min_score=20,
            min_confidence=0.5
        )
    
    def _evaluate_rule(self, rule: CompositeSignalRule, signals: List[ComponentSignal]) -> Optional[CompositeSignal]:
        """评估单个规则"""
        # 1. 检查必要信号
        required_signals = self._find_required_signals(rule, signals)
        if not self._check_required_signals(rule, required_signals):
            return None
        
        # 2. 收集所有相关信号
        relevant_signals = self._find_relevant_signals(rule, signals)
        
        # 3. 计算评分
        score_result = self._calculate_composite_score(rule, relevant_signals)
        
        # 4. 检查阈值
        if (score_result['total_score'] < rule.min_score or 
            score_result['confidence'] < rule.min_confidence):
            return None
        
        # 5. 生成组合信号
        return CompositeSignal(
            name=rule.name,
            rule_name=rule.name,
            strength=self._score_to_strength(score_result['total_score']),
            direction=self._determine_direction(relevant_signals),
            total_score=score_result['total_score'],
            confidence=score_result['confidence'],
            component_signals=relevant_signals,
            signal_breakdown=score_result['breakdown'],
            weights_applied=score_result['weights'],
            created_at=datetime.now(),
            expires_at=self._calculate_expiry(relevant_signals),
            priority=self._calculate_priority(score_result)
        )
    
    def _find_required_signals(self, rule: CompositeSignalRule, signals: List[ComponentSignal]) -> List[ComponentSignal]:
        """查找必要信号"""
        required = []
        for signal_type in rule.required_signals:
            matching = [s for s in signals if s.signal_type == signal_type]
            if matching:
                required.extend(matching)
        return required
    
    def _check_required_signals(self, rule: CompositeSignalRule, required_signals: List[ComponentSignal]) -> bool:
        """检查必要信号是否满足"""
        found_types = set(s.signal_type for s in required_signals)
        return all(signal_type in found_types for signal_type in rule.required_signals)
    
    def _find_relevant_signals(self, rule: CompositeSignalRule, signals: List[ComponentSignal]) -> List[ComponentSignal]:
        """查找所有相关信号"""
        all_types = rule.required_signals + rule.optional_signals
        return [s for s in signals if s.signal_type in all_types]
    
    def _calculate_composite_score(self, rule: CompositeSignalRule, signals: List[ComponentSignal]) -> Dict:
        """计算组合信号评分"""
        total_score = 0.0
        confidence_sum = 0.0
        weight_sum = 0.0
        breakdown = {}
        weights_applied = {}
        
        for weight_config in rule.weights:
            # 找到匹配的信号
            matching_signals = [s for s in signals if s.signal_type == weight_config.signal_type]
            
            if not matching_signals:
                # 检查是否必须
                if weight_config.necessity == SignalNecessity.REQUIRED:
                    return {'total_score': 0, 'confidence': 0, 'breakdown': {}, 'weights': {}}
                continue
            
            # 取最好的信号
            best_signal = max(matching_signals, key=lambda s: s.score)
            
            # 计算有效权重
            effective_weight = self._calculate_effective_weight(weight_config, best_signal, signals)
            
            # 计算贡献分数
            contribution = best_signal.score * effective_weight
            total_score += contribution
            confidence_sum += best_signal.confidence * effective_weight
            weight_sum += effective_weight
            
            # 记录分解
            breakdown[weight_config.signal_type] = {
                'signal': best_signal,
                'base_score': best_signal.score,
                'weight': effective_weight,
                'contribution': contribution
            }
            weights_applied[weight_config.signal_type] = effective_weight
        
        # 计算最终置信度
        final_confidence = confidence_sum / weight_sum if weight_sum > 0 else 0
        
        return {
            'total_score': total_score,
            'confidence': final_confidence,
            'breakdown': breakdown,
            'weights': weights_applied
        }
    
    def _calculate_effective_weight(self, weight_config: SignalWeight, signal: ComponentSignal, all_signals: List[ComponentSignal]) -> float:
        """计算有效权重 - 考虑动态调整因素"""
        base_weight = weight_config.base_weight
        
        # 应用乘数条件
        for condition, multiplier in weight_config.multiplier_conditions.items():
            if self._check_condition(condition, signal, all_signals):
                base_weight *= multiplier
        
        # 必要性加权
        necessity_multiplier = {
            SignalNecessity.OPTIONAL: 0.8,
            SignalNecessity.PREFERRED: 1.0,
            SignalNecessity.REQUIRED: 1.2,
            SignalNecessity.CRITICAL: 1.5
        }
        
        return base_weight * necessity_multiplier[weight_config.necessity]
    
    def _check_condition(self, condition: str, signal: ComponentSignal, all_signals: List[ComponentSignal]) -> bool:
        """检查条件是否满足"""
        if condition == "strong_power":
            return signal.strength.value >= 3  # STRONG或以上
        elif condition == "multiple_fractals":
            return len([s for s in all_signals if s.component_type == 'fractal']) > 1
        # 其他条件可以继续添加
        return False
    
    def _score_to_strength(self, score: float) -> CompositeSignalStrength:
        """将评分转换为信号强度"""
        if score >= 300:
            return CompositeSignalStrength.CRITICAL
        elif score >= 250:
            return CompositeSignalStrength.VERY_STRONG
        elif score >= 200:
            return CompositeSignalStrength.STRONG
        elif score >= 150:
            return CompositeSignalStrength.MODERATE
        else:
            return CompositeSignalStrength.WEAK
    
    def _determine_direction(self, signals: List[ComponentSignal]) -> SignalDirection:
        """确定信号方向"""
        bullish_count = sum(1 for s in signals if s.direction == SignalDirection.BULLISH)
        bearish_count = sum(1 for s in signals if s.direction == SignalDirection.BEARISH)
        
        if bullish_count > bearish_count:
            return SignalDirection.BULLISH
        elif bearish_count > bullish_count:
            return SignalDirection.BEARISH
        else:
            return SignalDirection.NEUTRAL
    
    def _calculate_expiry(self, signals: List[ComponentSignal]) -> datetime:
        """计算组合信号过期时间"""
        if not signals:
            return datetime.now() + timedelta(hours=1)
        
        # 取最短过期时间
        expiry_times = [s.expires_at for s in signals if s.expires_at]
        if expiry_times:
            return min(expiry_times)
        else:
            return datetime.now() + timedelta(hours=2)
    
    def _calculate_priority(self, score_result: Dict) -> int:
        """计算优先级"""
        score = score_result['total_score']
        confidence = score_result['confidence']
        
        # 综合评分和置信度
        priority = int(score * confidence)
        return max(0, min(1000, priority))  # 限制在0-1000范围
    
    def _rank_and_filter(self, signals: List[CompositeSignal]) -> List[CompositeSignal]:
        """排序和过滤组合信号"""
        if not signals:
            return []
        
        # 1. 去重 - 相似信号只保留最佳
        unique_signals = self._remove_duplicates(signals)
        
        # 2. 多维度排序
        ranked_signals = sorted(unique_signals, key=lambda s: (
            s.priority,                    # 优先级
            s.total_score,                 # 总评分
            s.confidence,                  # 置信度
            len(s.component_signals),      # 信号数量
            -s.created_at.timestamp()      # 时间新鲜度
        ), reverse=True)
        
        # 3. 过滤 - 只保留高质量信号
        min_score = self.config.get('min_composite_score', 20)  # 降低默认阈值
        min_confidence = self.config.get('min_composite_confidence', 0.3)  # 降低默认阈值
        
        filtered_signals = [
            s for s in ranked_signals 
            if s.total_score >= min_score and s.confidence >= min_confidence
        ]
        
        
        # 4. 限制数量
        max_signals = self.config.get('max_signals_per_timeframe', 5)
        return filtered_signals[:max_signals]
    
    def _remove_duplicates(self, signals: List[CompositeSignal]) -> List[CompositeSignal]:
        """去除重复信号"""
        # 简化实现：按名称去重，保留评分最高的
        unique_map = {}
        for signal in signals:
            key = signal.name
            if key not in unique_map or signal.total_score > unique_map[key].total_score:
                unique_map[key] = signal
        
        return list(unique_map.values())