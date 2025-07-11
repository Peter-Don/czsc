# -*- coding: utf-8 -*-
"""
分离架构增强组件
author: Claude Code AI Assistant
create_dt: 2025-01-11
describe: 实现分型和Order Block的分离架构设计
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from czsc.enum import Mark, Direction
from czsc.objects import NewBar, FX


# =====================================================
# 第一阶段：基础识别层（纯客观）
# =====================================================

@dataclass
class BasicFractal:
    """基础分型 - 纯客观识别
    
    职责：仅负责客观识别，不包含任何主观评分
    """
    
    # 基础标识（客观）
    symbol: str
    dt: datetime
    mark: Mark  # 顶分型/底分型
    
    # 价格信息（客观）
    high: float
    low: float
    fx: float  # 分型价格
    
    # 构成信息（客观）
    elements: List[NewBar] = field(default_factory=list)  # 构成分型的3根K线
    
    # 缓存（技术用途）
    cache: dict = field(default_factory=dict)
    
    # 客观属性计算
    @property
    def open(self) -> float:
        """开盘价：分型中第一根K线的收盘价"""
        if len(self.elements) >= 3:
            return self.elements[0].close
        return 0.0
    
    @property
    def close(self) -> float:
        """收盘价：分型中最后一根K线的收盘价"""
        if len(self.elements) >= 3:
            return self.elements[-1].close
        return 0.0
    
    @property
    def vol(self) -> float:
        """成交量：分型中3根K线的成交量之和"""
        if len(self.elements) >= 3:
            return sum([x.vol for x in self.elements])
        return 0.0
    
    @property
    def amount(self) -> float:
        """成交额：分型中3根K线的成交额之和"""
        if len(self.elements) >= 3:
            return sum([x.amount for x in self.elements])
        return 0.0
    
    @property
    def strength(self) -> int:
        """分型强度：构成K线数量（客观）"""
        return len(self.elements)
    
    @property
    def has_overlap(self) -> bool:
        """构成分型的三根K线是否有重叠（客观）"""
        if len(self.elements) != 3:
            return False
        zd = max([x.low for x in self.elements])
        zg = min([x.high for x in self.elements])
        return zg >= zd


@dataclass
class BasicOrderBlock:
    """基础Order Block - 纯客观识别
    
    统一定义：从分型第一根K线开始往后，找到的第一个FVG中的第一根K线就是OB
    
    职责：仅负责客观识别，不包含任何主观评分
    """
    
    # 核心标识（客观事实）
    ob_candle: NewBar              # OB K线（核心）
    related_fractal: BasicFractal  # 关联的基础分型
    fvg_bars: List[NewBar]         # 形成FVG的3根K线
    
    # 类型信息（客观）
    direction: str                 # BULLISH, BEARISH
    formation_timestamp: datetime
    
    # 价格边界（客观）
    upper_boundary: float          # OB K线最高价
    lower_boundary: float          # OB K线最低价
    
    # 基础信息
    symbol: str = ""
    timeframe: str = ""
    
    @property
    def size(self) -> float:
        """OB大小（客观计算）"""
        return abs(self.upper_boundary - self.lower_boundary)
    
    @property
    def center(self) -> float:
        """OB中心价格（客观计算）"""
        return (self.upper_boundary + self.lower_boundary) / 2.0
    
    @property
    def volume(self) -> float:
        """OB K线成交量（客观数据）"""
        return self.ob_candle.vol


# =====================================================
# 第二阶段：分析评分层（主观评估）
# =====================================================

@dataclass
class FractalAnalysis:
    """分型分析 - 主观评分与质量分析"""
    
    # 关联的基础分型
    basic_fractal: BasicFractal
    
    # 等级评分（主观）
    level: int = 1  # 1-5级分型
    level_score: float = 0.0  # 0.0-1.0
    
    # 评级原因（主观）
    level_reasons: List[str] = field(default_factory=list)
    enhancement_factors: Dict[str, float] = field(default_factory=dict)
    
    # 质量评估（主观）
    importance_score: float = 0.0  # 重要性评分
    reliability_score: float = 0.0  # 可靠性评分
    context_score: float = 0.0     # 上下文评分
    
    # 市场上下文（主观）
    market_role: str = ""  # REVERSAL, CONTINUATION, ACCUMULATION
    position_significance: str = ""  # HIGH, MEDIUM, LOW
    
    # 层次关系（主观）
    parent_fractal: Optional['FractalAnalysis'] = None
    child_fractals: List['FractalAnalysis'] = field(default_factory=list)
    
    # 时间分析（主观）
    time_significance: float = 0.0  # ICT时间窗口加权
    session_importance: str = ""    # ASIAN, LONDON, NY, OVERLAP
    
    @property
    def comprehensive_score(self) -> float:
        """综合评分"""
        return (self.level_score * 0.4 + 
                self.importance_score * 0.3 + 
                self.reliability_score * 0.2 + 
                self.context_score * 0.1)
    
    @property
    def description(self) -> str:
        """分型描述"""
        level_names = {1: "一级", 2: "二级", 3: "三级", 4: "四级", 5: "五级"}
        mark_names = {Mark.D: "底分型", Mark.G: "顶分型"}
        
        return f"{level_names.get(self.level, f'{self.level}级')}{mark_names.get(self.basic_fractal.mark, '')}"


@dataclass
class OrderBlockAnalysis:
    """Order Block分析 - 基于SMC/ICT/TradinghHub理论的综合评分
    
    职责：对基础OB进行质量评估和交易价值分析
    """
    
    # 关联的基础OB
    basic_ob: BasicOrderBlock
    
    # === SMC (Smart Money Concepts) 评分维度 ===
    institutional_strength: float = 0.0    # 机构强度评分 (0.0-1.0)
    smart_money_footprint: float = 0.0     # 智能钱足迹评分
    liquidity_significance: float = 0.0    # 流动性重要性评分
    confluence_score: float = 0.0          # 多因素汇合评分
    
    # === ICT (Inner Circle Trader) 评分维度 ===
    liquidity_sweep_quality: float = 0.0   # 流动性扫荡质量
    kill_zone_alignment: float = 0.0       # Kill Zone时间对齐度
    market_structure_role: float = 0.0     # 市场结构作用评分
    algorithm_probability: float = 0.0      # 算法交易概率
    
    # === TradinghHub 实战评分维度 ===
    retest_probability: float = 0.0        # 重测概率预估
    reaction_strength: float = 0.0         # 反应强度预期
    entry_precision: float = 0.0           # 入场精确度
    risk_reward_ratio: float = 0.0         # 风险收益比
    
    # === 综合评级 ===
    overall_grade: str = "BASIC"           # BASIC, GOOD, EXCELLENT, PREMIUM
    confidence_level: float = 0.0          # 综合置信度 (0.0-1.0)
    trading_suitability: str = "LOW"       # LOW, MEDIUM, HIGH, EXTREME
    
    # === 分析详情 ===
    strength_factors: List[str] = field(default_factory=list)   # 优势因素
    weakness_factors: List[str] = field(default_factory=list)   # 劣势因素
    enhancement_reasons: Dict[str, float] = field(default_factory=dict)  # 增强原因
    
    # === 市场上下文 ===
    session_context: str = ""              # ASIAN, LONDON, NY, OVERLAP
    volatility_environment: str = ""       # LOW, MEDIUM, HIGH, EXTREME
    trend_alignment: str = ""              # WITH_TREND, AGAINST_TREND, SIDEWAYS
    
    @property
    def composite_score(self) -> float:
        """综合评分计算"""
        smc_score = (self.institutional_strength + self.smart_money_footprint + 
                    self.liquidity_significance + self.confluence_score) / 4.0
        
        ict_score = (self.liquidity_sweep_quality + self.kill_zone_alignment + 
                    self.market_structure_role + self.algorithm_probability) / 4.0
        
        practical_score = (self.retest_probability + self.reaction_strength + 
                          self.entry_precision + self.risk_reward_ratio) / 4.0
        
        return (smc_score * 0.35 + ict_score * 0.35 + practical_score * 0.30)
    
    @property
    def analysis_summary(self) -> str:
        """分析摘要"""
        return f"{self.overall_grade} OB - 置信度:{self.confidence_level:.2f} - 适用性:{self.trading_suitability}"


# =====================================================
# 分析器类
# =====================================================

class FractalAnalyzer:
    """分型分析器 - 负责主观评分"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 评分权重配置
        self.volume_weight = self.config.get('volume_weight', 0.3)
        self.position_weight = self.config.get('position_weight', 0.2)
        self.context_weight = self.config.get('context_weight', 0.3)
        self.time_weight = self.config.get('time_weight', 0.2)
    
    def analyze_fractal(self, basic_fractal: BasicFractal, market_context: Dict) -> FractalAnalysis:
        """分析分型质量"""
        
        analysis = FractalAnalysis(basic_fractal=basic_fractal)
        
        # 计算各项评分
        analysis.level_score = self._calculate_level_score(basic_fractal, market_context)
        analysis.importance_score = self._calculate_importance_score(basic_fractal, market_context)
        analysis.reliability_score = self._calculate_reliability_score(basic_fractal, market_context)
        analysis.context_score = self._calculate_context_score(basic_fractal, market_context)
        
        # 确定等级
        analysis.level = self._determine_level(analysis.comprehensive_score)
        
        # 分析原因
        analysis.level_reasons = self._analyze_level_reasons(basic_fractal, market_context)
        
        # 时间分析
        analysis.time_significance = self._analyze_time_significance(basic_fractal)
        
        return analysis
    
    def _calculate_level_score(self, fractal: BasicFractal, context: Dict) -> float:
        """计算等级评分"""
        score = 0.0
        
        # 成交量因素
        avg_volume = context.get('avg_volume', 1.0)
        if fractal.vol > avg_volume * 2.0:
            score += 0.3
        elif fractal.vol > avg_volume * 1.5:
            score += 0.2
        
        # 位置因素
        if context.get('at_key_level', False):
            score += 0.2
        
        # 结构因素
        if context.get('structure_significance', False):
            score += 0.2
        
        # 时间因素
        if self._is_in_ict_kill_zone(fractal.dt):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_importance_score(self, fractal: BasicFractal, context: Dict) -> float:
        """计算重要性评分"""
        # 基于分型强度、位置等因素
        score = fractal.strength / 10.0  # 基础分数
        
        # 价格位置重要性
        if context.get('at_resistance', False) or context.get('at_support', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_reliability_score(self, fractal: BasicFractal, context: Dict) -> float:
        """计算可靠性评分"""
        score = 0.5  # 基础分数
        
        # 重叠度分析
        if fractal.has_overlap:
            score += 0.2
        
        # 周围环境
        if context.get('clean_environment', False):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_context_score(self, fractal: BasicFractal, context: Dict) -> float:
        """计算上下文评分"""
        score = 0.0
        
        # 趋势一致性
        if context.get('trend_alignment', False):
            score += 0.4
        
        # 市场阶段
        if context.get('market_phase') == 'TRENDING':
            score += 0.3
        
        return min(score, 1.0)
    
    def _determine_level(self, comprehensive_score: float) -> int:
        """确定分型等级"""
        if comprehensive_score >= 0.8:
            return 5
        elif comprehensive_score >= 0.6:
            return 4
        elif comprehensive_score >= 0.4:
            return 3
        elif comprehensive_score >= 0.2:
            return 2
        else:
            return 1
    
    def _analyze_level_reasons(self, fractal: BasicFractal, context: Dict) -> List[str]:
        """分析等级原因"""
        reasons = []
        
        if fractal.vol > context.get('avg_volume', 1.0) * 2.0:
            reasons.append("大成交量支撑")
        
        if context.get('at_key_level', False):
            reasons.append("关键技术位置")
        
        if fractal.has_overlap:
            reasons.append("分型重叠增强")
        
        return reasons
    
    def _analyze_time_significance(self, fractal: BasicFractal) -> float:
        """分析时间重要性"""
        if self._is_in_ict_kill_zone(fractal.dt):
            return 1.0
        return 0.3
    
    def _is_in_ict_kill_zone(self, dt: datetime) -> bool:
        """检查是否在ICT Kill Zone时间"""
        hour = dt.hour
        return hour in [2, 3, 4, 8, 9, 13, 14, 16, 17]  # 简化的Kill Zone时间


class OrderBlockAnalyzer:
    """Order Block综合分析器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # ICT Kill Zone时间配置 (UTC时间)
        self.kill_zones = {
            'ASIAN_SESSION': (0, 3),      # 亚洲时段
            'LONDON_OPEN': (7, 10),       # 伦敦开盘
            'NY_OPEN': (12, 15),          # 纽约开盘
            'LONDON_CLOSE': (15, 18),     # 伦敦收盘
        }
        
        # SMC评分权重
        self.smc_weights = {
            'volume_factor': 0.3,
            'structure_factor': 0.25,
            'confluence_factor': 0.25,
            'liquidity_factor': 0.2
        }
    
    def analyze_order_block(self, basic_ob: BasicOrderBlock, market_context: Dict) -> OrderBlockAnalysis:
        """全面分析Order Block质量"""
        
        analysis = OrderBlockAnalysis(basic_ob=basic_ob)
        
        # === SMC维度分析 ===
        analysis.institutional_strength = self._analyze_institutional_strength(basic_ob, market_context)
        analysis.smart_money_footprint = self._analyze_smart_money_footprint(basic_ob, market_context)
        analysis.liquidity_significance = self._analyze_liquidity_significance(basic_ob, market_context)
        analysis.confluence_score = self._analyze_confluence_factors(basic_ob, market_context)
        
        # === ICT维度分析 ===
        analysis.liquidity_sweep_quality = self._analyze_liquidity_sweep(basic_ob, market_context)
        analysis.kill_zone_alignment = self._analyze_kill_zone_alignment(basic_ob)
        analysis.market_structure_role = self._analyze_market_structure_role(basic_ob, market_context)
        analysis.algorithm_probability = self._analyze_algorithm_probability(basic_ob, market_context)
        
        # === TradinghHub实战分析 ===
        analysis.retest_probability = self._analyze_retest_probability(basic_ob, market_context)
        analysis.reaction_strength = self._analyze_reaction_strength(basic_ob, market_context)
        analysis.entry_precision = self._analyze_entry_precision(basic_ob, market_context)
        analysis.risk_reward_ratio = self._calculate_risk_reward_ratio(basic_ob, market_context)
        
        # === 综合评级 ===
        analysis.overall_grade = self._determine_overall_grade(analysis.composite_score)
        analysis.confidence_level = analysis.composite_score
        analysis.trading_suitability = self._determine_trading_suitability(analysis)
        
        # === 生成分析详情 ===
        analysis.strength_factors = self._identify_strength_factors(basic_ob, analysis)
        analysis.weakness_factors = self._identify_weakness_factors(basic_ob, analysis)
        
        return analysis
    
    def _analyze_institutional_strength(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析机构强度 - SMC核心理论"""
        score = 0.0
        
        # 成交量分析（SMC理论：机构大单特征）
        avg_volume = context.get('avg_volume', 1.0)
        volume_ratio = ob.volume / avg_volume if avg_volume > 0 else 0
        
        if volume_ratio >= 5.0:
            score += 0.5  # 极端成交量增加
        elif volume_ratio >= 3.0:
            score += 0.4  # 显著成交量增加
        elif volume_ratio >= 2.0:
            score += 0.3  # 中等成交量增加
        elif volume_ratio >= 1.5:
            score += 0.2  # 轻微成交量增加
        
        # 价格冲击分析（SMC理论：Smart Money执行效应）
        fvg_size = self._calculate_fvg_size(ob.fvg_bars)
        atr = context.get('atr', 1.0)
        if fvg_size >= atr * 1.0:
            score += 0.3  # 显著价格跳跃
        elif fvg_size >= atr * 0.5:
            score += 0.2  # 中等价格跳跃
        
        # 分型强度（机构决策确定性）
        fractal_strength = len(ob.related_fractal.elements)
        if fractal_strength >= 5:
            score += 0.2  # 强分型
        elif fractal_strength >= 3:
            score += 0.1  # 标准分型
        
        return min(score, 1.0)
    
    def _analyze_smart_money_footprint(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析智能钱足迹"""
        score = 0.0
        
        # 时间效率分析
        if context.get('fast_move_after_ob', False):
            score += 0.4
        
        # 价格精确度
        if context.get('precise_level_reaction', False):
            score += 0.3
        
        # 重测行为
        if context.get('clean_retest', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_liquidity_significance(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析流动性重要性"""
        score = 0.0
        
        # 位置重要性
        if context.get('at_daily_level', False):
            score += 0.4
        elif context.get('at_4h_level', False):
            score += 0.3
        
        # 流动性池大小
        if context.get('major_liquidity_pool', False):
            score += 0.3
        
        # 市场关注度
        if context.get('high_market_attention', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_confluence_factors(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析汇合因素"""
        score = 0.0
        
        # 技术位汇合
        if context.get('fibonacci_confluence', False):
            score += 0.25
        
        # 多时间框架对齐
        if context.get('multi_tf_alignment', False):
            score += 0.25
        
        # 成交量确认
        if context.get('volume_confirmation', False):
            score += 0.25
        
        # 其他理论汇合
        if context.get('wyckoff_confluence', False):
            score += 0.25
        
        return min(score, 1.0)
    
    def _analyze_liquidity_sweep(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析流动性扫荡质量 - ICT核心理论"""
        score = 0.0
        
        # 检查是否有明显的流动性扫荡
        has_sweep = context.get('liquidity_sweep_detected', False)
        if has_sweep:
            score += 0.4
            
            # 扫荡距离分析
            sweep_distance = context.get('sweep_distance', 0)
            atr = context.get('atr', 1.0)
            if sweep_distance > atr * 0.5:
                score += 0.3  # 显著扫荡
            elif sweep_distance > atr * 0.2:
                score += 0.2  # 中等扫荡
        
        # 回撤速度（ICT理论：快速回撤表明流动性被清理）
        reversion_speed = context.get('reversion_speed', 10)
        if reversion_speed <= 3:
            score += 0.3  # 快速回撤
        elif reversion_speed <= 5:
            score += 0.2  # 中速回撤
        
        return min(score, 1.0)
    
    def _analyze_kill_zone_alignment(self, ob: BasicOrderBlock) -> float:
        """分析Kill Zone对齐度"""
        ob_hour = ob.formation_timestamp.hour
        
        for zone_name, (start, end) in self.kill_zones.items():
            if start <= ob_hour < end:
                if zone_name in ['LONDON_OPEN', 'NY_OPEN']:
                    return 1.0  # 最重要的时间窗口
                else:
                    return 0.7  # 次要时间窗口
        
        return 0.2  # 非Kill Zone时间
    
    def _analyze_market_structure_role(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析市场结构作用"""
        score = 0.0
        
        if context.get('breaks_structure', False):
            score += 0.5  # 突破市场结构
        
        if context.get('continues_trend', False):
            score += 0.3  # 延续趋势
        
        if context.get('reversal_potential', False):
            score += 0.2  # 反转潜力
        
        return min(score, 1.0)
    
    def _analyze_algorithm_probability(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析算法交易概率"""
        score = 0.0
        
        # 价格效率
        if context.get('high_price_efficiency', False):
            score += 0.4
        
        # 时间精确性
        if context.get('precise_timing', False):
            score += 0.3
        
        # 执行特征
        if context.get('algorithmic_execution', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_retest_probability(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析重测概率 - TradinghHub理论"""
        score = 0.0
        
        # 历史重测行为
        retest_history = context.get('retest_history', 0)
        if retest_history >= 2:
            score += 0.4
        elif retest_history >= 1:
            score += 0.2
        
        # 距离当前价格远近
        distance_factor = context.get('distance_factor', 1.0)
        if distance_factor <= 0.5:
            score += 0.3  # 较近距离，重测概率高
        elif distance_factor <= 1.0:
            score += 0.2
        
        # 市场环境
        if context.get('favorable_market_condition', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _analyze_reaction_strength(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析反应强度预期"""
        score = 0.0
        
        # 历史反应强度
        historical_reaction = context.get('historical_reaction_strength', 0.0)
        score += min(historical_reaction, 0.5)
        
        # 当前市场情绪
        if context.get('strong_market_sentiment', False):
            score += 0.3
        
        # 技术汇合
        if context.get('technical_confluence', False):
            score += 0.2
        
        return min(score, 1.0)
    
    def _analyze_entry_precision(self, ob: BasicOrderBlock, context: Dict) -> float:
        """分析入场精确度"""
        score = 0.0
        
        # OB清晰度
        if ob.size / context.get('atr', 1.0) <= 0.5:
            score += 0.4  # 小OB，精确度高
        
        # 边界清晰度
        if context.get('clear_boundaries', False):
            score += 0.3
        
        # 失效点明确
        if context.get('clear_invalidation', False):
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_risk_reward_ratio(self, ob: BasicOrderBlock, context: Dict) -> float:
        """计算风险收益比"""
        potential_reward = context.get('potential_reward', 1.0)
        potential_risk = context.get('potential_risk', 1.0)
        
        if potential_risk > 0:
            ratio = potential_reward / potential_risk
            return min(ratio / 3.0, 1.0)  # 标准化到0-1范围
        
        return 0.0
    
    def _determine_overall_grade(self, composite_score: float) -> str:
        """确定综合评级"""
        if composite_score >= 0.85:
            return "PREMIUM"    # 顶级OB
        elif composite_score >= 0.70:
            return "EXCELLENT"  # 优秀OB
        elif composite_score >= 0.55:
            return "GOOD"       # 良好OB
        elif composite_score >= 0.40:
            return "AVERAGE"    # 平均OB
        else:
            return "BASIC"      # 基础OB
    
    def _determine_trading_suitability(self, analysis: OrderBlockAnalysis) -> str:
        """确定交易适用性"""
        score = analysis.composite_score
        
        if score >= 0.8:
            return "EXTREME"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _identify_strength_factors(self, ob: BasicOrderBlock, analysis: OrderBlockAnalysis) -> List[str]:
        """识别优势因素"""
        factors = []
        
        if analysis.institutional_strength >= 0.7:
            factors.append("强机构特征")
        
        if analysis.kill_zone_alignment >= 0.7:
            factors.append("Kill Zone对齐")
        
        if analysis.liquidity_sweep_quality >= 0.6:
            factors.append("流动性扫荡确认")
        
        if analysis.retest_probability >= 0.6:
            factors.append("高重测概率")
        
        return factors
    
    def _identify_weakness_factors(self, ob: BasicOrderBlock, analysis: OrderBlockAnalysis) -> List[str]:
        """识别劣势因素"""
        factors = []
        
        if analysis.institutional_strength < 0.3:
            factors.append("机构特征不明显")
        
        if analysis.kill_zone_alignment < 0.3:
            factors.append("时间窗口不佳")
        
        if analysis.liquidity_sweep_quality < 0.3:
            factors.append("缺少流动性扫荡")
        
        if analysis.entry_precision < 0.4:
            factors.append("入场精确度低")
        
        return factors
    
    def _calculate_fvg_size(self, fvg_bars: List[NewBar]) -> float:
        """计算FVG大小"""
        if len(fvg_bars) >= 3:
            bar1, bar2, bar3 = fvg_bars[0], fvg_bars[1], fvg_bars[2]
            # 看涨FVG: bar3.low - bar1.high
            # 看跌FVG: bar1.low - bar3.high
            if bar1.high < bar3.low:
                return bar3.low - bar1.high
            elif bar1.low > bar3.high:
                return bar1.low - bar3.high
        
        return 0.0


# =====================================================
# 统一的OB检测算法
# =====================================================

class UnifiedOrderBlockDetector:
    """统一的Order Block检测器"""
    
    def detect_order_block(self, fractal: FX, czsc) -> Optional[BasicOrderBlock]:
        """检测Order Block - 统一算法
        
        算法流程：
        1. 从分型第一根K线开始
        2. 按序搜索第一个方向一致的FVG
        3. FVG的第一根K线就是OB
        
        示例：
        K1 K2 K3(底分型) K4 K5 K6
        ↑________________↑___↑___↑
        从K1开始搜索     如果K4-K5-K6形成第一个看涨FVG
                        那么K4是看涨OB
        """
        
        # 获取分型第一根K线的索引
        fractal_start_index = self._find_fractal_start_index(fractal, czsc)
        if fractal_start_index == -1:
            return None
        
        # 从分型第一根K线开始搜索
        search_bars = czsc.bars_ubi[fractal_start_index:]
        
        # 搜索第一个方向一致的FVG
        for i in range(2, min(len(search_bars), 20)):  # 限制搜索范围
            if i + 1 >= len(search_bars):
                break
                
            bar1, bar2, bar3 = search_bars[i-2:i+1]
            
            # 检查是否形成方向一致的FVG
            if self._is_direction_consistent_fvg(bar1, bar2, bar3, fractal):
                # 将FX对象转换为BasicFractal
                basic_fractal = self._convert_fx_to_basic_fractal(fractal)
                
                # FVG的第一根K线(bar1)就是OB
                # 正确判断OB方向：基于笔方向和后续走势
                ob_direction = self._determine_ob_direction_comprehensive(
                    fractal, bar1, czsc, search_bars[i+1:i+11]  # 后续10根K线
                )
                
                return BasicOrderBlock(
                    ob_candle=bar1,
                    related_fractal=basic_fractal,
                    fvg_bars=[bar1, bar2, bar3],
                    direction=ob_direction,
                    formation_timestamp=bar1.dt,
                    upper_boundary=bar1.high,
                    lower_boundary=bar1.low,
                    symbol=fractal.symbol if hasattr(fractal, 'symbol') else "",
                    timeframe=""  # 可根据需要设置
                )
        
        return None
    
    def detect_all_order_blocks(self, czsc) -> List[BasicOrderBlock]:
        """检测所有分型的Order Block"""
        
        order_blocks = []
        
        for fractal in czsc.fx_list:
            ob = self.detect_order_block(fractal, czsc)
            if ob:
                order_blocks.append(ob)
        
        return order_blocks
    
    def _is_direction_consistent_fvg(self, bar1: NewBar, bar2: NewBar, bar3: NewBar, fractal: FX) -> bool:
        """检查是否是方向一致的FVG"""
        
        if fractal.mark == Mark.D:  # 底分型 → 看涨FVG
            return bar1.high < bar3.low  # 看涨FVG条件
        
        elif fractal.mark == Mark.G:  # 顶分型 → 看跌FVG
            return bar1.low > bar3.high  # 看跌FVG条件
        
        return False
    
    def _find_fractal_start_index(self, fractal: FX, czsc) -> int:
        """找到分型第一根K线在bars_ubi中的索引"""
        
        if not fractal.elements or len(fractal.elements) < 3:
            return -1
        
        # 分型第一根K线
        first_bar = fractal.elements[0]
        
        # 在bars_ubi中找到对应的索引
        bars_ubi = getattr(czsc, 'bars_ubi', [])
        for i, bar in enumerate(bars_ubi):
            if bar.dt == first_bar.dt:
                return i
        
        return -1
    
    def _convert_fx_to_basic_fractal(self, fx: FX) -> BasicFractal:
        """将FX对象转换为BasicFractal对象"""
        return BasicFractal(
            symbol=fx.symbol,
            dt=fx.dt,
            mark=fx.mark,
            high=fx.high,
            low=fx.low,
            fx=fx.fx,
            elements=fx.elements
        )
    
    def _determine_ob_direction_comprehensive(self, fractal: FX, ob_candle: NewBar, 
                                            czsc, subsequent_bars: List[NewBar]) -> str:
        """综合判断OB方向
        
        核心原理：OB的方向应该与其所推动的市场结构方向一致
        
        Args:
            fractal: 关联的分型
            ob_candle: OB K线
            czsc: CZSC对象
            subsequent_bars: OB形成后的K线序列
            
        Returns:
            str: "BULLISH", "BEARISH", 或 "UNKNOWN"
        """
        
        results = []
        
        # 方法1：基于笔方向判断（主要方法）
        stroke_direction = self._determine_direction_by_stroke(ob_candle, czsc)
        if stroke_direction != "UNKNOWN":
            results.append(stroke_direction)
        
        # 方法2：基于后续价格走势判断（辅助确认）
        if subsequent_bars:
            movement_direction = self._determine_direction_by_movement(ob_candle, subsequent_bars)
            if movement_direction != "UNKNOWN":
                results.append(movement_direction)
        
        # 方法3：基于FVG方向判断（最后兜底）
        fvg_direction = self._determine_direction_by_fvg(fractal)
        results.append(fvg_direction)
        
        # 投票决定最终方向
        if not results:
            return "UNKNOWN"
        
        bullish_count = results.count("BULLISH")
        bearish_count = results.count("BEARISH")
        
        if bullish_count > bearish_count:
            return "BULLISH"
        elif bearish_count > bullish_count:
            return "BEARISH"
        else:
            # 平票时，优先使用笔方向判断
            return stroke_direction if stroke_direction != "UNKNOWN" else fvg_direction
    
    def _determine_direction_by_stroke(self, ob_candle: NewBar, czsc) -> str:
        """根据OB所在笔的方向判断OB方向"""
        
        # 获取笔列表
        bi_list = getattr(czsc, 'bi_list', [])
        if not bi_list:
            return "UNKNOWN"
        
        # 找到包含OB K线的笔
        for bi in bi_list:
            if hasattr(bi, 'fx_a') and hasattr(bi, 'fx_b'):
                # 检查OB时间是否在笔的时间范围内
                if bi.fx_a.dt <= ob_candle.dt <= bi.fx_b.dt:
                    if bi.direction == Direction.Up:
                        return "BULLISH"
                    elif bi.direction == Direction.Down:
                        return "BEARISH"
        
        return "UNKNOWN"
    
    def _determine_direction_by_movement(self, ob_candle: NewBar, subsequent_bars: List[NewBar]) -> str:
        """根据OB形成后的价格走势判断方向"""
        
        if not subsequent_bars:
            return "UNKNOWN"
        
        ob_price = ob_candle.close
        
        # 计算后续价格的加权趋势（近期权重更高）
        price_changes = []
        weights = []
        
        for i, bar in enumerate(subsequent_bars):
            price_change = (bar.close - ob_price) / ob_price
            weight = 1.0 / (i + 1)  # 距离越近权重越高
            
            price_changes.append(price_change)
            weights.append(weight)
        
        # 计算加权平均趋势
        if weights:
            weighted_trend = sum(pc * w for pc, w in zip(price_changes, weights)) / sum(weights)
            
            # 设置阈值避免微小波动的误判
            threshold = 0.002  # 0.2%的阈值
            
            if weighted_trend > threshold:
                return "BULLISH"
            elif weighted_trend < -threshold:
                return "BEARISH"
        
        return "UNKNOWN"
    
    def _determine_direction_by_fvg(self, fractal: FX) -> str:
        """根据分型类型判断FVG预期方向（兜底方法）"""
        
        # 这是原来的简单逻辑，作为最后的兜底方案
        if fractal.mark == Mark.D:  # 底分型通常产生看涨FVG
            return "BULLISH"
        elif fractal.mark == Mark.G:  # 顶分型通常产生看跌FVG
            return "BEARISH"
        else:
            return "UNKNOWN"


# =====================================================
# 使用示例
# =====================================================

def example_usage():
    """使用示例"""
    
    # 假设有一个分型对象
    from czsc.objects import FX
    from datetime import datetime
    
    # 模拟数据（实际使用时从CZSC获取）
    sample_fx = FX(
        symbol="BTCUSDT",
        dt=datetime.now(),
        mark=Mark.D,
        high=25000,
        low=24500,
        fx=24500,
        elements=[]  # 实际应包含3根NewBar
    )
    
    # 第一阶段：基础识别
    detector = UnifiedOrderBlockDetector()
    # basic_ob = detector.detect_order_block(sample_fx, czsc_instance)
    
    # 第二阶段：分析评分（假设已有basic_ob）
    # market_context = {
    #     'avg_volume': 1000,
    #     'atr': 100,
    #     'at_key_level': True,
    #     'liquidity_sweep_detected': True
    # }
    
    # ob_analyzer = OrderBlockAnalyzer()
    # ob_analysis = ob_analyzer.analyze_order_block(basic_ob, market_context)
    
    # print(f"OB评级: {ob_analysis.overall_grade}")
    # print(f"综合评分: {ob_analysis.composite_score:.2f}")
    # print(f"分析摘要: {ob_analysis.analysis_summary}")
    
    print("分离架构组件已实现")


if __name__ == "__main__":
    example_usage()