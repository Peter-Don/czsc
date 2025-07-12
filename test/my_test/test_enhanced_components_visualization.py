#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强CZSC组件可视化测试
使用真实的BTCUSDT数据展示所有增强功能：
- 处理后的K线与分型
- FVG检测与缓解分析
- Order Block识别
- 分型级别增强
- NewBar包含处理OCHLV
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq, Direction, Mark
from czsc.utils.echarts_plot import kline_pro
from czsc.poi.fvg import FVGDetector, identify_fvg_basic
from czsc.poi.order_block import detect_order_blocks_from_czsc
from czsc.utils.inclusion_processing import set_inclusion_prices_for_bars, verify_inclusion_processing


def load_btc_data(file_path, max_rows=500):
    """加载BTC真实数据并转换为RawBar格式"""
    print(f"加载BTC数据: {file_path}")
    
    # 读取CSV数据
    df = pd.read_csv(file_path)
    
    # 限制数据量以便可视化
    if len(df) > max_rows:
        # 取中间一段数据，包含更多价格变化
        start_idx = len(df) // 3
        df = df.iloc[start_idx:start_idx + max_rows].copy()
    
    print(f"使用数据范围: {len(df)}行")
    
    # 转换为RawBar对象
    bars = []
    for i, row in df.iterrows():
        # 处理时间格式
        dt = pd.to_datetime(row['open_time'])
        
        bar = RawBar(
            symbol="BTCUSDT",
            id=i,
            dt=dt,
            freq=Freq.F1,  # 1分钟
            open=float(row['open']),
            close=float(row['close']),
            high=float(row['high']),
            low=float(row['low']),
            vol=float(row['volume']),
            amount=float(row['quote_volume'])
        )
        bars.append(bar)
    
    print(f"✅ 成功加载 {len(bars)} 条K线数据")
    print(f"时间范围: {bars[0].dt} 到 {bars[-1].dt}")
    print(f"价格范围: {min(bar.low for bar in bars):.1f} - {max(bar.high for bar in bars):.1f}")
    
    return bars


def analyze_enhanced_czsc(bars):
    """使用增强的CZSC分析K线数据"""
    print("\n" + "=" * 60)
    print("CZSC增强分析")
    print("=" * 60)
    
    # 创建CZSC分析器
    czsc = CZSC(bars, pen_model='standard')
    
    print(f"原始K线数量: {len(bars)}")
    print(f"处理后K线数量: {len(czsc.bars_ubi)}")
    print(f"K线压缩率: {(len(bars) - len(czsc.bars_ubi)) / len(bars) * 100:.1f}%")
    print(f"识别分型数量: {len(czsc.fx_list)}")
    print(f"构建笔数量: {len(czsc.bi_list)}")
    
    return czsc


def detect_enhanced_fvg(czsc):
    """检测增强的FVG"""
    print("\n" + "=" * 60)
    print("FVG增强检测")
    print("=" * 60)
    
    # 使用增强的FVG检测器
    fvg_detector = FVGDetector(config={
        'min_size_atr_factor': 0.3,  # 适中的阈值
        'auto_analysis': True,
        'analyzer_config': {
            'fractal_proximity_weight': 0.2,
            'stroke_context_weight': 0.3,
            'volume_analysis_weight': 0.2,
            'atr_significance_weight': 0.1
        }
    })
    
    # 构建CZSC上下文
    czsc_context = {
        'fractals': czsc.fx_list,
        'strokes': czsc.bi_list,
        'bars': czsc.bars_ubi,
        'timestamp': czsc.bars_ubi[-1].dt if czsc.bars_ubi else None
    }
    
    # 运行完整的FVG检测管道
    result = fvg_detector.run_full_pipeline(czsc.bars_ubi, czsc_context)
    
    identified_fvgs = result['identified']
    analyzed_fvgs = result['analyzed']
    
    print(f"识别的FVG数量: {len(identified_fvgs)}")
    print(f"分析的FVG数量: {len(analyzed_fvgs)}")
    print(f"高质量FVG数量: {result['stage_summary']['high_quality_count']}")
    
    # 测试缓解分析
    for fvg in analyzed_fvgs[:5]:  # 只测试前5个
        # 模拟价格测试FVG
        test_price = fvg.center
        fvg.update_mitigation(test_price, datetime.now())
        print(f"FVG {fvg.dt.strftime('%H:%M')}: {fvg.get_mitigation_type()} - {fvg.get_mitigation_description()}")
    
    return identified_fvgs, analyzed_fvgs


