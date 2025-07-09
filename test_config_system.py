# coding: utf-8
"""
测试配置文件系统
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from czsc.config_loader import pen_config, PenConfigLoader
from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq
from datetime import datetime, timedelta

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    if pen_config is None:
        print("警告：配置文件加载失败，使用默认配置")
        return
    
    # 打印配置信息
    pen_config.print_config_info()
    
    # 测试不同市场配置
    print("\n--- 测试不同市场配置 ---")
    for market in ['stock', 'crypto', 'futures']:
        config = pen_config.get_pen_config_for_market(market, 'moderate')
        print(f"{market}市场配置: {config}")
    
    # 测试不同阈值模式
    print("\n--- 测试不同阈值模式 ---")
    for mode in ['conservative', 'moderate', 'aggressive']:
        config = pen_config.get_pen_config_for_market('stock', mode)
        print(f"{mode}模式配置: {config}")

def create_test_bars():
    """创建测试数据"""
    bars = []
    base_time = datetime(2024, 1, 1, 9, 0, 0)
    
    # 创建更多测试数据
    test_prices = [
        {'open': 100, 'high': 102, 'low': 99, 'close': 101, 'vol': 1000},
        {'open': 101, 'high': 103, 'low': 100, 'close': 102, 'vol': 1100},
        {'open': 102, 'high': 105, 'low': 101, 'close': 104, 'vol': 1200},
        {'open': 104, 'high': 106, 'low': 103, 'close': 105, 'vol': 1300},
        {'open': 105, 'high': 107, 'low': 104, 'close': 106, 'vol': 1400},
        {'open': 106, 'high': 108, 'low': 95, 'close': 96, 'vol': 5000},   # 极端反转
        {'open': 96, 'high': 98, 'low': 94, 'close': 97, 'vol': 1500},
        {'open': 97, 'high': 99, 'low': 95, 'close': 98, 'vol': 1600},
        {'open': 98, 'high': 100, 'low': 96, 'close': 99, 'vol': 1700},
        {'open': 99, 'high': 101, 'low': 97, 'close': 100, 'vol': 1800},
        {'open': 100, 'high': 95, 'low': 92, 'close': 94, 'vol': 4000},    # 另一个极端
        {'open': 94, 'high': 96, 'low': 92, 'close': 95, 'vol': 1900},
        {'open': 95, 'high': 97, 'low': 93, 'close': 96, 'vol': 2000},
        {'open': 96, 'high': 98, 'low': 94, 'close': 97, 'vol': 2100},
        {'open': 97, 'high': 99, 'low': 95, 'close': 98, 'vol': 2200},
    ]
    
    for i, price_data in enumerate(test_prices):
        bar = RawBar(
            symbol='TEST',
            id=i,
            freq=Freq.F1,
            dt=base_time + timedelta(minutes=i),
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            vol=price_data['vol'],
            amount=price_data['close'] * price_data['vol']
        )
        bars.append(bar)
    
    return bars

def test_different_configs():
    """测试不同配置的效果"""
    print("\n=== 测试不同配置效果 ===")
    
    bars = create_test_bars()
    
    # 测试1: 默认配置
    print("\n--- 默认配置 ---")
    c1 = CZSC(bars)
    print(f"默认配置 - 笔数量: {len(c1.bi_list)}")
    print(f"配置: pen_model={c1.pen_model}, adaptive_pen={c1.use_adaptive_pen}")
    print(f"参数: vol_ratio={c1.adaptive_vol_ratio}, atr_ratio={c1.adaptive_atr_ratio}")
    
    # 测试2: 股票市场配置
    print("\n--- 股票市场配置 ---")
    c2 = CZSC(bars, market_type='stock')
    print(f"股票市场配置 - 笔数量: {len(c2.bi_list)}")
    print(f"配置: pen_model={c2.pen_model}, adaptive_pen={c2.use_adaptive_pen}")
    print(f"参数: vol_ratio={c2.adaptive_vol_ratio}, atr_ratio={c2.adaptive_atr_ratio}")
    
    # 测试3: 加密货币市场配置
    print("\n--- 加密货币市场配置 ---")
    c3 = CZSC(bars, market_type='crypto')
    print(f"加密货币市场配置 - 笔数量: {len(c3.bi_list)}")
    print(f"配置: pen_model={c3.pen_model}, adaptive_pen={c3.use_adaptive_pen}")
    print(f"参数: vol_ratio={c3.adaptive_vol_ratio}, atr_ratio={c3.adaptive_atr_ratio}")
    
    # 测试4: 灵活模式 + 自适应笔
    print("\n--- 灵活模式 + 自适应笔 ---")
    c4 = CZSC(bars, pen_model='flexible', use_adaptive_pen=True, 
              market_type='stock', threshold_mode='conservative')
    print(f"灵活+自适应配置 - 笔数量: {len(c4.bi_list)}")
    print(f"配置: pen_model={c4.pen_model}, adaptive_pen={c4.use_adaptive_pen}")
    print(f"参数: vol_ratio={c4.adaptive_vol_ratio}, atr_ratio={c4.adaptive_atr_ratio}")
    
    # 测试5: 完全自定义参数
    print("\n--- 完全自定义参数 ---")
    c5 = CZSC(bars, pen_model='flexible', use_adaptive_pen=True,
              adaptive_vol_ratio=1.5, adaptive_atr_ratio=1.2)
    print(f"自定义参数配置 - 笔数量: {len(c5.bi_list)}")
    print(f"配置: pen_model={c5.pen_model}, adaptive_pen={c5.use_adaptive_pen}")
    print(f"参数: vol_ratio={c5.adaptive_vol_ratio}, atr_ratio={c5.adaptive_atr_ratio}")

def test_config_modification():
    """测试配置修改"""
    print("\n=== 测试配置修改 ===")
    
    if pen_config is None:
        print("跳过配置修改测试（配置文件不可用）")
        return
    
    # 获取原始配置
    original_config = pen_config.get_adaptive_mode_config()
    print(f"原始自适应配置: {original_config}")
    
    # 修改配置
    pen_config.update_adaptive_config(
        volume_ratio=2.5,
        atr_ratio=1.8,
        enabled=True
    )
    
    # 获取修改后的配置
    modified_config = pen_config.get_adaptive_mode_config()
    print(f"修改后自适应配置: {modified_config}")
    
    # 恢复原始配置
    pen_config.update_adaptive_config(
        volume_ratio=original_config['volume_ratio'],
        atr_ratio=original_config['atr_ratio'],
        enabled=original_config['enabled']
    )
    
    print("已恢复原始配置")

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    # 测试不存在的配置文件
    try:
        config_loader = PenConfigLoader("/nonexistent/path/config.json")
        print("错误：应该抛出异常")
    except FileNotFoundError as e:
        print(f"正确处理文件不存在错误: {e}")
    
    # 测试不存在的市场类型
    if pen_config is not None:
        config = pen_config.get_market_specific_config('nonexistent')
        print(f"不存在的市场类型返回: {config}")  # 应该返回空字典
    
    # 测试不存在的阈值模式
    if pen_config is not None:
        config = pen_config.get_adaptive_threshold('nonexistent')
        print(f"不存在的阈值模式返回: {config}")  # 应该返回空字典

if __name__ == "__main__":
    print("开始测试配置文件系统...")
    
    try:
        # 测试配置加载
        test_config_loading()
        
        # 测试不同配置效果
        test_different_configs()
        
        # 测试配置修改
        test_config_modification()
        
        # 测试错误处理
        test_error_handling()
        
        print("\n=== 测试完成 ===")
        print("配置文件系统测试成功！")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()