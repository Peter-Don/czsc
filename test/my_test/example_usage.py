#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分级分型增强功能使用示例
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from datetime import datetime, timedelta
from czsc.objects import RawBar
from czsc.analyze import CZSC
from czsc.enum import Freq
import random

def create_sample_data():
    """创建示例数据"""
    bars = []
    base_price = 100.0
    base_time = datetime.now()
    
    # 创建一个有趋势的价格序列
    for i in range(100):
        if i < 30:
            # 上升趋势
            trend = 0.002
        elif i < 60:
            # 横盘整理
            trend = 0
        else:
            # 下降趋势
            trend = -0.002
        
        # 添加随机波动
        noise = random.uniform(-0.01, 0.01)
        base_price *= (1 + trend + noise)
        
        # 生成OHLC
        high = base_price * random.uniform(1.0, 1.015)
        low = base_price * random.uniform(0.985, 1.0)
        open_price = base_price * random.uniform(0.995, 1.005)
        close_price = base_price
        
        bar = RawBar(
            symbol="SAMPLE",
            id=i + 1,
            dt=base_time + timedelta(hours=i),
            freq=Freq.F60,
            open=open_price,
            close=close_price,
            high=high,
            low=low,
            vol=random.uniform(1000, 5000),
            amount=random.uniform(100000, 500000)
        )
        bars.append(bar)
    
    return bars