def detect_enhanced_order_blocks(czsc):
    """检测增强的Order Block"""
    print("\n" + "=" * 60)
    print("Order Block增强检测")
    print("=" * 60)
    
    # 配置Order Block检测器
    config = {
        'min_fractal_strength': 3,
        'sweep_atr_factor': 0.3,
        'sweep_reversion_bars': 8,
        'sweep_volume_multiplier': 1.2,
        'fvg_lookforward_bars': 15,
        'fvg_min_size_atr': 0.2,
        'volume_spike_multiplier': 1.5,
        'volume_lookback': 20
    }
    
    # 检测Order Block
    order_blocks = detect_order_blocks_from_czsc(czsc.bars_ubi, czsc.fx_list, config)
    
    print(f"检测到的Order Block数量: {len(order_blocks)}")
    
    for i, ob in enumerate(order_blocks[:3]):  # 显示前3个
        ob_type_str = "需求区域" if ob.ob_type == "DEMAND_ZONE" else "供应区域"
        print(f"OB{i}: {ob_type_str} @ {ob.dt.strftime('%H:%M')} "
              f"[{ob.low:.1f}-{ob.high:.1f}] "
              f"FVG确认:{ob.fvg_creation_confirmed}")
    
    return order_blocks


def enhance_fractal_levels(czsc):
    """增强分型级别分析"""
    print("\n" + "=" * 60)
    print("分型级别增强")
    print("=" * 60)
    
    # 手动设置一些分型级别进行演示
    enhanced_count = 0
    for i, fx in enumerate(czsc.fx_list):
        # 基于价格幅度和成交量设置级别
        vol_avg = np.mean([bar.vol for bar in czsc.bars_raw[-20:]])
        
        if fx.vol > vol_avg * 2:  # 成交量大的设为高级分型
            fx.gfc_level = 3
            fx.level_2_reasons = ['成交量激增']
            fx.level_3_reasons = ['成交量异常激增，机构参与']
            enhanced_count += 1
        elif fx.vol > vol_avg * 1.5:
            fx.gfc_level = 2
            fx.level_2_reasons = ['成交量显著增加']
            enhanced_count += 1
        elif i % 4 == 0:  # 每4个分型中设1个为二级
            fx.gfc_level = 2
            fx.level_2_reasons = ['位置重要性']
            enhanced_count += 1
    
    print(f"增强了 {enhanced_count} 个分型的级别")
    
    # 统计级别分布
    level_stats = {}
    for fx in czsc.fx_list:
        level = fx.gfc_level
        level_stats[level] = level_stats.get(level, 0) + 1
    
    for level, count in sorted(level_stats.items()):
        print(f"  {level}级分型: {count}个")
    
    return czsc.fx_list


