#!/usr/bin/env python
# coding: utf-8
"""
测试从CSV加载组件信息
"""

import os
import sys
import pandas as pd

# 添加项目根路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)


def test_load_components():
    """测试从CSV加载组件信息"""
    print("=" * 60)
    print("测试从CSV加载组件信息")
    print("=" * 60)
    
    # 读取保存的组件信息
    components_file = os.path.join(current_dir, "result", "fvg_ob_components.csv")
    
    if not os.path.exists(components_file):
        print(f"❌ 组件文件不存在: {components_file}")
        return
    
    df = pd.read_csv(components_file)
    
    print(f"✅ 成功加载组件信息:")
    print(f"   - 文件路径: {components_file}")
    print(f"   - 总组件数: {len(df)}")
    print(f"   - 分型(FX): {len(df[df['type'] == 'FX'])} 个")
    print(f"   - 笔(BI): {len(df[df['type'] == 'BI'])} 个")
    print(f"   - FVG: {len(df[df['type'] == 'FVG'])} 个")
    print(f"   - OB: {len(df[df['type'] == 'OB'])} 个")
    
    # 分析FVG信息
    fvg_df = df[df['type'] == 'FVG']
    if len(fvg_df) > 0:
        print(f"\n📊 FVG分析:")
        print(f"   - 看涨FVG: {len(fvg_df[fvg_df['direction'] == 'Up'])} 个")
        print(f"   - 看跌FVG: {len(fvg_df[fvg_df['direction'] == 'Down'])} 个")
        
        # 分析FVG的有效性
        valid_fvgs = 0
        mitigated_fvgs = 0
        
        for _, row in fvg_df.iterrows():
            raw_data = row['raw_data']
            if 'valid:True' in raw_data:
                valid_fvgs += 1
            if 'mitigated:True' in raw_data:
                mitigated_fvgs += 1
        
        print(f"   - 有效FVG: {valid_fvgs} 个")
        print(f"   - 已缓解FVG: {mitigated_fvgs} 个")
        print(f"   - 活跃FVG: {valid_fvgs - mitigated_fvgs} 个")
        
        # 显示最近的FVG
        print(f"\n📋 最近的10个FVG:")
        for i, (_, row) in enumerate(fvg_df.tail(10).iterrows()):
            direction_symbol = "↑" if row['direction'] == 'Up' else "↓"
            dt_str = pd.to_datetime(row['dt']).strftime('%m-%d %H:%M')
            # 解析raw_data中的信息
            raw_data = row['raw_data']
            valid = 'valid:True' in raw_data
            mitigated = 'mitigated:True' in raw_data
            status = "活跃" if valid and not mitigated else "已缓解"
            
            print(f"   {i+1}. {direction_symbol} {dt_str} [{row['low']:.2f}, {row['high']:.2f}] "
                  f"方向:{row['direction']} 状态:{status}")
    
    # 分析分型信息
    fx_df = df[df['type'] == 'FX']
    if len(fx_df) > 0:
        print(f"\n📊 分型分析:")
        print(f"   - 顶分型: {len(fx_df[fx_df['mark'] == '顶分型'])} 个")
        print(f"   - 底分型: {len(fx_df[fx_df['mark'] == '底分型'])} 个")
    
    # 分析笔信息
    bi_df = df[df['type'] == 'BI']
    if len(bi_df) > 0:
        print(f"\n📊 笔分析:")
        print(f"   - 向上笔: {len(bi_df[bi_df['direction'] == '向上'])} 个")
        print(f"   - 向下笔: {len(bi_df[bi_df['direction'] == '向下'])} 个")
    
    print(f"\n🎯 总结:")
    print(f"   通过CSV文件可以快速获取历史组件信息")
    print(f"   包含了分型、笔、FVG等所有组件的详细数据")
    print(f"   可以用于快速分析和历史回测")


if __name__ == "__main__":
    test_load_components()