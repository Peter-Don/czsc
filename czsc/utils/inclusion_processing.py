# -*- coding: utf-8 -*-
"""
author: claude
create_dt: 2025/01/11
describe: CZSC包含处理后的K线OCHLV处理工具
为NewBar添加包含处理后的OCHLV信息，开盘价取前一根K线的收盘价，收盘价取后一根K线的收盘价
"""
from typing import List
from ..objects import NewBar


def set_inclusion_prices_for_bars(bars: List[NewBar]) -> List[NewBar]:
    """为NewBar序列设置包含处理后的OCHLV价格
    
    处理规则：
    - 开盘价：取前一根K线的收盘价
    - 收盘价：取后一根K线的收盘价
    - 高低点：保持原有值
    - 成交量成交额：保持原有值
    
    Args:
        bars: NewBar序列（已经过包含处理）
        
    Returns:
        设置了包含OCHLV信息的NewBar序列
    """
    if len(bars) < 2:
        return bars
    
    processed_bars = bars.copy()
    
    for i, bar in enumerate(processed_bars):
        # 确定前一根和后一根K线的收盘价
        previous_close = bars[i-1].close if i > 0 else bar.open
        next_close = bars[i+1].close if i < len(bars) - 1 else bar.close
        
        # 设置包含处理后的价格
        bar.set_inclusion_prices(previous_close, next_close)
        
        # 额外在cache中记录处理信息
        bar.cache['inclusion_processed'] = True
        bar.cache['inclusion_processing_time'] = bars[-1].dt if bars else bar.dt
    
    return processed_bars


def get_inclusion_ohlcv_sequence(bars: List[NewBar]) -> List[dict]:
    """获取包含处理后的OHLCV序列
    
    Args:
        bars: 已设置包含OCHLV的NewBar序列
        
    Returns:
        包含处理后的OHLCV字典列表
    """
    return [bar.get_inclusion_ohlcv() for bar in bars]


def verify_inclusion_processing(bars: List[NewBar]) -> dict:
    """验证包含处理后的OCHLV是否正确设置
    
    Args:
        bars: NewBar序列
        
    Returns:
        验证结果字典
    """
    if not bars:
        return {'status': 'empty', 'processed_count': 0, 'total_count': 0}
    
    processed_count = 0
    errors = []
    
    for i, bar in enumerate(bars):
        is_processed = bar.cache.get('inclusion_processed', False)
        if is_processed:
            processed_count += 1
            
            # 验证开盘价设置
            expected_open = bars[i-1].close if i > 0 else bar.open
            actual_open = bar.inclusion_open
            if abs(actual_open - expected_open) > 1e-6:
                errors.append(f"Bar {i}: 开盘价不匹配，期望{expected_open}，实际{actual_open}")
            
            # 验证收盘价设置
            expected_close = bars[i+1].close if i < len(bars) - 1 else bar.close
            actual_close = bar.inclusion_close
            if abs(actual_close - expected_close) > 1e-6:
                errors.append(f"Bar {i}: 收盘价不匹配，期望{expected_close}，实际{actual_close}")
            
            # 验证成交量（参照分型处理方式）
            if bar.elements:
                expected_vol = sum([element.vol for element in bar.elements])
                actual_vol = bar.inclusion_vol
                if abs(actual_vol - expected_vol) > 1e-6:
                    errors.append(f"Bar {i}: 成交量不匹配，期望{expected_vol}，实际{actual_vol}")
                
                expected_amount = sum([element.amount for element in bar.elements])
                actual_amount = bar.inclusion_amount
                if abs(actual_amount - expected_amount) > 1e-6:
                    errors.append(f"Bar {i}: 成交额不匹配，期望{expected_amount}，实际{actual_amount}")
    
    return {
        'status': 'verified' if not errors else 'errors_found',
        'processed_count': processed_count,
        'total_count': len(bars),
        'processing_rate': processed_count / len(bars) if bars else 0,
        'errors': errors
    }


def create_enhanced_newbar_with_inclusion(symbol: str, bars_data: List[dict]) -> List[NewBar]:
    """创建增强的NewBar序列，自动包含OCHLV处理
    
    Args:
        symbol: 交易标的代码
        bars_data: K线数据字典列表，包含基本OHLCV信息
        
    Returns:
        已处理包含OCHLV的NewBar序列
    """
    from ..enum import Freq
    from datetime import datetime
    
    # 创建基础NewBar序列
    new_bars = []
    for i, data in enumerate(bars_data):
        bar = NewBar(
            symbol=symbol,
            id=i,
            dt=data.get('dt', datetime.now()),
            freq=data.get('freq', Freq.F1),
            open=data['open'],
            close=data['close'],
            high=data['high'],
            low=data['low'],
            vol=data.get('vol', 0),
            amount=data.get('amount', 0)
        )
        new_bars.append(bar)
    
    # 设置包含处理后的OCHLV
    processed_bars = set_inclusion_prices_for_bars(new_bars)
    
    return processed_bars


def compare_original_vs_inclusion_ohlcv(bars: List[NewBar]) -> dict:
    """比较原始OHLCV与包含处理后OHLCV的差异
    
    Args:
        bars: NewBar序列
        
    Returns:
        比较结果统计
    """
    if not bars:
        return {'status': 'empty'}
    
    comparisons = []
    
    for i, bar in enumerate(bars):
        original = {
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'vol': bar.vol,
            'amount': bar.amount
        }
        
        inclusion = bar.get_inclusion_ohlcv()
        
        comparison = {
            'bar_index': i,
            'dt': bar.dt,
            'original': original,
            'inclusion': inclusion,
            'differences': {
                'open_diff': inclusion['open'] - original['open'],
                'close_diff': inclusion['close'] - original['close'],
                'high_same': inclusion['high'] == original['high'],
                'low_same': inclusion['low'] == original['low'],
                'vol_diff': inclusion['vol'] - original['vol'],  # 成交量可能不同（包含关系处理）
                'amount_diff': inclusion['amount'] - original['amount']  # 成交额可能不同（包含关系处理）
            }
        }
        
        comparisons.append(comparison)
    
    # 统计差异
    open_changes = sum(1 for c in comparisons if abs(c['differences']['open_diff']) > 1e-6)
    close_changes = sum(1 for c in comparisons if abs(c['differences']['close_diff']) > 1e-6)
    vol_changes = sum(1 for c in comparisons if abs(c['differences']['vol_diff']) > 1e-6)
    amount_changes = sum(1 for c in comparisons if abs(c['differences']['amount_diff']) > 1e-6)
    
    return {
        'status': 'compared',
        'total_bars': len(bars),
        'open_price_changes': open_changes,
        'close_price_changes': close_changes,
        'volume_changes': vol_changes,
        'amount_changes': amount_changes,
        'change_rate': {
            'open': open_changes / len(bars) if bars else 0,
            'close': close_changes / len(bars) if bars else 0,
            'volume': vol_changes / len(bars) if bars else 0,
            'amount': amount_changes / len(bars) if bars else 0
        },
        'comparisons': comparisons
    }