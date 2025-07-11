# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2024/12/28
describe: FVG (Fair Value Gap) 公允价值缺口
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from ..objects import NewBar, FX
from ..enum import Direction, Mark
from ..utils.ta import ATR


@dataclass
class FVG:
    """Fair Value Gap 公允价值缺口"""
    symbol: str
    dt: datetime
    direction: Direction
    
    # 构成FVG的三根K线
    bar1: NewBar
    bar2: NewBar
    bar3: NewBar
    
    # FVG边界
    high: float
    low: float
    
    # 状态
    is_valid: bool = True
    is_tested: bool = False
    is_mitigated: bool = False
    
    # 缓解程度
    mitigation_level: float = 0.0
    mitigation_threshold: float = 0.5
    
    # 交互历史
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 评分
    score: float = 0.0
    
    # 缓存
    cache: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 设置基本信息
        self.symbol = self.bar1.symbol
        self.dt = self.bar2.dt
        
        # 根据方向设置FVG边界
        if self.direction == Direction.Up:
            # 看涨FVG：bar1的高点到bar3的低点之间的空隙
            self.high = self.bar3.low
            self.low = self.bar1.high
        else:
            # 看跌FVG：bar3的高点到bar1的低点之间的空隙
            self.high = self.bar1.low
            self.low = self.bar3.high
        
        # 确保高低点顺序正确
        if self.high < self.low:
            self.high, self.low = self.low, self.high
    
    @property
    def size(self) -> float:
        """FVG大小"""
        return abs(self.high - self.low)
    
    @property
    def center(self) -> float:
        """FVG中心价格"""
        return (self.high + self.low) / 2.0
    
    @property
    def strength(self) -> float:
        """FVG强度"""
        # 基于bar2的实体大小和成交量计算强度
        body_size = abs(self.bar2.close - self.bar2.open)
        bar_range = self.bar2.high - self.bar2.low
        
        if bar_range == 0:
            return 0.0
            
        body_ratio = body_size / bar_range
        volume_factor = self.bar2.vol / max(self.bar1.vol, self.bar3.vol, 1)
        
        return body_ratio * volume_factor
    
    @property
    def relative_size(self) -> float:
        """相对大小（相对于bar2的范围）"""
        bar2_range = self.bar2.high - self.bar2.low
        if bar2_range == 0:
            return 0.0
        return self.size / bar2_range
    
    def contains(self, price: float) -> bool:
        """判断价格是否在FVG范围内"""
        return self.low <= price <= self.high
    
    def distance_to(self, price: float) -> float:
        """计算价格到FVG的距离"""
        if price > self.high:
            return price - self.high
        elif price < self.low:
            return self.low - price
        else:
            return 0.0
    
    def is_bullish_fvg(self) -> bool:
        """判断是否为看涨FVG"""
        return self.direction == Direction.Up
    
    def is_bearish_fvg(self) -> bool:
        """判断是否为看跌FVG"""
        return self.direction == Direction.Down
    
    def get_mitigation_type(self) -> str:
        """获取缓解类型
        
        Returns:
            缓解类型：NONE, PARTIAL, SIGNIFICANT, COMPLETE, OVERSHOOT
        """
        if self.mitigation_level < 0.25:
            return "NONE"  # 无缓解
        elif self.mitigation_level < 0.5:
            return "PARTIAL"  # 部分缓解
        elif self.mitigation_level < 0.9:
            return "SIGNIFICANT"  # 显著缓解
        elif self.mitigation_level < 1.5:
            return "COMPLETE"  # 完全缓解
        else:
            return "OVERSHOOT"  # 完全被穿透（≥150%）
    
    def get_mitigation_description(self) -> str:
        """获取缓解程度的描述"""
        mitigation_type = self.get_mitigation_type()
        descriptions = {
            "NONE": f"无缓解({self.mitigation_level:.1%})",
            "PARTIAL": f"部分缓解({self.mitigation_level:.1%})",
            "SIGNIFICANT": f"显著缓解({self.mitigation_level:.1%})",
            "COMPLETE": f"完全缓解({self.mitigation_level:.1%})",
            "OVERSHOOT": f"完全被穿透({self.mitigation_level:.1%})"
        }
        return descriptions.get(mitigation_type, f"未知类型({self.mitigation_level:.1%})")
    
    def is_effective_for_trading(self) -> bool:
        """判断FVG是否仍具有交易价值"""
        return self.mitigation_level < 0.7  # 缓解程度<70%时仍具有交易价值
    
    def update_mitigation(self, price: float, dt: datetime) -> bool:
        """更新缓解状态"""
        old_mitigation = self.mitigation_level
        old_tested = self.is_tested
        
        # 计算当前缓解程度（支持超调穿透）
        if self.direction == Direction.Up:
            # 看涨FVG，价格从上往下进入
            if price <= self.high:
                if price >= self.low:
                    # 在FVG范围内
                    current_mitigation = (self.high - price) / self.size
                else:
                    # 完全穿透FVG下边界
                    current_mitigation = 1.0 + (self.low - price) / self.size  # 超过100%
            else:
                current_mitigation = 0.0
        else:
            # 看跌FVG，价格从下往上进入
            if price >= self.low:
                if price <= self.high:
                    # 在FVG范围内
                    current_mitigation = (price - self.low) / self.size
                else:
                    # 完全穿透FVG上边界
                    current_mitigation = 1.0 + (price - self.high) / self.size  # 超过100%
            else:
                current_mitigation = 0.0
        
        current_mitigation = max(0.0, current_mitigation)  # 不限制上限，支持超调
        
        # 更新最大缓解程度
        self.mitigation_level = max(self.mitigation_level, current_mitigation)
        
        # 更新测试状态
        if current_mitigation > 0 and not self.is_tested:
            self.is_tested = True
            
            # 记录交互历史
            self.interaction_history.append({
                'dt': dt,
                'type': 'first_test',
                'price': price,
                'mitigation_level': self.mitigation_level
            })
        
        # 检查是否达到缓解阈值
        if self.mitigation_level >= self.mitigation_threshold and not self.is_mitigated:
            self.is_mitigated = True
            
            # 记录缓解事件
            self.interaction_history.append({
                'dt': dt,
                'type': 'mitigated',
                'price': price,
                'mitigation_level': self.mitigation_level
            })
        
        return old_mitigation != self.mitigation_level or old_tested != self.is_tested
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'dt': self.dt.isoformat(),
            'direction': self.direction.value,
            'high': self.high,
            'low': self.low,
            'size': self.size,
            'center': self.center,
            'strength': self.strength,
            'relative_size': self.relative_size,
            'is_valid': self.is_valid,
            'is_tested': self.is_tested,
            'is_mitigated': self.is_mitigated,
            'mitigation_level': self.mitigation_level,
            'score': self.score,
            'interaction_count': len(self.interaction_history)
        }
    
    def __repr__(self):
        direction_str = "Bullish" if self.direction == Direction.Up else "Bearish"
        status = "Mitigated" if self.is_mitigated else f"Active({self.mitigation_level:.1%})"
        return f"FVG({direction_str}, {self.symbol}, {self.dt.strftime('%Y-%m-%d %H:%M')}, " \
               f"[{self.low:.4f}, {self.high:.4f}], {status})"


