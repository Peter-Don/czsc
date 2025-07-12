#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
原地扩展方案演示 - 在现有czsc架构基础上直接扩展分级分型功能

核心思想：
1. 直接在原有FX、BI类上新增分级属性
2. 在CZSC类update方法中新增分级逻辑  
3. 保持原有API完全不变，新功能通过新属性访问
4. 高效、低开发成本、不容易出错
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from czsc.analyze import CZSC
from czsc.objects import RawBar, FX, BI
from czsc.enum import Freq
from datetime import datetime
import pandas as pd


def create_sample_bars():
    """创建示例K线数据"""
    dates = pd.date_range('2023-01-01', periods=100, freq='1h')
    bars = []
    
    # 模拟价格走势
    price = 100.0
    for i, dt in enumerate(dates):
        # 添加一些波动
        change = (i % 10 - 5) * 0.5 + (i % 3 - 1) * 0.2
        price += change
        
        # 确保价格合理性
        high = price + abs(change) * 0.5
        low = price - abs(change) * 0.5
        open_price = price - change * 0.3
        close_price = price
        
        bar = RawBar(
            symbol="DEMO",
            id=i,
            dt=dt,
            freq=Freq.F60,
            open=round(open_price, 2),
            close=round(close_price, 2), 
            high=round(high, 2),
            low=round(low, 2),
            vol=1000 + i * 10,
            amount=1000000 + i * 10000
        )
        bars.append(bar)
    
    return bars


def demo_basic_compatibility():
    """演示基础兼容性 - 原有功能完全不变"""
    print("=" * 60)
    print("1. 基础兼容性测试 - 原有功能完全不变")
    print("=" * 60)
    
    bars = create_sample_bars()
    czsc = CZSC(bars=bars)
    
    # 原有API完全正常使用
    print(f"分型数量: {len(czsc.fx_list)}")
    print(f"笔数量: {len(czsc.bi_list)}")
    print(f"最后一根K线: {czsc.bars_raw[-1].dt}")
    
    # 原有分型属性正常访问
    if czsc.fx_list:
        fx = czsc.fx_list[0]
        print(f"第一个分型: {fx.mark.value} @ {fx.dt} = {fx.fx}")
        print(f"分型力度: {fx.power_str}")
        print(f"是否有中枢: {fx.has_zs}")
    
    # 原有笔属性正常访问  
    if czsc.bi_list:
        bi = czsc.bi_list[0]
        print(f"第一笔: {bi.direction.value} @ {bi.sdt} -> {bi.edt}")
        print(f"笔力度: {bi.power_price}")
        print(f"笔角度: {bi.angle}°")


def demo_enhanced_features():
    """演示增强功能 - 新增的分级分型功能"""
    print("\n" + "=" * 60)
    print("2. 增强功能演示 - 新增分级分型功能")
    print("=" * 60)
    
    bars = create_sample_bars()
    czsc = CZSC(bars=bars)
    
    # 新增功能：分级分型查询
    print(f"二级及以上分型数量: {len(czsc.level_2_fxs)}")
    print(f"三级及以上分型数量: {len(czsc.level_3_fxs)}")
    print(f"二级及以上笔数量: {len(czsc.level_2_bis)}")
    print(f"三级及以上笔数量: {len(czsc.level_3_bis)}")
    
    # 新增功能：级别统计
    stats = czsc.get_level_statistics()
    print(f"分型级别统计: {stats['fx_statistics']}")
    print(f"笔级别统计: {stats['bi_statistics']}")
    
    # 新增功能：查看具体分型的增强信息
    for i, fx in enumerate(czsc.fx_list[:5]):  # 查看前5个分型
        print(f"分型 {i+1}: {fx.level_description} - {fx.enhancement_summary}")
        print(f"  级别: {fx.gfc_level}")
        print(f"  二级原因: {fx.level_2_reasons}")
        print(f"  三级原因: {fx.level_3_reasons}")
        print(f"  便捷判断: 二级={fx.is_level_2}, 三级={fx.is_level_3}")
    
    # 新增功能：查看具体笔的增强信息  
    for i, bi in enumerate(czsc.bi_list[:3]):  # 查看前3笔
        print(f"笔 {i+1}: {bi.level_description} - {bi.enhancement_summary}")
        print(f"  级别: {bi.gbc_level}")
        print(f"  二级原因: {bi.level_2_reasons}")
        print(f"  三级原因: {bi.level_3_reasons}")
        print(f"  便捷判断: 二级={bi.is_level_2}, 三级={bi.is_level_3}")


