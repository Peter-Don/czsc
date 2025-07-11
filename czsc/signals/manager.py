# -*- coding: utf-8 -*-
"""
信号管理器 - 统一管理所有信号生成和过滤

职责：
1. 协调各个信号生成器
2. 应用信号过滤和排序
3. 提供统一的信号接口
"""

from typing import List, Dict, Any
from datetime import datetime

from czsc.analyze import CZSC
from czsc.signals.base import ComponentSignal, CompositeSignal
from czsc.signals.fractal_signals import FractalComponentSignalGenerator
from czsc.signals.composite import SignalScoringEngine


class SignalManager:
    """
    信号管理器 - 统一管理所有信号生成和过滤
    
    职责：
    1. 协调各个信号生成器
    2. 应用信号过滤和排序
    3. 提供统一的信号接口
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.component_generators = {
            'fractal': FractalComponentSignalGenerator(self.config.get('fractal_config', {}))
        }
        self.scoring_engine = SignalScoringEngine(self.config.get('scoring_config', {}))
        
        # 兼容性设置
        self.legacy_mode = self.config.get('enable_legacy_mode', True)
        self.enable_filtering = self.config.get('enable_signal_filtering', True)
    
    def generate_all_component_signals(self, czsc: CZSC) -> List[ComponentSignal]:
        """生成所有单体信号"""
        all_signals = []
        
        # 从分型生成器获取信号
        if hasattr(czsc, 'fx_list') and czsc.fx_list:
            for fx in czsc.fx_list[-20:]:  # 只处理最近20个分型
                fractal_signals = self.component_generators['fractal'].generate_component_signals(fx)
                all_signals.extend(fractal_signals)
        
        # 应用过滤
        if self.enable_filtering:
            all_signals = self._filter_component_signals(all_signals)
        
        return all_signals
    
    def generate_composite_signals(self, component_signals: List[ComponentSignal]) -> List[CompositeSignal]:
        """生成组合信号"""
        if not component_signals:
            return []
        
        return self.scoring_engine.evaluate_signals(component_signals)
    
    def generate_all_signals(self, czsc: CZSC) -> Dict[str, List]:
        """生成所有类型的信号"""
        # 生成单体信号
        component_signals = self.generate_all_component_signals(czsc)
        
        # 生成组合信号
        composite_signals = self.generate_composite_signals(component_signals)
        
        return {
            'component_signals': component_signals,
            'composite_signals': composite_signals,
            'summary': {
                'component_count': len(component_signals),
                'composite_count': len(composite_signals),
                'generated_at': datetime.now().isoformat()
            }
        }
    
    def get_best_signals(self, czsc: CZSC, limit: int = 3) -> List[CompositeSignal]:
        """获取最佳信号（简化接口）"""
        all_signals = self.generate_all_signals(czsc)
        composite_signals = all_signals['composite_signals']
        
        # 按评分排序并限制数量
        sorted_signals = sorted(composite_signals, 
                              key=lambda s: (s.total_score, s.confidence), 
                              reverse=True)
        
        return sorted_signals[:limit]
    
    def _filter_component_signals(self, signals: List[ComponentSignal]) -> List[ComponentSignal]:
        """过滤单体信号"""
        if not self.enable_filtering:
            return signals
            
        filtered = []
        expired_count = 0
        low_confidence_count = 0
        duplicate_count = 0
        
        for signal in signals:
            # 过滤低置信度信号（调低阈值）
            if signal.confidence < 0.2:
                low_confidence_count += 1
                continue
            
            # 过滤过期信号
            if self._is_signal_expired(signal):
                expired_count += 1
                continue
            
            # 过滤重复信号
            if not self._is_duplicate_signal(signal, filtered):
                filtered.append(signal)
            else:
                duplicate_count += 1
        
        return filtered
    
    def _is_signal_expired(self, signal: ComponentSignal) -> bool:
        """检查信号是否过期"""
        return not signal.is_valid()
    
    def _is_duplicate_signal(self, signal: ComponentSignal, existing_signals: List[ComponentSignal]) -> bool:
        """检查是否为重复信号"""
        for existing in existing_signals:
            if (signal.component_id == existing.component_id and 
                signal.signal_type == existing.signal_type):
                return True
        return False
    
    def add_component_generator(self, name: str, generator):
        """添加组件信号生成器"""
        self.component_generators[name] = generator
    
    def set_scoring_config(self, config: Dict[str, Any]):
        """设置评分配置"""
        self.scoring_engine.config.update(config)
    
    def get_signal_statistics(self, czsc: CZSC) -> Dict[str, Any]:
        """获取信号统计信息"""
        all_signals = self.generate_all_signals(czsc)
        component_signals = all_signals['component_signals']
        composite_signals = all_signals['composite_signals']
        
        # 单体信号统计
        component_stats = {}
        for signal in component_signals:
            signal_type = signal.signal_type
            if signal_type not in component_stats:
                component_stats[signal_type] = {'count': 0, 'strengths': {}}
            
            component_stats[signal_type]['count'] += 1
            strength = signal.strength.name
            if strength not in component_stats[signal_type]['strengths']:
                component_stats[signal_type]['strengths'][strength] = 0
            component_stats[signal_type]['strengths'][strength] += 1
        
        # 组合信号统计
        composite_stats = {}
        for signal in composite_signals:
            strength = signal.strength.value
            if strength not in composite_stats:
                composite_stats[strength] = 0
            composite_stats[strength] += 1
        
        return {
            'component_signals': {
                'total': len(component_signals),
                'by_type': component_stats
            },
            'composite_signals': {
                'total': len(composite_signals),
                'by_strength': composite_stats
            },
            'quality_metrics': {
                'avg_component_confidence': sum(s.confidence for s in component_signals) / len(component_signals) if component_signals else 0,
                'avg_composite_score': sum(s.total_score for s in composite_signals) / len(composite_signals) if composite_signals else 0,
                'high_quality_signals': len([s for s in composite_signals if s.total_score >= 200 and s.confidence >= 0.7])
            }
        }