# -*- coding: utf-8 -*-
"""
Order Block (OB) 检测模块

Order Block是Smart Money Concepts中的关键概念，表示机构订单的聚集区域。
OB通常在价格快速移动前形成，是重要的支撑阻力位。

author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2024/12/28
describe: Order Block检测与分析
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from czsc.objects import NewBar, FX
from czsc.enum import Direction
from czsc.poi.utils import calculate_atr, check_liquidity_sweep, check_body_break


@dataclass
class OB:
    """Order Block对象"""
    symbol: str
    dt: datetime
    direction: Direction
    
    # OB的组成K线
    origin_bar: NewBar  # 引起突破的K线
    ob_bars: List[NewBar]  # OB区域的K线
    
    # OB区域
    high: float
    low: float
    
    # OB属性
    strength: float = 0.0  # OB强度
    volume_profile: float = 0.0  # 成交量特征
    is_valid: bool = True
    is_tested: bool = False
    is_broken: bool = False
    test_count: int = 0
    
    # 测试相关
    test_threshold: float = 0.5  # 测试阈值
    entry_price: Optional[float] = None
    entry_dt: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.high == 0.0 or self.low == 0.0:
            self._calculate_ob_range()
        
        if self.strength == 0.0:
            self._calculate_strength()
        
        if self.volume_profile == 0.0:
            self._calculate_volume_profile()
    
    def _calculate_ob_range(self):
        """计算OB区域范围"""
        if not self.ob_bars:
            return
        
        highs = [bar.high for bar in self.ob_bars]
        lows = [bar.low for bar in self.ob_bars]
        
        self.high = max(highs)
        self.low = min(lows)
    
    def _calculate_strength(self):
        """计算OB强度"""
        if not self.ob_bars or not self.origin_bar:
            self.strength = 0.0
            return
        
        # 基于突破幅度计算强度
        ob_size = self.high - self.low
        if ob_size <= 0:
            self.strength = 0.0
            return
        
        # 突破K线的实体大小
        origin_body = abs(self.origin_bar.close - self.origin_bar.open)
        
        # 突破距离
        if self.direction == Direction.Up:
            breakout_distance = self.origin_bar.close - self.high
        else:
            breakout_distance = self.low - self.origin_bar.close
        
        # 强度计算：突破距离相对于OB大小的比例 + 实体大小的影响
        strength = (breakout_distance / ob_size) + (origin_body / ob_size) * 0.5
        self.strength = max(0.0, min(5.0, strength))  # 限制在0-5之间
    
    def _calculate_volume_profile(self):
        """计算成交量特征"""
        if not self.ob_bars:
            self.volume_profile = 0.0
            return
        
        # 计算OB区域的平均成交量
        total_volume = sum(bar.vol for bar in self.ob_bars)
        avg_volume = total_volume / len(self.ob_bars)
        
        # 与突破K线的成交量比较
        if self.origin_bar.vol > 0:
            self.volume_profile = avg_volume / self.origin_bar.vol
        else:
            self.volume_profile = 0.0
    
    def is_bullish_ob(self) -> bool:
        """是否为看涨OB"""
        return self.direction == Direction.Up
    
    def is_bearish_ob(self) -> bool:
        """是否为看跌OB"""
        return self.direction == Direction.Down
    
    @property
    def size(self) -> float:
        """OB大小"""
        return self.high - self.low
    
    @property
    def center(self) -> float:
        """OB中心价格"""
        return (self.high + self.low) / 2
    
    def contains(self, price: float) -> bool:
        """判断价格是否在OB区域内"""
        return self.low <= price <= self.high
    
    def distance_to(self, price: float) -> float:
        """计算价格到OB的距离"""
        if self.contains(price):
            return 0.0
        elif price > self.high:
            return price - self.high
        else:
            return self.low - price
    
    def update_test(self, price: float, dt: datetime) -> bool:
        """更新OB测试状态"""
        if not self.is_valid or self.is_broken:
            return False
        
        # 检查价格是否进入OB区域
        if self.contains(price):
            if not self.is_tested:
                self.is_tested = True
                self.entry_price = price
                self.entry_dt = dt
            
            self.test_count += 1
            
            # 计算测试深度
            if self.direction == Direction.Up:
                # 看涨OB，价格从上方测试
                test_depth = (self.high - price) / self.size
            else:
                # 看跌OB，价格从下方测试
                test_depth = (price - self.low) / self.size
            
            # 如果测试深度超过阈值，认为OB被破坏
            if test_depth >= self.test_threshold:
                self.is_broken = True
                self.is_valid = False
                return True
        
        return False
    
    def __str__(self):
        direction_str = "Bullish" if self.is_bullish_ob() else "Bearish"
        status = "Broken" if self.is_broken else ("Tested" if self.is_tested else "Active")
        return f"OB({direction_str}, {self.symbol}, {self.dt.strftime('%Y-%m-%d %H:%M')}, " \
               f"[{self.low:.4f}, {self.high:.4f}], {status})"


class OBDetector:
    """Order Block检测器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化OB检测器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 检测参数
        self.min_breakout_ratio = self.config.get('min_breakout_ratio', 1.5)  # 最小突破比例
        self.min_ob_bars = self.config.get('min_ob_bars', 3)  # 最小OB K线数
        self.max_ob_bars = self.config.get('max_ob_bars', 10)  # 最大OB K线数
        self.min_volume_ratio = self.config.get('min_volume_ratio', 1.2)  # 最小成交量比例
        self.test_threshold = self.config.get('test_threshold', 0.6)  # 测试阈值
        self.max_age_bars = self.config.get('max_age_bars', 100)  # 最大保留K线数
        
        # OB列表
        self.obs: List[OB] = []
    
    def detect_obs_from_bars(self, bars: List[NewBar]) -> List[OB]:
        """从K线数据检测OB"""
        if len(bars) < self.min_ob_bars + 1:
            return []
        
        obs = []
        
        # 使用更小的步长，提高检测频率
        for i in range(self.min_ob_bars, len(bars)):
            # 检查看涨OB - 传统突破模式
            bullish_ob = self._check_bullish_ob(bars, i)
            if bullish_ob:
                obs.append(bullish_ob)
            
            # 检查看跌OB - 传统突破模式
            bearish_ob = self._check_bearish_ob(bars, i)
            if bearish_ob:
                obs.append(bearish_ob)
            
            # 检查看涨OB - 反转模式
            bullish_reversal_ob = self._check_bullish_reversal_ob(bars, i)
            if bullish_reversal_ob:
                obs.append(bullish_reversal_ob)
            
            # 检查看跌OB - 反转模式
            bearish_reversal_ob = self._check_bearish_reversal_ob(bars, i)
            if bearish_reversal_ob:
                obs.append(bearish_reversal_ob)
        
        return obs
    
    def _check_bullish_ob(self, bars: List[NewBar], breakout_idx: int) -> Optional[OB]:
        """检查看涨OB"""
        if breakout_idx < self.min_ob_bars:
            return None
        
        breakout_bar = bars[breakout_idx]
        
        # 寻找突破前的整理区域
        consolidation_start = max(0, breakout_idx - self.max_ob_bars)
        consolidation_bars = bars[consolidation_start:breakout_idx]
        
        if len(consolidation_bars) < self.min_ob_bars:
            return None
        
        # 计算整理区域的高低点
        consolidation_high = max(bar.high for bar in consolidation_bars)
        consolidation_low = min(bar.low for bar in consolidation_bars)
        consolidation_size = consolidation_high - consolidation_low
        
        if consolidation_size <= 0:
            return None
        
        # 检查是否有显著的向上突破
        breakout_height = breakout_bar.close - consolidation_high
        breakout_ratio = breakout_height / consolidation_size
        
        if breakout_ratio < self.min_breakout_ratio:
            return None
        
        # 检查成交量确认
        avg_volume = sum(bar.vol for bar in consolidation_bars) / len(consolidation_bars)
        if breakout_bar.vol < avg_volume * self.min_volume_ratio:
            return None
        
        # 找到最后一个接触整理区域高点的K线作为OB
        ob_bars = []
        for j in range(len(consolidation_bars) - 1, -1, -1):
            bar = consolidation_bars[j]
            if abs(bar.high - consolidation_high) / consolidation_size < 0.1:  # 接近高点
                ob_bars.insert(0, bar)
                if len(ob_bars) >= self.min_ob_bars:
                    break
        
        if len(ob_bars) < self.min_ob_bars:
            ob_bars = consolidation_bars[-self.min_ob_bars:]
        
        # 创建OB对象
        ob = OB(
            symbol=breakout_bar.symbol,
            dt=breakout_bar.dt,
            direction=Direction.Up,
            origin_bar=breakout_bar,
            ob_bars=ob_bars,
            high=0.0,  # 将在__post_init__中计算
            low=0.0,
            test_threshold=self.test_threshold
        )
        
        return ob
    
    def _check_bearish_ob(self, bars: List[NewBar], breakout_idx: int) -> Optional[OB]:
        """检查看跌OB"""
        if breakout_idx < self.min_ob_bars:
            return None
        
        breakout_bar = bars[breakout_idx]
        
        # 寻找突破前的整理区域
        consolidation_start = max(0, breakout_idx - self.max_ob_bars)
        consolidation_bars = bars[consolidation_start:breakout_idx]
        
        if len(consolidation_bars) < self.min_ob_bars:
            return None
        
        # 计算整理区域的高低点
        consolidation_high = max(bar.high for bar in consolidation_bars)
        consolidation_low = min(bar.low for bar in consolidation_bars)
        consolidation_size = consolidation_high - consolidation_low
        
        if consolidation_size <= 0:
            return None
        
        # 检查是否有显著的向下突破
        breakout_depth = consolidation_low - breakout_bar.close
        breakout_ratio = breakout_depth / consolidation_size
        
        if breakout_ratio < self.min_breakout_ratio:
            return None
        
        # 检查成交量确认
        avg_volume = sum(bar.vol for bar in consolidation_bars) / len(consolidation_bars)
        if breakout_bar.vol < avg_volume * self.min_volume_ratio:
            return None
        
        # 找到最后一个接触整理区域低点的K线作为OB
        ob_bars = []
        for j in range(len(consolidation_bars) - 1, -1, -1):
            bar = consolidation_bars[j]
            if abs(bar.low - consolidation_low) / consolidation_size < 0.1:  # 接近低点
                ob_bars.insert(0, bar)
                if len(ob_bars) >= self.min_ob_bars:
                    break
        
        if len(ob_bars) < self.min_ob_bars:
            ob_bars = consolidation_bars[-self.min_ob_bars:]
        
        # 创建OB对象
        ob = OB(
            symbol=breakout_bar.symbol,
            dt=breakout_bar.dt,
            direction=Direction.Down,
            origin_bar=breakout_bar,
            ob_bars=ob_bars,
            high=0.0,  # 将在__post_init__中计算
            low=0.0,
            test_threshold=self.test_threshold
        )
        
        return ob
    
    def _check_bullish_reversal_ob(self, bars: List[NewBar], reversal_idx: int) -> Optional[OB]:
        """检查看涨反转OB - 下跌后的强势反转"""
        if reversal_idx < self.min_ob_bars + 2:
            return None
        
        reversal_bar = bars[reversal_idx]
        
        # 寻找反转前的下跌趋势
        lookback_bars = bars[reversal_idx - self.max_ob_bars:reversal_idx]
        
        if len(lookback_bars) < self.min_ob_bars:
            return None
        
        # 检查是否有下跌趋势
        first_bar = lookback_bars[0]
        last_bar = lookback_bars[-1]
        
        # 下跌趋势：最后的价格明显低于开始的价格
        downtrend_exists = last_bar.close < first_bar.close * 0.995  # 至少下跌0.5%
        
        if not downtrend_exists:
            return None
        
        # 找到下跌趋势中的最低点区域
        min_low = min(bar.low for bar in lookback_bars)
        low_bars = [bar for bar in lookback_bars if abs(bar.low - min_low) / min_low < 0.001]  # 接近最低点的K线
        
        if len(low_bars) < 2:
            return None
        
        # 检查反转K线的强度
        reversal_strength = (reversal_bar.close - reversal_bar.open) / (reversal_bar.high - reversal_bar.low)
        if reversal_strength < 0.5:  # 实体至少占K线的50%
            return None
        
        # 检查反转幅度
        reversal_move = reversal_bar.close - min_low
        avg_range = sum(bar.high - bar.low for bar in lookback_bars) / len(lookback_bars)
        reversal_ratio = reversal_move / avg_range
        
        if reversal_ratio < 0.8:  # 反转幅度至少是平均振幅的0.8倍
            return None
        
        # 创建反转OB
        ob = OB(
            symbol=reversal_bar.symbol,
            dt=reversal_bar.dt,
            direction=Direction.Up,
            origin_bar=reversal_bar,
            ob_bars=low_bars,
            high=0.0,
            low=0.0,
            test_threshold=self.test_threshold
        )
        
        return ob
    
    def _check_bearish_reversal_ob(self, bars: List[NewBar], reversal_idx: int) -> Optional[OB]:
        """检查看跌反转OB - 上涨后的强势反转"""
        if reversal_idx < self.min_ob_bars + 2:
            return None
        
        reversal_bar = bars[reversal_idx]
        
        # 寻找反转前的上涨趋势
        lookback_bars = bars[reversal_idx - self.max_ob_bars:reversal_idx]
        
        if len(lookback_bars) < self.min_ob_bars:
            return None
        
        # 检查是否有上涨趋势
        first_bar = lookback_bars[0]
        last_bar = lookback_bars[-1]
        
        # 上涨趋势：最后的价格明显高于开始的价格
        uptrend_exists = last_bar.close > first_bar.close * 1.005  # 至少上涨0.5%
        
        if not uptrend_exists:
            return None
        
        # 找到上涨趋势中的最高点区域
        max_high = max(bar.high for bar in lookback_bars)
        high_bars = [bar for bar in lookback_bars if abs(bar.high - max_high) / max_high < 0.001]  # 接近最高点的K线
        
        if len(high_bars) < 2:
            return None
        
        # 检查反转K线的强度
        reversal_strength = (reversal_bar.open - reversal_bar.close) / (reversal_bar.high - reversal_bar.low)
        if reversal_strength < 0.5:  # 实体至少占K线的50%
            return None
        
        # 检查反转幅度
        reversal_move = max_high - reversal_bar.close
        avg_range = sum(bar.high - bar.low for bar in lookback_bars) / len(lookback_bars)
        reversal_ratio = reversal_move / avg_range
        
        if reversal_ratio < 0.8:  # 反转幅度至少是平均振幅的0.8倍
            return None
        
        # 创建反转OB
        ob = OB(
            symbol=reversal_bar.symbol,
            dt=reversal_bar.dt,
            direction=Direction.Down,
            origin_bar=reversal_bar,
            ob_bars=high_bars,
            high=0.0,
            low=0.0,
            test_threshold=self.test_threshold
        )
        
        return ob
    
    def update_obs(self, bars: List[NewBar]) -> None:
        """更新OB状态"""
        if not bars:
            return
        
        # 重新检测OB
        self.obs = self.detect_obs_from_bars(bars)
        
        # 更新OB的测试状态
        if len(bars) > 0:
            current_bar = bars[-1]
            current_price = current_bar.close
            current_dt = current_bar.dt
            
            for ob in self.obs:
                # 检查后续K线是否测试了OB
                for bar in bars:
                    if bar.dt > ob.dt:
                        ob.update_test(bar.close, bar.dt)
    
    def get_active_obs(self) -> List[OB]:
        """获取活跃的OB"""
        return [ob for ob in self.obs if ob.is_valid and not ob.is_broken]
    
    def get_obs_near_price(self, price: float, tolerance: float = 0.02) -> List[OB]:
        """获取价格附近的OB"""
        nearby_obs = []
        for ob in self.get_active_obs():
            distance = ob.distance_to(price)
            if distance <= tolerance * price:
                nearby_obs.append(ob)
        return nearby_obs
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        active_obs = self.get_active_obs()
        bullish_obs = [ob for ob in active_obs if ob.direction == Direction.Up]
        bearish_obs = [ob for ob in active_obs if ob.direction == Direction.Down]
        
        return {
            'total_obs': len(self.obs),
            'active_obs': len(active_obs),
            'bullish_obs': len(bullish_obs),
            'bearish_obs': len(bearish_obs),
            'tested_obs': len([ob for ob in self.obs if ob.is_tested]),
            'broken_obs': len([ob for ob in self.obs if ob.is_broken])
        }
    
    def to_echarts_data(self) -> List[Dict[str, Any]]:
        """将OB数据转换为ECharts可视化格式"""
        echarts_data = []
        for ob in self.obs:
            if ob.is_valid and not ob.is_broken:
                echarts_data.append({
                    'direction': 'Up' if ob.is_bullish_ob() else 'Down',
                    'start_dt': ob.ob_bars[0].dt,
                    'end_dt': ob.ob_bars[-1].dt,
                    'low': ob.low,
                    'high': ob.high,
                    'size': ob.size,
                    'strength': ob.strength,
                    'symbol': ob.symbol,
                    'volume_profile': ob.volume_profile
                })
        return echarts_data


def check_ob_from_bars(bars: List[NewBar], 
                       min_breakout_ratio: float = 1.5,
                       min_volume_ratio: float = 1.2) -> List[OB]:
    """从K线数据中检测OB的便捷函数"""
    detector = OBDetector({
        'min_breakout_ratio': min_breakout_ratio,
        'min_volume_ratio': min_volume_ratio
    })
    return detector.detect_obs_from_bars(bars)