def prepare_visualization_data(czsc, fvgs, order_blocks):
    """准备可视化数据"""
    print("\n" + "=" * 60)
    print("准备可视化数据")
    print("=" * 60)
    
    # K线数据
    kline = [x.__dict__ for x in czsc.bars_raw]
    print(f"K线数据: {len(kline)}条")
    
    # 笔数据
    bi = []
    if len(czsc.bi_list) > 0:
        bi = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx} for x in czsc.bi_list] + \
             [{'dt': czsc.bi_list[-1].fx_b.dt, "bi": czsc.bi_list[-1].fx_b.fx}]
    print(f"笔数据: {len(bi)}个点")
    
    # 增强分型数据
    fx_enhanced = []
    for fx in czsc.fx_list:
        fx_enhanced.append({
            'dt': fx.dt,
            'fx': fx.fx,
            'level': fx.gfc_level,
            'mark': fx.mark.value,
            'level_desc': fx.level_description,
            'enhancement_summary': fx.enhancement_summary,
            'level_2_reasons': fx.level_2_reasons,
            'level_3_reasons': fx.level_3_reasons,
            'open': fx.open,
            'close': fx.close,
            'high': fx.high,
            'low': fx.low,
            'vol': fx.vol
        })
    print(f"增强分型数据: {len(fx_enhanced)}个")
    
    # FVG数据
    fvg_data = []
    for fvg in fvgs:
        direction_str = "看涨" if fvg.direction == Direction.Up else "看跌"
        # 计算FVG的开始和结束时间
        start_dt = fvg.dt - timedelta(minutes=5)  # 假设FVG开始于检测时间前5分钟
        end_dt = fvg.dt + timedelta(minutes=5)    # 假设FVG结束于检测时间后5分钟
        
        fvg_data.append({
            'start_dt': start_dt,
            'end_dt': end_dt,
            'dt': fvg.dt,
            'high': fvg.high,
            'low': fvg.low,
            'direction': direction_str,
            'size': fvg.size,
            'center': fvg.center,
            'score': getattr(fvg, 'score', 0.5),
            'mitigation_type': fvg.get_mitigation_type() if hasattr(fvg, 'get_mitigation_type') else 'NONE'
        })
    print(f"FVG数据: {len(fvg_data)}个")
    
    # Order Block数据
    ob_data = []
    for ob in order_blocks:
        ob_type_str = "需求区域" if ob.ob_type == "DEMAND_ZONE" else "供应区域"
        ob_data.append({
            'dt': ob.dt,
            'high': ob.high,
            'low': ob.low,
            'type': ob_type_str,
            'poi_level': ob.poi_level,
            'strength_score': ob.strength_score,
            'reliability_score': ob.reliability_score,
            'fvg_confirmed': ob.fvg_creation_confirmed
        })
    print(f"Order Block数据: {len(ob_data)}个")
    
    return {
        'kline': kline,
        'bi': bi,
        'fx': fx_enhanced,
        'fvg': fvg_data,
        'ob': ob_data
    }


def create_enhanced_visualization(data, output_file="enhanced_btc_analysis.html"):
    """创建增强的可视化图表"""
    print("\n" + "=" * 60)
    print("生成可视化图表")
    print("=" * 60)
    
    # 使用增强的kline_pro函数
    chart = kline_pro(
        kline=data['kline'],
        bi=data['bi'],
        fx=data['fx'],  # 包含级别信息的分型数据
        fvg=data['fvg'],  # FVG数据
        ob=data['ob'],    # Order Block数据
        title="CZSC增强组件分析 - BTCUSDT",
        width="1600px",
        height="800px"
    )
    
    # 保存到result目录
    result_dir = os.path.join(os.path.dirname(__file__), 'result')
    os.makedirs(result_dir, exist_ok=True)
    output_path = os.path.join(result_dir, output_file)
    
    chart.render(output_path)
    
    print(f"✅ 可视化文件已生成: {output_path}")
    return output_path


def save_analysis_data(czsc, fvgs, order_blocks):
    """保存分析数据到CSV"""
    result_dir = os.path.join(os.path.dirname(__file__), 'result')
    os.makedirs(result_dir, exist_ok=True)
    
    # 保存分型数据
    fx_data = []
    for i, fx in enumerate(czsc.fx_list):
        fx_data.append({
            'id': i,
            'dt': fx.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'mark': fx.mark.value,
            'price': fx.fx,
            'high': fx.high,
            'low': fx.low,
            'vol': fx.vol,
            'level': fx.gfc_level,
            'level_desc': fx.level_description,
            'level_2_reasons': ';'.join(fx.level_2_reasons),
            'level_3_reasons': ';'.join(fx.level_3_reasons)
        })
    
    if fx_data:
        fx_df = pd.DataFrame(fx_data)
        fx_df.to_csv(os.path.join(result_dir, 'btc_enhanced_fractals.csv'), index=False, encoding='utf-8')
        print(f"分型数据已保存: btc_enhanced_fractals.csv")
    
    # 保存FVG数据
    if fvgs:
        fvg_data = []
        for i, fvg in enumerate(fvgs):
            direction_str = "看涨" if fvg.direction == Direction.Up else "看跌"
            fvg_data.append({
                'id': i,
                'dt': fvg.dt.strftime('%Y-%m-%d %H:%M:%S'),
                'direction': direction_str,
                'high': fvg.high,
                'low': fvg.low,
                'size': fvg.size,
                'center': fvg.center,
                'score': getattr(fvg, 'score', 0.5),
                'mitigation_type': fvg.get_mitigation_type() if hasattr(fvg, 'get_mitigation_type') else 'NONE'
            })
        
        fvg_df = pd.DataFrame(fvg_data)
        fvg_df.to_csv(os.path.join(result_dir, 'btc_detected_fvgs.csv'), index=False, encoding='utf-8')
        print(f"FVG数据已保存: btc_detected_fvgs.csv")
    
    # 保存Order Block数据
    if order_blocks:
        ob_data = []
        for i, ob in enumerate(order_blocks):
            ob_type_str = "需求区域" if ob.ob_type == "DEMAND_ZONE" else "供应区域"
            ob_data.append({
                'id': i,
                'dt': ob.dt.strftime('%Y-%m-%d %H:%M:%S'),
                'type': ob_type_str,
                'high': ob.high,
                'low': ob.low,
                'poi_level': ob.poi_level,
                'strength_score': ob.strength_score,
                'reliability_score': ob.reliability_score,
                'fvg_confirmed': ob.fvg_creation_confirmed
            })
        
        ob_df = pd.DataFrame(ob_data)
        ob_df.to_csv(os.path.join(result_dir, 'btc_detected_order_blocks.csv'), index=False, encoding='utf-8')
        print(f"Order Block数据已保存: btc_detected_order_blocks.csv")