def main():
    """主函数，演示分级分型增强功能的使用"""
    print("=" * 80)
    print("分级分型增强功能使用示例")
    print("=" * 80)
    
    # 1. 创建数据并初始化CZSC
    print("\n1. 创建CZSC分析对象")
    print("-" * 40)
    
    bars = create_sample_data()
    czsc = CZSC(bars=bars, pen_model='standard')
    
    print(f"分析对象: {czsc}")
    print(f"K线数量: {len(czsc.bars_raw)}")
    print(f"分型数量: {len(czsc.fx_list)}")
    print(f"笔数量: {len(czsc.bi_list)}")
    
    # 2. 查看传统功能（确保兼容性）
    print("\n2. 传统功能展示（确保兼容性）")
    print("-" * 40)
    
    if czsc.fx_list:
        latest_fx = czsc.fx_list[-1]
        print(f"最新分型: {latest_fx.mark.value} @ {latest_fx.fx:.2f}")
        print(f"分型力度: {latest_fx.power_str}")
        print(f"分型成交量: {latest_fx.power_volume:.0f}")
    
    if czsc.bi_list:
        latest_bi = czsc.bi_list[-1]
        print(f"最新笔: {latest_bi.direction.value} @ {latest_bi.power:.2f}")
        print(f"笔长度: {latest_bi.length}")
        print(f"笔信噪比: {latest_bi.SNR:.3f}")
    
    # 3. 分级分型增强功能展示
    print("\n3. 分级分型增强功能展示")
    print("-" * 40)
    
    # 获取分级统计信息
    stats = czsc.get_level_statistics()
    print(f"分级统计信息:")
    print(f"  总分型数: {stats['total_fxs']}")
    print(f"  总笔数: {stats['total_bis']}")
    print(f"  高级分型数: {stats['high_level_fxs']}")
    print(f"  高级笔数: {stats['high_level_bis']}")
    
    # 显示各级别分型分布
    print(f"\n分型级别分布:")
    for level in range(1, 4):
        count = stats['fx_statistics'][f'level_{level}']
        print(f"  {level}级分型: {count}个")
    
    print(f"\n笔级别分布:")
    for level in range(1, 4):
        count = stats['bi_statistics'][f'level_{level}']
        print(f"  {level}级笔: {count}个")
    
    # 4. 高级分型查询
    print("\n4. 高级分型查询功能")
    print("-" * 40)
    
    # 查询二级分型
    level_2_fxs = czsc.level_2_fxs
    print(f"二级分型数量: {len(level_2_fxs)}")
    if level_2_fxs:
        fx = level_2_fxs[-1]
        print(f"最新二级分型: {fx.enhancement_summary}")
        print(f"二级原因: {fx.level_2_reasons}")
    
    # 查询三级分型
    level_3_fxs = czsc.level_3_fxs
    print(f"三级分型数量: {len(level_3_fxs)}")
    if level_3_fxs:
        fx = level_3_fxs[-1]
        print(f"最新三级分型: {fx.enhancement_summary}")
        print(f"三级原因: {fx.level_3_reasons}")
    
    # 5. 高级笔查询
    print("\n5. 高级笔查询功能")
    print("-" * 40)
    
    # 查询二级笔
    level_2_bis = czsc.level_2_bis
    print(f"二级笔数量: {len(level_2_bis)}")
    if level_2_bis:
        bi = level_2_bis[-1]
        print(f"最新二级笔: {bi.enhancement_summary}")
        print(f"二级原因: {bi.level_2_reasons}")
    
    # 查询三级笔
    level_3_bis = czsc.level_3_bis
    print(f"三级笔数量: {len(level_3_bis)}")
    if level_3_bis:
        bi = level_3_bis[-1]
        print(f"最新三级笔: {bi.enhancement_summary}")
        print(f"三级原因: {bi.level_3_reasons}")
    
    # 6. 便捷查询方法
    print("\n6. 便捷查询方法")
    print("-" * 40)
    
    # 获取最新高级分型
    latest_high_fx = czsc.get_latest_high_level_fx(min_level=2)
    if latest_high_fx:
        print(f"最新高级分型: {latest_high_fx.enhancement_summary}")
        print(f"分型时间: {latest_high_fx.dt}")
        print(f"分型价格: {latest_high_fx.fx:.2f}")
    
    # 获取最新高级笔
    latest_high_bi = czsc.get_latest_high_level_bi(min_level=2)
    if latest_high_bi:
        print(f"最新高级笔: {latest_high_bi.enhancement_summary}")
        print(f"笔时间: {latest_high_bi.fx_a.dt} -> {latest_high_bi.fx_b.dt}")
        print(f"笔价格: {latest_high_bi.fx_a.fx:.2f} -> {latest_high_bi.fx_b.fx:.2f}")
    
    # 7. 分级分型在交易中的应用示例
    print("\n7. 交易应用示例")
    print("-" * 40)
    
    # 寻找重要的支撑阻力位
    high_level_fxs = czsc.level_2_fxs + czsc.level_3_fxs
    if high_level_fxs:
        # 按时间排序
        high_level_fxs.sort(key=lambda x: x.dt)
        recent_high_level_fxs = high_level_fxs[-5:]  # 最近5个高级分型
        
        print("最近的重要支撑阻力位:")
        for fx in recent_high_level_fxs:
            position_type = "阻力位" if fx.mark.value == "顶分型" else "支撑位"
            print(f"  {position_type}: {fx.fx:.2f} ({fx.level_description}, {fx.dt.strftime('%m-%d %H:%M')})")
    
    # 分析当前市场状态
    if czsc.bi_list:
        current_bi = czsc.bi_list[-1]
        print(f"\n当前市场状态:")
        print(f"  最新笔方向: {current_bi.direction.value}")
        print(f"  笔级别: {current_bi.level_description}")
        print(f"  笔力度: {current_bi.power:.2f}")
        
        # 基于笔级别判断重要性
        if current_bi.gbc_level >= 3:
            print(f"  ⚠️ 当前笔为三级笔，属于重要级别的价格运动")
        elif current_bi.gbc_level >= 2:
            print(f"  ⚠️ 当前笔为二级笔，需要关注")
        else:
            print(f"  ℹ️ 当前笔为一级笔，属于常规价格运动")
    
    # 8. 保存分析结果
    print("\n8. 保存分析结果")
    print("-" * 40)
    
    # 保存到CSV文件
    csv_file = czsc.save_components_to_csv("sample_analysis.csv")
    print(f"分析结果已保存到: {csv_file}")
    
    # 9. 实时更新示例
    print("\n9. 实时更新示例")
    print("-" * 40)
    
    # 模拟新K线到来
    print("模拟新K线数据到来...")
    last_bar = bars[-1]
    
    # 创建新的K线
    new_bar = RawBar(
        symbol="SAMPLE",
        id=last_bar.id + 1,
        dt=last_bar.dt + timedelta(hours=1),
        freq=Freq.F60,
        open=last_bar.close,
        close=last_bar.close * 1.005,  # 价格上涨0.5%
        high=last_bar.close * 1.008,
        low=last_bar.close * 0.998,
        vol=random.uniform(1000, 5000),
        amount=random.uniform(100000, 500000)
    )
    
    # 更新分析
    old_fx_count = len(czsc.fx_list)
    old_bi_count = len(czsc.bi_list)
    
    czsc.update(new_bar)
    
    new_fx_count = len(czsc.fx_list)
    new_bi_count = len(czsc.bi_list)
    
    print(f"更新后:")
    print(f"  分型数量: {old_fx_count} -> {new_fx_count}")
    print(f"  笔数量: {old_bi_count} -> {new_bi_count}")
    
    # 检查是否有新的高级分型或笔
    if new_fx_count > old_fx_count:
        latest_fx = czsc.fx_list[-1]
        if latest_fx.gfc_level >= 2:
            print(f"  🔥 新增高级分型: {latest_fx.enhancement_summary}")
    
    if new_bi_count > old_bi_count:
        latest_bi = czsc.bi_list[-1]
        if latest_bi.gbc_level >= 2:
            print(f"  🔥 新增高级笔: {latest_bi.enhancement_summary}")
    
    print("\n" + "=" * 80)
    print("分级分型增强功能演示完成！")
    print("=" * 80)

if __name__ == "__main__":
    # 设置随机种子
    random.seed(42)
    
    # 运行示例
    main()