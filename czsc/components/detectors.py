# -*- coding: utf-8 -*-
"""
组件检测器 - 客观识别市场技术结构

实现各种技术组件的自动检测：
- FVGDetector: 检测价格价值缺口
- OBDetector: 检测订单块
"""

from typing import List, Optional
from datetime import datetime

from czsc.objects import RawBar, NewBar
from czsc.components.institutional import FVG, OB, FVGDirection, OBDirection


class FVGDetector:
    """
    价格价值缺口检测器
    
    识别三根连续K线形成的价格缺口
    """
    
    def __init__(self, min_gap_size: float = 0.0001):
        """
        初始化FVG检测器
        
        Args:
            min_gap_size: 最小缺口大小（相对价格比例），过滤微小缺口
        """
        self.min_gap_size = min_gap_size
    
    def detect_fvgs(self, bars: List[NewBar]) -> List[FVG]:
        """
        检测所有FVG
        
        Args:
            bars: 经过缠论包含处理后的K线序列（NewBar）
            
        Returns:
            检测到的FVG列表
        """
        if len(bars) < 3:
            return []
        
        fvgs = []
        
        # 滑动窗口检测
        for i in range(len(bars) - 2):
            bar1 = bars[i]      # 第一根K线
            bar2 = bars[i + 1]  # 第二根K线（中心）
            bar3 = bars[i + 2]  # 第三根K线
            
            fvg = self._check_fvg_pattern(bar1, bar2, bar3)
            if fvg:
                fvgs.append(fvg)
        
        return fvgs
    
    def _check_fvg_pattern(self, bar1: NewBar, bar2: NewBar, bar3: NewBar) -> Optional[FVG]:
        """检查三根K线是否构成FVG模式"""
        
        # 检查看涨FVG：第一根K线的高点 < 第三根K线的低点
        if bar1.high < bar3.low:
            gap_size = bar3.low - bar1.high
            center_price = (bar1.high + bar3.low) / 2
            
            # 过滤微小缺口
            if gap_size / center_price >= self.min_gap_size:
                return FVG(
                    id=f"fvg_bullish_{bar2.dt.isoformat()}",
                    symbol=bar2.symbol,
                    dt=bar2.dt,
                    direction=FVGDirection.BULLISH,
                    top=bar3.low,
                    bottom=bar1.high,
                    midpoint_ce=(bar1.high + bar3.low) / 2,
                    first_bar_dt=bar1.dt,
                    second_bar_dt=bar2.dt,
                    third_bar_dt=bar3.dt
                )
        
        # 检查看跌FVG：第一根K线的低点 > 第三根K线的高点
        elif bar1.low > bar3.high:
            gap_size = bar1.low - bar3.high
            center_price = (bar1.low + bar3.high) / 2
            
            # 过滤微小缺口
            if gap_size / center_price >= self.min_gap_size:
                return FVG(
                    id=f"fvg_bearish_{bar2.dt.isoformat()}",
                    symbol=bar2.symbol,
                    dt=bar2.dt,
                    direction=FVGDirection.BEARISH,
                    top=bar1.low,
                    bottom=bar3.high,
                    midpoint_ce=(bar1.low + bar3.high) / 2,
                    first_bar_dt=bar1.dt,
                    second_bar_dt=bar2.dt,
                    third_bar_dt=bar3.dt
                )
        
        return None
    
    def update_fvg_mitigation(self, fvgs: List[FVG], current_bars: List[NewBar]):
        """更新FVG的回补状态"""
        if not current_bars:
            return
        
        current_bar = current_bars[-1]
        current_price_range = (current_bar.low, current_bar.high)
        
        for fvg in fvgs:
            if not fvg.is_mitigated:
                # 检查价格是否触及FVG区域
                if (current_price_range[0] <= fvg.top and 
                    current_price_range[1] >= fvg.bottom):
                    
                    # 使用收盘价更新回补状态
                    fvg.update_mitigation(current_bar.close, current_bar.dt)