def main():
    """主测试函数"""
    print("CZSC增强组件可视化测试")
    print("=" * 60)
    print("数据源: BTCUSDT 1分钟数据")
    print("功能: FVG、Order Block、分型级别、包含处理")
    print("输出: 交互式HTML可视化 + CSV数据")
    print("=" * 60)
    
    try:
        # 1. 加载真实BTC数据
        data_file = os.path.join(os.path.dirname(__file__), 'data', 'BTCUSDT_1m_2023-09.csv')
        bars = load_btc_data(data_file, max_rows=400)  # 使用400根K线以保证有足够的模式
        
        # 2. CZSC增强分析
        czsc = analyze_enhanced_czsc(bars)
        
        # 3. FVG检测
        identified_fvgs, analyzed_fvgs = detect_enhanced_fvg(czsc)
        
        # 4. Order Block检测
        order_blocks = detect_enhanced_order_blocks(czsc)
        
        # 5. 分型级别增强
        enhanced_fractals = enhance_fractal_levels(czsc)
        
        # 6. 准备可视化数据
        viz_data = prepare_visualization_data(czsc, analyzed_fvgs, order_blocks)
        
        # 7. 生成可视化
        output_file = create_enhanced_visualization(viz_data)
        
        # 8. 保存分析数据
        save_analysis_data(czsc, analyzed_fvgs, order_blocks)
        
        # 9. 生成报告
        print("\n" + "=" * 60)
        print("分析完成报告")
        print("=" * 60)
        print(f"📊 原始K线: {len(bars)}根")
        print(f"📈 处理后K线: {len(czsc.bars_ubi)}根 (压缩率: {(len(bars) - len(czsc.bars_ubi)) / len(bars) * 100:.1f}%)")
        print(f"📍 识别分型: {len(czsc.fx_list)}个")
        print(f"📏 构建笔: {len(czsc.bi_list)}条")
        print(f"🔳 检测FVG: {len(analyzed_fvgs)}个")
        print(f"📦 发现Order Block: {len(order_blocks)}个")
        
        level_stats = {}
        for fx in czsc.fx_list:
            level = fx.gfc_level
            level_stats[level] = level_stats.get(level, 0) + 1
        
        print(f"🎯 分型级别分布:")
        for level, count in sorted(level_stats.items()):
            print(f"   {level}级分型: {count}个")
        
        print(f"\n🎨 可视化文件: {output_file}")
        print(f"📁 数据文件: test/result/ 目录下的CSV文件")
        print("\n✅ 测试完成! 请打开HTML文件查看交互式可视化效果")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 保存错误信息
        result_dir = os.path.join(os.path.dirname(__file__), 'result')
        os.makedirs(result_dir, exist_ok=True)
        
        with open(os.path.join(result_dir, 'visualization_error.txt'), 'w', encoding='utf-8') as f:
            f.write(f"错误时间: {datetime.now()}\n")
            f.write(f"错误信息: {str(e)}\n")
            f.write(f"详细追踪:\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()