# ============================================================================
# 第一阶段：识别层 - 纯客观几何条件
# ============================================================================

def identify_fvg_basic(bars: List[NewBar], min_size_atr_factor: float = 0.3, 
                      atr_period: int = 14) -> List[FVG]:
    """
    第一阶段：基础FVG识别（纯几何条件）
    
    职责：
    - 基于CZSC处理后的K线进行纯几何识别
    - 只应用最基础的过滤条件（如ATR大小过滤）
    - 不考虑任何上下文信息
    
    Args:
        bars: CZSC包含处理后的K线列表（NewBar）
        min_size_atr_factor: 最小FVG大小与ATR的比例（基础过滤）
        atr_period: ATR计算周期
        
    Returns:
        识别到的基础FVG列表（未评分）
    """
    if len(bars) < 3:
        return []
    
    fvgs = []
    
    # 计算ATR（用于基础大小过滤）
    if len(bars) >= atr_period:
        df = pd.DataFrame([{
            'high': bar.high,
            'low': bar.low,
            'close': bar.close
        } for bar in bars])
        atr_values = ATR(df['high'], df['low'], df['close'], timeperiod=atr_period)
        current_atr = atr_values.iloc[-1] if not pd.isna(atr_values.iloc[-1]) else 0.0
    else:
        # 简单估算ATR
        current_atr = np.mean([bar.high - bar.low for bar in bars])
    
    min_gap_size = current_atr * min_size_atr_factor
    
    # 纯几何FVG识别
    for i in range(len(bars) - 2):
        bar1, bar2, bar3 = bars[i], bars[i + 1], bars[i + 2]
        
        # 看涨FVG识别（严格定义）
        if bar1.high < bar3.low:
            gap_size = bar3.low - bar1.high
            if gap_size >= min_gap_size:
                fvg = FVG(
                    symbol=bar1.symbol,
                    dt=bar2.dt,
                    direction=Direction.Up,
                    bar1=bar1,
                    bar2=bar2,
                    bar3=bar3,
                    high=bar3.low,
                    low=bar1.high
                )
                # 记录识别信息
                fvg.cache['stage'] = 'IDENTIFIED'
                fvg.cache['gap_to_atr_ratio'] = gap_size / current_atr if current_atr > 0 else 0
                fvg.cache['identification_timestamp'] = bars[-1].dt
                fvgs.append(fvg)
        
        # 看跌FVG识别（严格定义）
        elif bar1.low > bar3.high:
            gap_size = bar1.low - bar3.high
            if gap_size >= min_gap_size:
                fvg = FVG(
                    symbol=bar1.symbol,
                    dt=bar2.dt,
                    direction=Direction.Down,
                    bar1=bar1,
                    bar2=bar2,
                    bar3=bar3,
                    high=bar1.low,
                    low=bar3.high
                )
                # 记录识别信息
                fvg.cache['stage'] = 'IDENTIFIED'
                fvg.cache['gap_to_atr_ratio'] = gap_size / current_atr if current_atr > 0 else 0
                fvg.cache['identification_timestamp'] = bars[-1].dt
                fvgs.append(fvg)
    
    return fvgs


