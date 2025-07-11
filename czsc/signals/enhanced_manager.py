# -*- coding: utf-8 -*-
"""
增强信号管理器 - 整合缠论几何组件与机构足迹组件

基于CZSC分析结果，统一管理：
- 缠论几何组件：分型(FX)、笔(BI) - 来自原CZSC
- 机构足迹组件：FVG、OB - 基于包含处理后的K线检测
"""

from typing import List, Dict, Any
from datetime import datetime

from czsc.analyze import CZSC
from czsc.components.detectors import FVGDetector, OBDetector
from czsc.components.institutional import FVG, OB
from czsc.signals.base import ComponentSignal, CompositeSignal
from czsc.signals.fractal_signals import FractalComponentSignalGenerator
from czsc.signals.institutional_signals import FVGSignalGenerator, OBSignalGenerator
from czsc.signals.composite import SignalScoringEngine


class EnhancedSignalManager:
    """
    增强信号管理器
    
    整合缠论几何分析与机构足迹分析的完整信号系统
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 组件检测器
        self.fvg_detector = FVGDetector(
            min_gap_size=self.config.get('fvg_min_gap_size', 0.001)
        )
        self.ob_detector = OBDetector(
            min_move_strength=self.config.get('ob_min_move_strength', 0.02),
            require_fvg=self.config.get('ob_require_fvg', True)
        )
        
        # 单体信号生成器
        self.component_generators = {
            'fractal': FractalComponentSignalGenerator(self.config.get('fractal_config', {})),
            'fvg': FVGSignalGenerator(self.config.get('fvg_config', {})),
            'ob': OBSignalGenerator(self.config.get('ob_config', {}))
        }
        
        # 组合信号评分引擎
        self.scoring_engine = SignalScoringEngine(self.config.get('scoring_config', {}))
        
        # 兼容性设置
        self.legacy_mode = self.config.get('enable_legacy_mode', True)
        self.enable_filtering = self.config.get('enable_signal_filtering', True)
    
    def analyze_market_structure(self, czsc: CZSC) -> Dict[str, Any]:
        """
        全面分析市场结构
        
        Args:
            czsc: CZSC分析对象（包含包含处理后的K线和分型、笔）
            
        Returns:
            完整的市场结构分析结果
        """
        
        # 1. 检测机构足迹组件（基于包含处理后的K线）
        fvgs = self.fvg_detector.detect_fvgs(czsc.bars_ubi)  # 使用包含处理后的K线
        obs = self.ob_detector.detect_obs(czsc.bars_ubi, fvgs)
        
        # 2. 更新组件状态
        if czsc.bars_ubi:
            self.fvg_detector.update_fvg_mitigation(fvgs, czsc.bars_ubi)
            self.ob_detector.update_ob_mitigation(obs, czsc.bars_ubi)
        
        return {
            'geometric_components': {
                'fractals': czsc.fx_list or [],
                'strokes': czsc.bi_list or []
            },
            'institutional_components': {
                'fvgs': fvgs,
                'obs': obs
            },
            'analysis_time': datetime.now().isoformat()
        }
    
    def generate_all_component_signals(self, czsc: CZSC) -> List[ComponentSignal]:
        """生成所有单体信号"""
        all_signals = []
        
        # 分析市场结构
        market_structure = self.analyze_market_structure(czsc)
        
        # 1. 从缠论几何组件生成信号
        fractals = market_structure['geometric_components']['fractals']
        if fractals:
            for fx in fractals[-20:]:  # 处理最近20个分型
                fractal_signals = self.component_generators['fractal'].generate_component_signals(fx)
                all_signals.extend(fractal_signals)
        
        # 2. 从FVG组件生成信号
        fvgs = market_structure['institutional_components']['fvgs']
        if fvgs:
            for fvg in fvgs[-10:]:  # 处理最近10个FVG
                fvg_signals = self.component_generators['fvg'].generate_component_signals(fvg)
                all_signals.extend(fvg_signals)
        
        # 3. 从OB组件生成信号
        obs = market_structure['institutional_components']['obs']
        if obs:
            for ob in obs[-10:]:  # 处理最近10个OB
                ob_signals = self.component_generators['ob'].generate_component_signals(ob)
                all_signals.extend(ob_signals)
        
        # 应用过滤
        if self.enable_filtering:
            all_signals = self._filter_component_signals(all_signals)
        
        return all_signals
    
    def generate_composite_signals(self, component_signals: List[ComponentSignal]) -> List[CompositeSignal]:
        """生成组合信号"""
        if not component_signals:
            return []
        
        return self.scoring_engine.evaluate_signals(component_signals)
    
    def generate_all_signals(self, czsc: CZSC) -> Dict[str, Any]:
        """生成所有类型的信号"""
        
        # 分析市场结构
        market_structure = self.analyze_market_structure(czsc)
        
        # 生成单体信号
        component_signals = self.generate_all_component_signals(czsc)
        
        # 生成组合信号
        composite_signals = self.generate_composite_signals(component_signals)
        
        return {
            'market_structure': market_structure,
            'component_signals': component_signals,
            'composite_signals': composite_signals,
            'summary': {
                'fractal_count': len(market_structure['geometric_components']['fractals']),
                'stroke_count': len(market_structure['geometric_components']['strokes']),
                'fvg_count': len(market_structure['institutional_components']['fvgs']),
                'ob_count': len(market_structure['institutional_components']['obs']),
                'component_signal_count': len(component_signals),
                'composite_signal_count': len(composite_signals),
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
        for signal in signals:
            # 过滤低置信度信号
            if signal.confidence < 0.2:
                continue
            
            # 过滤过期信号
            if not signal.is_valid():
                continue
            
            # 过滤重复信号
            if not self._is_duplicate_signal(signal, filtered):
                filtered.append(signal)
        
        return filtered
    
    def _is_duplicate_signal(self, signal: ComponentSignal, existing_signals: List[ComponentSignal]) -> bool:
        """检查是否为重复信号"""
        for existing in existing_signals:
            if (signal.component_id == existing.component_id and 
                signal.signal_type == existing.signal_type):
                return True
        return False
    
    def get_market_overview(self, czsc: CZSC) -> Dict[str, Any]:
        """获取市场概览"""
        market_structure = self.analyze_market_structure(czsc)
        
        # 统计各类组件
        fractal_count = len(market_structure['geometric_components']['fractals'])
        stroke_count = len(market_structure['geometric_components']['strokes'])
        fvg_count = len(market_structure['institutional_components']['fvgs'])
        ob_count = len(market_structure['institutional_components']['obs'])
        
        # 分析FVG状态
        fvgs = market_structure['institutional_components']['fvgs']
        active_fvgs = [fvg for fvg in fvgs if not fvg.is_mitigated]
        
        # 分析OB状态
        obs = market_structure['institutional_components']['obs']
        active_obs = [ob for ob in obs if not ob.is_mitigated]
        
        return {
            'structure_overview': {
                'geometric': {
                    'fractal_count': fractal_count,
                    'stroke_count': stroke_count
                },
                'institutional': {
                    'fvg_total': fvg_count,
                    'fvg_active': len(active_fvgs),
                    'ob_total': ob_count,
                    'ob_active': len(active_obs)
                }
            },
            'current_focus_areas': {
                'active_fvgs': [
                    {
                        'id': fvg.id,
                        'direction': fvg.direction.value,
                        'size_pct': f"{fvg.size_percentage:.3%}",
                        'top': fvg.top,
                        'bottom': fvg.bottom
                    }
                    for fvg in active_fvgs[-5:]  # 最近5个活跃FVG
                ],
                'active_obs': [
                    {
                        'id': ob.id,
                        'direction': ob.direction.value,
                        'quality_score': f"{ob.quality_score:.1f}",
                        'top': ob.top,
                        'bottom': ob.bottom
                    }
                    for ob in active_obs[-5:]  # 最近5个活跃OB
                ]
            },
            'analysis_timestamp': datetime.now().isoformat()
        }