def demo_advanced_queries():
    """演示高级查询功能"""
    print("\n" + "=" * 60)
    print("3. 高级查询功能演示")
    print("=" * 60)
    
    bars = create_sample_bars()
    czsc = CZSC(bars=bars)
    
    # 按级别查询
    for level in [1, 2, 3]:
        fxs = czsc.get_fxs_by_level(level)
        bis = czsc.get_bis_by_level(level)
        print(f"Level {level}: {len(fxs)}个分型, {len(bis)}笔")
    
    # 获取最新高级分型和笔
    latest_high_fx = czsc.get_latest_high_level_fx(min_level=2)
    latest_high_bi = czsc.get_latest_high_level_bi(min_level=2)
    
    if latest_high_fx:
        print(f"最新高级分型: {latest_high_fx.level_description} @ {latest_high_fx.dt}")
    
    if latest_high_bi:
        print(f"最新高级笔: {latest_high_bi.level_description} @ {latest_high_bi.sdt}")


def demo_data_export():
    """演示数据导出功能"""
    print("\n" + "=" * 60)
    print("4. 数据导出功能演示")
    print("=" * 60)
    
    bars = create_sample_bars()
    czsc = CZSC(bars=bars)
    
    # 导出组件信息到CSV
    csv_file = czsc.save_components_to_csv("demo_components.csv")
    print(f"组件信息已导出到: {csv_file}")
    
    # 加载并查看
    df = czsc.load_components_from_csv(csv_file)
    if df is not None:
        print(f"CSV文件包含 {len(df)} 行数据")
        print("数据类型分布:")
        print(df['type'].value_counts())


def demo_original_extension_approach():
    """展示原地扩展方案的核心优势"""
    print("\n" + "=" * 60)
    print("5. 原地扩展方案核心优势展示")
    print("=" * 60)
    
    bars = create_sample_bars()
    czsc = CZSC(bars=bars)
    
    print("✅ 完全兼容: 所有原有代码无需修改")
    print("✅ 直接扩展: 在原有类上新增属性，不是包装")
    print("✅ 共用资源: 复用原有cache、属性计算等")
    print("✅ 高效开发: 最小化代码变更，降低出错风险")
    print("✅ 渐进增强: 可选择性地使用新功能")
    
    # 展示同一个分型对象既有原有属性又有新属性
    if czsc.fx_list:
        fx = czsc.fx_list[0]
        print(f"\n同一个分型对象 {fx}:")
        print(f"  原有属性: mark={fx.mark.value}, fx={fx.fx}, power_str={fx.power_str}")  
        print(f"  新增属性: gfc_level={fx.gfc_level}, level_description={fx.level_description}")
        print(f"  -> 完美融合，无缝衔接!")
    
    # 展示同一个笔对象既有原有属性又有新属性
    if czsc.bi_list:
        bi = czsc.bi_list[0]
        print(f"\n同一个笔对象 {bi}:")
        print(f"  原有属性: direction={bi.direction.value}, power={bi.power}, angle={bi.angle}")
        print(f"  新增属性: gbc_level={bi.gbc_level}, level_description={bi.level_description}")
        print(f"  -> 完美融合，无缝衔接!")


if __name__ == "__main__":
    print("原地扩展方案演示 - 在现有czsc架构基础上直接扩展分级分型功能")
    print("设计理念: 复用原有架构，直接扩展，高效开发，完全兼容")
    
    try:
        demo_basic_compatibility()
        demo_enhanced_features()
        demo_advanced_queries()
        demo_data_export()
        demo_original_extension_approach()
        
        print("\n" + "=" * 60)
        print("演示完成！原地扩展方案运行成功！")
        print("=" * 60)
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()