# ============================================================================
# 第二阶段：分析层 - 质量评分与上下文分析
# ============================================================================

class FVGAnalyzer:
    """FVG分析器 - 第二阶段质量评分与上下文分析"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化FVG分析器
        
        Args:
            config: 分析配置参数
        """
        self.config = config or {}
        self.fractal_proximity_weight = self.config.get('fractal_proximity_weight', 0.2)
        self.stroke_context_weight = self.config.get('stroke_context_weight', 0.3)
        self.volume_analysis_weight = self.config.get('volume_analysis_weight', 0.2)
        self.atr_significance_weight = self.config.get('atr_significance_weight', 0.1)
        self.base_score = self.config.get('base_score', 0.5)
    
    def analyze_fvg_quality(self, identified_fvgs: List[FVG], czsc_context: Optional[Dict] = None) -> List[FVG]:
        """
        第二阶段：FVG质量分析与评分
        
        职责：
        - 对已识别的FVG进行质量评分
        - 考虑缠论结构上下文（分型、笔等）
        - 分析成交量、时间等因素
        - 生成综合质量评分
        
        Args:
            identified_fvgs: 第一阶段识别的FVG列表
            czsc_context: 缠论结构上下文信息
                {
                    'fractals': List[FX],  # 分型列表
                    'strokes': List[BI],   # 笔列表  
                    'bars': List[NewBar],  # K线列表
                    'timestamp': datetime  # 分析时间戳
                }
                
        Returns:
            分析后的FVG列表（包含质量评分）
        """
        if not identified_fvgs:
            return []
        
        analyzed_fvgs = []
        
        for fvg in identified_fvgs:
            # 初始化分析结果
            analysis_result = {
                'quality_score': self.base_score,
                'analysis_factors': {},
                'recommendations': [],
                'confidence_level': 'LOW'
            }
            
            if czsc_context:
                # 分型邻近性分析
                if 'fractals' in czsc_context:
                    fractal_analysis = self._analyze_fractal_proximity(fvg, czsc_context['fractals'])
                    if fractal_analysis['significance'] > 0:
                        analysis_result['quality_score'] += self.fractal_proximity_weight * fractal_analysis['significance']
                        analysis_result['analysis_factors']['fractal_proximity'] = fractal_analysis
                
                # 笔上下文分析
                if 'strokes' in czsc_context:
                    stroke_analysis = self._analyze_stroke_context(fvg, czsc_context['strokes'])
                    if stroke_analysis['relevance'] > 0:
                        analysis_result['quality_score'] += self.stroke_context_weight * stroke_analysis['relevance']
                        analysis_result['analysis_factors']['stroke_context'] = stroke_analysis
                
                # 成交量上下文分析
                if 'bars' in czsc_context:
                    volume_analysis = self._analyze_volume_characteristics(fvg, czsc_context['bars'])
                    if volume_analysis['strength'] > 0:
                        analysis_result['quality_score'] += self.volume_analysis_weight * volume_analysis['strength']
                        analysis_result['analysis_factors']['volume_analysis'] = volume_analysis
            
            # ATR显著性分析
            atr_analysis = self._analyze_atr_significance(fvg)
            if atr_analysis['significance'] > 0:
                analysis_result['quality_score'] += self.atr_significance_weight * atr_analysis['significance']
                analysis_result['analysis_factors']['atr_significance'] = atr_analysis
            
            # 确定置信度水平
            analysis_result['confidence_level'] = self._determine_confidence_level(analysis_result['quality_score'])
            
            # 生成建议
            analysis_result['recommendations'] = self._generate_recommendations(analysis_result)
            
            # 更新FVG对象
            fvg.cache['stage'] = 'ANALYZED'
            fvg.cache['analysis_result'] = analysis_result
            fvg.cache['analysis_timestamp'] = czsc_context.get('timestamp') if czsc_context else None
            fvg.score = min(1.0, analysis_result['quality_score'])
            
            analyzed_fvgs.append(fvg)
        
        return analyzed_fvgs
    
    def _analyze_fractal_proximity(self, fvg: FVG, fractals: List[FX]) -> dict:
        """分析FVG与分型的邻近性"""
        max_significance = 0.0
        related_fractal = None
        
        for fx in fractals:
            # 计算时间距离（分钟）
            time_diff = abs((fvg.dt - fx.dt).total_seconds() / 60)
            
            # 邻近性评分（距离越近评分越高）
            if time_diff <= 3:  # 3分钟内
                significance = 1.0 - (time_diff / 3.0)  # 0到1之间
                if significance > max_significance:
                    max_significance = significance
                    related_fractal = fx
        
        return {
            'significance': max_significance,
            'related_fractal': related_fractal,
            'analysis_note': f"最近分型距离{time_diff:.1f}分钟" if related_fractal else "无邻近分型"
        }
    
    def _analyze_stroke_context(self, fvg: FVG, strokes: List) -> dict:
        """分析FVG的笔上下文"""
        containing_stroke = None
        relevance = 0.0
        
        for stroke in strokes:
            if hasattr(stroke, 'fx_a') and hasattr(stroke, 'fx_b'):
                if stroke.fx_a.dt <= fvg.dt <= stroke.fx_b.dt:
                    containing_stroke = stroke
                    # 根据笔的方向和FVG方向的一致性评分
                    if stroke.direction == fvg.direction:
                        relevance = 1.0  # 方向一致，高相关性
                    else:
                        relevance = 0.6  # 方向不一致，中等相关性
                    break
        
        return {
            'relevance': relevance,
            'containing_stroke': containing_stroke,
            'analysis_note': f"位于{stroke.direction.value}笔内" if containing_stroke else "未在笔结构内"
        }
    
    def _analyze_volume_characteristics(self, fvg: FVG, bars: List[NewBar]) -> dict:
        """分析FVG的成交量特征"""
        # 找到FVG在K线序列中的位置
        fvg_index = None
        for i, bar in enumerate(bars):
            if bar.dt == fvg.dt:
                fvg_index = i
                break
        
        if fvg_index is None or fvg_index < 20:
            return {'strength': 0.0, 'analysis_note': "无足够历史数据"}
        
        # 计算成交量特征
        recent_bars = bars[max(0, fvg_index - 20):fvg_index]
        avg_volume = np.mean([bar.vol for bar in recent_bars])
        center_volume = fvg.bar2.vol
        
        volume_ratio = center_volume / avg_volume if avg_volume > 0 else 0
        
        # 成交量强度评分
        if volume_ratio > 2.0:
            strength = 1.0
        elif volume_ratio > 1.5:
            strength = 0.7
        elif volume_ratio > 1.2:
            strength = 0.4
        else:
            strength = 0.0
        
        return {
            'strength': strength,
            'volume_ratio': volume_ratio,
            'avg_volume': avg_volume,
            'center_volume': center_volume,
            'analysis_note': f"成交量{volume_ratio:.1f}倍于均量"
        }
    
    def _analyze_atr_significance(self, fvg: FVG) -> dict:
        """分析FVG的ATR显著性"""
        gap_to_atr = fvg.cache.get('gap_to_atr_ratio', 0)
        
        if gap_to_atr > 1.0:
            significance = 1.0
        elif gap_to_atr > 0.5:
            significance = 0.7
        elif gap_to_atr > 0.3:
            significance = 0.4
        else:
            significance = 0.0
        
        return {
            'significance': significance,
            'gap_to_atr_ratio': gap_to_atr,
            'analysis_note': f"缺口为{gap_to_atr:.1f}倍ATR"
        }
    
    def _determine_confidence_level(self, quality_score: float) -> str:
        """确定置信度水平"""
        if quality_score >= 0.85:
            return 'VERY_HIGH'
        elif quality_score >= 0.75:
            return 'HIGH'
        elif quality_score >= 0.65:
            return 'MEDIUM'
        elif quality_score >= 0.55:
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    def _generate_recommendations(self, analysis_result: dict) -> List[str]:
        """生成交易建议"""
        recommendations = []
        score = analysis_result['quality_score']
        
        if score >= 0.8:
            recommendations.append("高质量FVG，可考虑作为主要交易信号")
        elif score >= 0.7:
            recommendations.append("中高质量FVG，建议结合其他确认信号")
        elif score >= 0.6:
            recommendations.append("中等质量FVG，谨慎使用，需要额外确认")
        else:
            recommendations.append("低质量FVG，不建议作为主要交易依据")
        
        # 基于分析因素的具体建议
        factors = analysis_result['analysis_factors']
        if 'fractal_proximity' in factors and factors['fractal_proximity']['significance'] > 0.7:
            recommendations.append("邻近关键分型，关注价格反应")
        
        if 'stroke_context' in factors and factors['stroke_context']['relevance'] > 0.8:
            recommendations.append("位于强势笔内，趋势延续概率高")
        
        return recommendations


