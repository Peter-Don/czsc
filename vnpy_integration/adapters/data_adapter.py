# -*- coding: utf-8 -*-
"""
数据适配器

VNPy与CZSC之间的数据格式转换和多周期数据管理
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import OrderedDict, defaultdict

# 添加CZSC路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# VNPy imports
try:
    from vnpy.trader.object import BarData
    from vnpy.trader.constant import Exchange, Interval
    VNPY_AVAILABLE = True
except ImportError:
    VNPY_AVAILABLE = False
    print("VNPy未安装，部分功能将受限")

# CZSC imports
try:
    from czsc.analyze import CZSC
    from czsc.objects import RawBar, Freq
    from czsc.utils import BarGenerator
    CZSC_AVAILABLE = True
except ImportError:
    CZSC_AVAILABLE = False
    print("CZSC库未安装，无法使用数据适配功能")


class VnpyToCzscConverter:
    """VNPy到CZSC的数据转换器"""
    
    # 频率映射
    FREQ_MAPPING = {
        Interval.MINUTE: Freq.F1,
        Interval.HOUR: Freq.F60, 
        Interval.DAILY: Freq.D,
        # 可以根据需要添加更多映射
    }
    
    @classmethod
    def convert_bar(cls, vnpy_bar: 'BarData', bar_id: Optional[int] = None) -> 'RawBar':
        """
        将VNPy的BarData转换为CZSC的RawBar
        
        Args:
            vnpy_bar: VNPy的K线数据对象
            bar_id: K线ID，如果不提供则使用时间戳
            
        Returns:
            RawBar: CZSC的原始K线对象
        """
        if not CZSC_AVAILABLE:
            raise ImportError("CZSC库未安装，无法进行数据转换")
            
        if not VNPY_AVAILABLE:
            raise ImportError("VNPy未安装，无法进行数据转换")
        
        # 如果没有提供bar_id，使用时间戳
        if bar_id is None:
            bar_id = int(vnpy_bar.datetime.timestamp())
        
        # 频率转换
        freq = cls.FREQ_MAPPING.get(vnpy_bar.interval, Freq.F1)
        
        # 处理成交额：如果没有成交额，使用成交量*收盘价估算
        amount = vnpy_bar.turnover
        if amount is None or amount == 0:
            amount = vnpy_bar.volume * vnpy_bar.close_price
        
        return RawBar(
            symbol=vnpy_bar.symbol,
            id=bar_id,
            dt=vnpy_bar.datetime,
            freq=freq,
            open=vnpy_bar.open_price,
            close=vnpy_bar.close_price,
            high=vnpy_bar.high_price,
            low=vnpy_bar.low_price,
            vol=vnpy_bar.volume,
            amount=amount,
            cache={}
        )
    
    @classmethod
    def convert_bars(cls, vnpy_bars: List['BarData']) -> List['RawBar']:
        """
        批量转换K线数据
        
        Args:
            vnpy_bars: VNPy K线数据列表
            
        Returns:
            List[RawBar]: CZSC原始K线列表
        """
        czsc_bars = []
        for i, vnpy_bar in enumerate(vnpy_bars):
            czsc_bar = cls.convert_bar(vnpy_bar, bar_id=i)
            czsc_bars.append(czsc_bar)
        return czsc_bars
    
    @classmethod
    def validate_bar_data(cls, vnpy_bar: 'BarData') -> bool:
        """
        验证K线数据的有效性
        
        Args:
            vnpy_bar: VNPy K线数据
            
        Returns:
            bool: 数据是否有效
        """
        # 基础数据检查
        if not vnpy_bar:
            return False
            
        # 价格数据检查
        if (vnpy_bar.high < vnpy_bar.low or 
            vnpy_bar.open_price < 0 or 
            vnpy_bar.close_price < 0 or
            vnpy_bar.high <= 0 or 
            vnpy_bar.low <= 0):
            return False
            
        # 成交量检查
        if vnpy_bar.volume < 0:
            return False
            
        # 时间检查
        if not isinstance(vnpy_bar.datetime, datetime):
            return False
            
        return True


class CzscDataManager:
    """CZSC数据管理器 - 管理多周期数据和CZSC分析器"""
    
    def __init__(self, symbol: str, frequencies: List[str], max_bars: int = 5000):
        """
        初始化数据管理器
        
        Args:
            symbol: 交易品种
            frequencies: 分析周期列表，如 ['1m', '5m', '15m', '30m', '1h', '1d']
            max_bars: 每个周期保留的最大K线数量
        """
        self.symbol = symbol
        self.frequencies = frequencies
        self.max_bars = max_bars
        
        # 数据存储
        self.raw_bars: Dict[str, List[RawBar]] = {freq: [] for freq in frequencies}
        self.czsc_analyzers: Dict[str, CZSC] = {}
        
        # 数据统计
        self.total_bars_received = 0
        self.last_update_time: Optional[datetime] = None
        self.converter = VnpyToCzscConverter()
        
        # 初始化CZSC分析器
        self._initialize_czsc_analyzers()
    
    def _initialize_czsc_analyzers(self):
        """初始化CZSC分析器"""
        if not CZSC_AVAILABLE:
            return
            
        for freq in self.frequencies:
            try:
                # 将频率字符串转换为Freq枚举
                freq_enum = self._convert_freq_string(freq)
                self.czsc_analyzers[freq] = CZSC(bars=[], freq=freq_enum)
            except Exception as e:
                print(f"初始化{freq}周期CZSC分析器失败: {e}")
    
    def _convert_freq_string(self, freq_str: str) -> 'Freq':
        """将频率字符串转换为Freq枚举"""
        freq_map = {
            '1m': Freq.F1,
            '5m': Freq.F5,
            '15m': Freq.F15,
            '30m': Freq.F30,
            '1h': Freq.F60,
            '4h': Freq.F240,
            '1d': Freq.D,
            '1w': Freq.W,
            '1M': Freq.M,
        }
        return freq_map.get(freq_str, Freq.F1)
    
    def update_base_bar(self, vnpy_bar: 'BarData') -> Dict[str, Any]:
        """
        更新基础周期K线数据（通常是1分钟）
        
        Args:
            vnpy_bar: VNPy K线数据
            
        Returns:
            Dict: 更新结果
        """
        result = {
            'success': False,
            'symbol': self.symbol,
            'datetime': vnpy_bar.datetime,
            'updated_frequencies': [],
            'error': None
        }
        
        try:
            # 验证数据
            if not self.converter.validate_bar_data(vnpy_bar):
                result['error'] = "K线数据验证失败"
                return result
            
            # 转换数据
            czsc_bar = self.converter.convert_bar(vnpy_bar, self.total_bars_received)
            
            # 更新统计
            self.total_bars_received += 1
            self.last_update_time = vnpy_bar.datetime
            
            # 根据基础周期更新各个周期的数据
            base_freq = self._get_base_frequency()
            if base_freq:
                self._update_frequency_data(base_freq, czsc_bar)
                result['updated_frequencies'].append(base_freq)
                
                # 合成其他周期数据
                for freq in self.frequencies:
                    if freq != base_freq:
                        if self._should_update_frequency(freq, czsc_bar):
                            synthesized_bar = self._synthesize_bar(freq, czsc_bar)
                            if synthesized_bar:
                                self._update_frequency_data(freq, synthesized_bar)
                                result['updated_frequencies'].append(freq)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"更新K线数据失败: {e}")
        
        return result
    
    def _get_base_frequency(self) -> Optional[str]:
        """获取基础周期（通常是最小周期）"""
        if '1m' in self.frequencies:
            return '1m'
        elif '5m' in self.frequencies:
            return '5m'
        elif self.frequencies:
            return self.frequencies[0]
        return None
    
    def _should_update_frequency(self, freq: str, new_bar: RawBar) -> bool:
        """判断是否应该更新指定周期"""
        # 简化实现：这里应该根据时间判断是否需要合成新的K线
        # 实际应用中需要更复杂的逻辑
        return True
    
    def _synthesize_bar(self, freq: str, base_bar: RawBar) -> Optional[RawBar]:
        """合成指定周期的K线"""
        # 简化实现：实际应该根据基础K线合成目标周期K线
        # 这里暂时返回基础K线，实际需要实现时间周期合成逻辑
        return RawBar(
            symbol=base_bar.symbol,
            id=base_bar.id,
            dt=base_bar.dt,
            freq=self._convert_freq_string(freq),
            open=base_bar.open,
            close=base_bar.close,
            high=base_bar.high,
            low=base_bar.low,
            vol=base_bar.vol,
            amount=base_bar.amount,
            cache={}
        )
    
    def _update_frequency_data(self, freq: str, bar: RawBar):
        """更新指定周期的数据"""
        # 添加到原始数据
        if freq not in self.raw_bars:
            self.raw_bars[freq] = []
        
        self.raw_bars[freq].append(bar)
        
        # 限制数据长度
        if len(self.raw_bars[freq]) > self.max_bars:
            self.raw_bars[freq] = self.raw_bars[freq][-self.max_bars:]
        
        # 更新CZSC分析器
        if freq in self.czsc_analyzers and self.raw_bars[freq]:
            try:
                # 重新初始化CZSC分析器或更新数据
                # 注意：这里可能需要优化，避免每次都重新创建
                self.czsc_analyzers[freq] = CZSC(
                    bars=self.raw_bars[freq], 
                    freq=self._convert_freq_string(freq)
                )
            except Exception as e:
                print(f"更新{freq}周期CZSC分析器失败: {e}")
    
    def get_czsc_data(self, frequency: str) -> Dict[str, Any]:
        """
        获取指定周期的CZSC分析数据
        
        Args:
            frequency: 分析周期
            
        Returns:
            Dict: CZSC分析数据
        """
        if frequency not in self.czsc_analyzers:
            return {}
        
        czsc = self.czsc_analyzers[frequency]
        
        try:
            return {
                'symbol': self.symbol,
                'frequency': frequency,
                'bars_count': len(czsc.bars_raw) if hasattr(czsc, 'bars_raw') else 0,
                'bars': getattr(czsc, 'bars_raw', []),
                'bars_ubi': getattr(czsc, 'bars_ubi', []),
                'fx_list': getattr(czsc, 'fx_list', []),
                'bi_list': getattr(czsc, 'bi_list', []),
                'finished_bis': getattr(czsc, 'finished_bis', []),
                'signals': getattr(czsc, 'signals', {}),
                'ubi': getattr(czsc, 'ubi', {}),
                'last_update': self.last_update_time
            }
        except Exception as e:
            print(f"获取{frequency}周期CZSC数据失败: {e}")
            return {}
    
    def get_all_czsc_data(self) -> Dict[str, Dict[str, Any]]:
        """获取所有周期的CZSC分析数据"""
        all_data = {}
        for freq in self.frequencies:
            all_data[freq] = self.get_czsc_data(freq)
        return all_data
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        stats = {
            'symbol': self.symbol,
            'total_bars_received': self.total_bars_received,
            'last_update_time': self.last_update_time,
            'frequencies': self.frequencies,
            'bars_count_by_freq': {},
            'czsc_status': {}
        }
        
        for freq in self.frequencies:
            # K线数量统计
            stats['bars_count_by_freq'][freq] = len(self.raw_bars.get(freq, []))
            
            # CZSC状态统计
            if freq in self.czsc_analyzers:
                czsc = self.czsc_analyzers[freq]
                try:
                    stats['czsc_status'][freq] = {
                        'fx_count': len(getattr(czsc, 'fx_list', [])),
                        'bi_count': len(getattr(czsc, 'bi_list', [])),
                        'has_signals': bool(getattr(czsc, 'signals', {})),
                        'last_bar_time': getattr(czsc.bars_raw[-1], 'dt', None) if getattr(czsc, 'bars_raw', []) else None
                    }
                except Exception as e:
                    stats['czsc_status'][freq] = {'error': str(e)}
        
        return stats
    
    def clear_data(self, frequency: Optional[str] = None):
        """
        清空数据
        
        Args:
            frequency: 指定周期，如果为None则清空所有周期
        """
        if frequency:
            if frequency in self.raw_bars:
                self.raw_bars[frequency] = []
            if frequency in self.czsc_analyzers:
                self._initialize_single_czsc_analyzer(frequency)
        else:
            # 清空所有数据
            for freq in self.frequencies:
                self.raw_bars[freq] = []
            self._initialize_czsc_analyzers()
            self.total_bars_received = 0
            self.last_update_time = None
    
    def _initialize_single_czsc_analyzer(self, frequency: str):
        """初始化单个CZSC分析器"""
        try:
            freq_enum = self._convert_freq_string(frequency)
            self.czsc_analyzers[frequency] = CZSC(bars=[], freq=freq_enum)
        except Exception as e:
            print(f"初始化{frequency}周期CZSC分析器失败: {e}")