class OBDetector:
    """
    订单块检测器
    
    识别强劲趋势行情前的最后一根反向K线
    """
    
    def __init__(self, min_move_strength: float = 0.02, require_fvg: bool = True):
        """
        初始化OB检测器
        
        Args:
            min_move_strength: 最小走势强度（价格变化百分比）
            require_fvg: 是否要求后续走势包含FVG
        """
        self.min_move_strength = min_move_strength
        self.require_fvg = require_fvg
    
    def detect_obs(self, bars: List[NewBar], fvgs: List[FVG] = None) -> List[OB]:
        """
        检测所有订单块
        
        Args:
            bars: 经过缠论包含处理后的K线序列（NewBar）
            fvgs: FVG列表，用于提高OB识别准确性
            
        Returns:
            检测到的OB列表
        """
        if len(bars) < 10:  # 需要足够的K线来识别趋势
            return []
        
        obs = []
        fvgs = fvgs or []
        
        # 寻找强劲走势
        strong_moves = self._find_strong_moves(bars, fvgs)
        
        # 为每个强劲走势寻找OB
        for move in strong_moves:
            ob = self._find_ob_for_move(bars, move)
            if ob:
                obs.append(ob)
        
        return obs
    
    def _find_strong_moves(self, bars: List[NewBar], fvgs: List[FVG]) -> List[dict]:
        """寻找强劲的趋势走势"""
        moves = []
        
        # 寻找连续的强势走势
        i = 5  # 从第6根K线开始查找
        while i < len(bars) - 3:
            move = self._analyze_move_from_index(bars, i, fvgs)
            if move:
                moves.append(move)
                i = move['end_index'] + 1  # 跳过已分析的区间
            else:
                i += 1
        
        return moves
    
    def _analyze_move_from_index(self, bars: List[NewBar], start_idx: int, fvgs: List[FVG]) -> Optional[dict]:
        """从指定索引分析是否存在强劲走势"""
        
        # 寻找连续的同向K线
        direction = None
        move_bars = []
        
        for i in range(start_idx, min(start_idx + 10, len(bars))):
            bar = bars[i]
            bar_direction = 'up' if bar.close > bar.open else 'down'
            
            if direction is None:
                direction = bar_direction
                move_bars.append(i)
            elif direction == bar_direction:
                move_bars.append(i)
            else:
                break
        
        # 检查是否构成强劲走势
        if len(move_bars) >= 3:  # 至少3根同向K线
            start_bar = bars[move_bars[0]]
            end_bar = bars[move_bars[-1]]
            
            # 计算走势强度
            if direction == 'up':
                price_change = end_bar.high - start_bar.low
                strength = price_change / start_bar.low
            else:
                price_change = start_bar.high - end_bar.low
                strength = price_change / start_bar.high
            
            # 检查是否满足最小强度要求
            if strength >= self.min_move_strength:
                
                # 检查是否包含FVG
                has_fvg = False
                related_fvgs = []
                
                if fvgs:
                    move_start_time = start_bar.dt
                    move_end_time = end_bar.dt
                    
                    for fvg in fvgs:
                        if move_start_time <= fvg.dt <= move_end_time:
                            # 检查FVG方向是否与走势一致
                            if ((direction == 'up' and fvg.direction == FVGDirection.BULLISH) or
                                (direction == 'down' and fvg.direction == FVGDirection.BEARISH)):
                                has_fvg = True
                                related_fvgs.append(fvg.id)
                
                # 如果要求包含FVG但没有找到，则不认为是有效走势
                if self.require_fvg and not has_fvg:
                    return None
                
                return {
                    'direction': direction,
                    'start_index': move_bars[0],
                    'end_index': move_bars[-1],
                    'strength': strength,
                    'has_fvg': has_fvg,
                    'related_fvgs': related_fvgs
                }
        
        return None
    
    def _find_ob_for_move(self, bars: List[NewBar], move: dict) -> Optional[OB]:
        """为强劲走势寻找对应的订单块"""
        
        start_idx = move['start_index']
        direction = move['direction']
        
        # 向前寻找最后一根反向K线（最多向前看5根）
        for i in range(max(0, start_idx - 5), start_idx):
            bar = bars[i]
            
            # 检查是否为反向K线
            if direction == 'up' and bar.close < bar.open:  # 走势向上，寻找阴线
                ob_direction = OBDirection.BULLISH
            elif direction == 'down' and bar.close > bar.open:  # 走势向下，寻找阳线
                ob_direction = OBDirection.BEARISH
            else:
                continue
            
            # 创建订单块
            ob = OB(
                id=f"ob_{ob_direction.value}_{bar.dt.isoformat()}",
                symbol=bar.symbol,
                dt=bar.dt,
                direction=ob_direction,
                top=bar.high,
                bottom=bar.low,
                open_price=bar.open,
                close_price=bar.close,
                related_move_has_fvg=move['has_fvg'],
                related_fvg_ids=move['related_fvgs'],
                subsequent_move_strength=move['strength']
            )
            
            # 计算成交量特征
            if i > 0:
                prev_bar = bars[i - 1]
                volume_multiplier = bar.vol / prev_bar.vol if prev_bar.vol > 0 else 1.0
                ob.volume_profile = {
                    'volume': bar.vol,
                    'volume_multiplier': volume_multiplier
                }
            
            return ob
        
        return None
    
    def update_ob_mitigation(self, obs: List[OB], current_bars: List[NewBar]):
        """更新订单块的缓解状态"""
        if not current_bars:
            return
        
        current_bar = current_bars[-1]
        
        for ob in obs:
            if not ob.is_mitigated:
                ob.update_mitigation(current_bar.close, current_bar.dt)