def _check_fractal_proximity(fvg: FVG, fxs: List[FX], max_distance: int = 3) -> dict:
    """检查FVG与分型的邻近性"""
    for fx in fxs:
        time_diff = abs((fvg.dt - fx.dt).total_seconds() / 60)  # 分钟差
        if time_diff <= max_distance:
            return {
                'is_near': True,
                'related_fractal': fx,
                'distance_minutes': time_diff,
                'fractal_type': fx.mark.value
            }
    
    return {'is_near': False}


def _check_stroke_context(fvg: FVG, bis: List) -> dict:
    """检查FVG的笔上下文"""
    for bi in bis:
        if hasattr(bi, 'fx_a') and hasattr(bi, 'fx_b'):
            if bi.fx_a.dt <= fvg.dt <= bi.fx_b.dt:
                return {
                    'in_stroke': True,
                    'containing_stroke': bi,
                    'stroke_direction': bi.direction.value,
                    'stroke_strength': getattr(bi, 'power', 0)
                }
    
    return {'in_stroke': False}


def _analyze_volume_context(fvg: FVG, bars: List[NewBar], lookback: int = 20) -> dict:
    """分析FVG的成交量上下文"""
    # 找到FVG时间点在bars中的位置
    fvg_index = -1
    for i, bar in enumerate(bars):
        if bar.dt == fvg.dt:
            fvg_index = i
            break
    
    if fvg_index == -1 or fvg_index < lookback:
        return {'volume_spike': False}
    
    # 计算平均成交量
    recent_bars = bars[max(0, fvg_index - lookback):fvg_index]
    avg_volume = np.mean([bar.vol for bar in recent_bars])
    
    # 检查FVG中间K线的成交量
    center_bar_volume = fvg.bar2.vol
    volume_ratio = center_bar_volume / avg_volume if avg_volume > 0 else 0
    
    return {
        'volume_spike': volume_ratio > 1.5,
        'volume_ratio': volume_ratio,
        'avg_volume': avg_volume,
        'center_volume': center_bar_volume
    }


# 保持向后兼容的函数
def check_fvg_from_bars(bars: List[NewBar], min_body_ratio: float = 0.5, 
                       min_size_atr_factor: float = 0.3, atr_period: int = 14) -> List[FVG]:
    """从K线中检测FVG（兼容性函数）
    
    现在使用分层检测策略：先基础检测，再增强评分
    """
    # 第一层：基础几何检测
    basic_fvgs = check_fvg_basic_geometric(bars, min_size_atr_factor, atr_period)
    
    # 第二层：简单的成交量过滤（保持兼容性）
    filtered_fvgs = []
    for fvg in basic_fvgs:
        body_size = abs(fvg.bar2.close - fvg.bar2.open)
        bar_range = fvg.bar2.high - fvg.bar2.low
        
        if bar_range > 0 and body_size / bar_range >= min_body_ratio:
            filtered_fvgs.append(fvg)
    
    return filtered_fvgs


def check_fvg_from_fx(fxs: List[FX], bars: List[NewBar], min_gap_atr_factor: float = 0.1) -> List[FVG]:
    """从分型中检测FVG
    
    Args:
        fxs: 分型列表
        bars: K线列表
        min_gap_atr_factor: 最小间隙与ATR的比例
        
    Returns:
        检测到的FVG列表
    """
    if len(fxs) < 2:
        return []
    
    fvgs = []
    
    # 计算ATR
    if len(bars) >= 14:
        df = pd.DataFrame([{
            'high': bar.high,
            'low': bar.low,
            'close': bar.close
        } for bar in bars])
        atr_values = ATR(df['high'], df['low'], df['close'], timeperiod=14)
        current_atr = atr_values.iloc[-1] if not pd.isna(atr_values.iloc[-1]) else 0.0
    else:
        current_atr = np.mean([bar.high - bar.low for bar in bars])
    
    min_gap_size = current_atr * min_gap_atr_factor
    
    # 检查相邻分型间的FVG
    for i in range(len(fxs) - 1):
        fx1, fx2 = fxs[i], fxs[i + 1]
        
        # 检查分型类型组合
        if fx1.mark == Mark.D and fx2.mark == Mark.G:
            # 底分型到顶分型，可能形成看涨FVG
            if fx1.high < fx2.low:
                gap_size = fx2.low - fx1.high
                if gap_size >= min_gap_size:
                    # 找到中间的强势K线
                    middle_bar = _find_middle_bar(fx1, fx2, bars)
                    if middle_bar:
                        fvg = FVG(
                            symbol=fx1.symbol,
                            dt=middle_bar.dt,
                            direction=Direction.Up,
                            bar1=fx1.elements[-1],
                            bar2=middle_bar,
                            bar3=fx2.elements[0],
                            high=fx2.low,
                            low=fx1.high
                        )
                        fvgs.append(fvg)
        
        elif fx1.mark == Mark.G and fx2.mark == Mark.D:
            # 顶分型到底分型，可能形成看跌FVG
            if fx1.low > fx2.high:
                gap_size = fx1.low - fx2.high
                if gap_size >= min_gap_size:
                    # 找到中间的强势K线
                    middle_bar = _find_middle_bar(fx1, fx2, bars)
                    if middle_bar:
                        fvg = FVG(
                            symbol=fx1.symbol,
                            dt=middle_bar.dt,
                            direction=Direction.Down,
                            bar1=fx1.elements[-1],
                            bar2=middle_bar,
                            bar3=fx2.elements[0],
                            high=fx1.low,
                            low=fx2.high
                        )
                        fvgs.append(fvg)
    
    return fvgs


def _find_middle_bar(fx1: FX, fx2: FX, bars: List[NewBar]) -> Optional[NewBar]:
    """在两个分型之间找到中间的强势K线"""
    fx1_time = fx1.dt
    fx2_time = fx2.dt
    
    # 找到时间范围内的K线
    middle_bars = []
    for bar in bars:
        if fx1_time < bar.dt < fx2_time:
            middle_bars.append(bar)
    
    # 返回实体最大的K线
    if middle_bars:
        middle_bars.sort(key=lambda x: abs(x.close - x.open), reverse=True)
        return middle_bars[0]
    
    return None


# ============================================================================
# 统一管理器 - 整合识别和分析两个阶段
# ============================================================================

class FVGDetector:
    """FVG检测器 - 统一管理识别和分析两个阶段"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化FVG检测器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 第一阶段配置（识别层）
        self.min_size_atr_factor = self.config.get('min_size_atr_factor', 0.3)
        self.atr_period = self.config.get('atr_period', 14)
        
        # 第二阶段配置（分析层）
        self.analyzer = FVGAnalyzer(self.config.get('analyzer_config', {}))
        
        # 通用配置
        self.mitigation_threshold = self.config.get('mitigation_threshold', 0.5)
        self.max_age_bars = self.config.get('max_age_bars', 100)
        self.auto_analysis = self.config.get('auto_analysis', True)
        
        # 存储数据
        self.identified_fvgs: List[FVG] = []  # 第一阶段：已识别的FVG
        self.analyzed_fvgs: List[FVG] = []    # 第二阶段：已分析的FVG
    
    def run_identification_stage(self, bars: List[NewBar]) -> List[FVG]:
        """
        第一阶段：FVG识别
        
        Args:
            bars: CZSC处理后的K线列表
            
        Returns:
            识别到的FVG列表（未评分）
        """
        identified_fvgs = identify_fvg_basic(bars, self.min_size_atr_factor, self.atr_period)
        self.identified_fvgs = identified_fvgs
        return identified_fvgs
    
    def run_analysis_stage(self, czsc_context: Optional[Dict] = None) -> List[FVG]:
        """
        第二阶段：FVG分析与评分
        
        Args:
            czsc_context: 缠论结构上下文
            
        Returns:
            分析后的FVG列表（包含质量评分）
        """
        if not self.identified_fvgs:
            return []
        
        analyzed_fvgs = self.analyzer.analyze_fvg_quality(self.identified_fvgs, czsc_context)
        self.analyzed_fvgs = analyzed_fvgs
        return analyzed_fvgs
    
    def run_full_pipeline(self, bars: List[NewBar], czsc_context: Optional[Dict] = None) -> Dict[str, List[FVG]]:
        """
        运行完整的FVG检测管道（识别 + 分析）
        
        Args:
            bars: CZSC处理后的K线列表
            czsc_context: 缠论结构上下文
            
        Returns:
            包含两个阶段结果的字典
        """
        # 第一阶段：识别
        identified = self.run_identification_stage(bars)
        
        # 第二阶段：分析（如果启用自动分析）
        analyzed = []
        if self.auto_analysis and czsc_context:
            analyzed = self.run_analysis_stage(czsc_context)
        
        return {
            'identified': identified,
            'analyzed': analyzed,
            'stage_summary': {
                'identification_count': len(identified),
                'analysis_count': len(analyzed),
                'high_quality_count': len([fvg for fvg in analyzed if fvg.score >= 0.8])
            }
        }
    
    def update_fvgs(self, bars: List[NewBar], fxs: Optional[List[FX]] = None) -> None:
        """更新FVG状态"""
        if not bars:
            return
        
        # 重新检测FVG
        self.identified_fvgs = self.run_identification_stage(bars)
        
        # 更新FVG的缓解状态
        if len(bars) > 0:
            current_bar = bars[-1]
            current_dt = current_bar.dt
            
            for fvg in self.identified_fvgs:
                # 检查后续K线是否与FVG有交集
                for bar in bars:
                    if bar.dt > fvg.dt and bar.low <= fvg.high and bar.high >= fvg.low:
                        fvg.update_mitigation(bar.close, bar.dt)
    
    def get_active_fvgs(self) -> List[FVG]:
        """获取活跃的FVG"""
        return [fvg for fvg in self.identified_fvgs if fvg.is_valid and not fvg.is_mitigated]
    
    def get_fvgs_near_price(self, price: float, tolerance: float = 0.01) -> List[FVG]:
        """获取价格附近的FVG"""
        nearby_fvgs = []
        for fvg in self.get_active_fvgs():
            distance = fvg.distance_to(price)
            if distance <= tolerance * price:
                nearby_fvgs.append(fvg)
        return nearby_fvgs
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        active_fvgs = self.get_active_fvgs()
        bullish_fvgs = [fvg for fvg in active_fvgs if fvg.direction == Direction.Up]
        bearish_fvgs = [fvg for fvg in active_fvgs if fvg.direction == Direction.Down]
        
        return {
            'total_fvgs': len(self.identified_fvgs),
            'active_fvgs': len(active_fvgs),
            'bullish_fvgs': len(bullish_fvgs),
            'bearish_fvgs': len(bearish_fvgs),
            'mitigated_fvgs': len([fvg for fvg in self.identified_fvgs if fvg.is_mitigated]),
            'tested_fvgs': len([fvg for fvg in self.identified_fvgs if fvg.is_tested])
        }
    
    def to_echarts_data(self) -> List[Dict[str, Any]]:
        """将FVG数据转换为ECharts可视化格式"""
        echarts_data = []
        for fvg in self.identified_fvgs:
            if fvg.is_valid and not fvg.is_mitigated:
                echarts_data.append({
                    'direction': 'Up' if fvg.is_bullish_fvg() else 'Down',
                    'start_dt': fvg.bar1.dt,
                    'end_dt': fvg.bar3.dt,
                    'low': fvg.low,
                    'high': fvg.high,
                    'size': fvg.size,
                    'strength': fvg.strength,
                    'symbol': fvg.symbol
                })
        return echarts_data