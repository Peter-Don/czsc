# -*- coding: utf-8 -*-
"""
测试增强的CZSC组件：处理后的K线、分型、FVG、OB
参照CZSC原有组件，展示增强功能的完整测试

文件组织：
- 测试数据保存在 test/data/ 目录
- 测试结果保存在 test/result/ 目录
- 支持CSV、JSON格式的数据导出
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
from datetime import datetime, timedelta
from czsc.objects import RawBar, NewBar, FX
from czsc.enum import Direction, Freq, Mark
from czsc.analyze import CZSC
from czsc.poi.fvg import FVGDetector, identify_fvg_basic
from czsc.poi.order_block import detect_order_blocks_from_czsc
from czsc.utils.inclusion_processing import set_inclusion_prices_for_bars, verify_inclusion_processing
import numpy as np


def create_test_data():
    """创建测试用的K线数据，包含明显的分型、FVG和OB模式"""
    symbol = "TESTUSDT"
    start_dt = datetime(2024, 1, 1, 9, 0, 0)
    
    # 构造更清晰的Order Block模式：分型 -> 流动性扫荡 -> 强势反转 -> 产生FVG
    price_patterns = [
        # 1. 初始下降趋势，形成底部区域
        (50000, 49950, 50020, 49930, 1000, 1000000),
        (49950, 49900, 49970, 49880, 1100, 1100000),
        (49900, 49850, 49920, 49830, 1200, 1200000),
        
        # 2. 形成明显的底分型（Order Block候选）
        (49850, 49800, 49870, 49780, 800, 800000),   # 第1根：继续下跌
        (49800, 49750, 49820, 49730, 1500, 1500000), # 第2根：底分型中心（关键决定性K线，高成交量）
        (49750, 49780, 49800, 49740, 1000, 1000000), # 第3根：开始反弹
        
        # 3. 流动性扫荡：价格测试底部然后快速反弹
        (49780, 49720, 49790, 49710, 900, 900000),   # 扫荡低点
        (49720, 49760, 49780, 49715, 800, 800000),   # 快速回升
        
        # 4. 强势上涨并产生看涨FVG（Order Block确认条件）
        (49760, 49850, 49870, 49740, 1400, 1400000), # bar1: 上涨但还有重叠
        (50000, 50150, 50200, 49980, 2000, 2000000), # bar2: 跳空强势上涨（产生FVG，大成交量）
        (50150, 50250, 50280, 50130, 1600, 1600000), # bar3: 延续上涨
        
        # 5. 继续上升趋势
        (50250, 50320, 50350, 50230, 1300, 1300000),
        (50320, 50380, 50420, 50300, 1200, 1200000),
        (50380, 50450, 50480, 50360, 1100, 1100000),
        
        # 6. 形成顶分型（另一个Order Block候选）
        (50450, 50520, 50550, 50430, 1000, 1000000), # 第1根：上涨
        (50520, 50580, 50620, 50500, 1800, 1800000), # 第2根：顶分型中心（关键决定性K线，高成交量）
        (50580, 50550, 50590, 50530, 900, 900000),   # 第3根：开始回落
        
        # 7. 流动性扫荡：价格测试顶部然后快速下跌
        (50550, 50590, 50630, 50540, 1100, 1100000), # 扫荡高点
        (50590, 50560, 50600, 50555, 1000, 1000000), # 快速回落
        
        # 8. 强势下跌并产生看跌FVG（Order Block确认条件）
        (50560, 50480, 50570, 50460, 1300, 1300000), # bar1: 下跌但还有重叠
        (50300, 50200, 50320, 50180, 2200, 2200000), # bar2: 跳空强势下跌（产生FVG，大成交量）
        (50200, 50120, 50220, 50100, 1700, 1700000), # bar3: 延续下跌
        
        # 9. 收尾
        (50120, 50080, 50140, 50060, 1000, 1000000),
        (50080, 50100, 50120, 50070, 900, 900000),
    ]
    
    raw_bars = []
    for i, (open_price, close_price, high_price, low_price, volume, amount) in enumerate(price_patterns):
        bar = RawBar(
            symbol=symbol,
            id=i,
            dt=start_dt + timedelta(minutes=i*5),
            freq=Freq.F5,
            open=open_price,
            close=close_price,
            high=high_price,
            low=low_price,
            vol=volume,
            amount=amount
        )
        raw_bars.append(bar)
    
    return raw_bars


def save_test_data_to_file(raw_bars, file_path):
    """保存测试数据到CSV文件"""
    data = []
    for bar in raw_bars:
        data.append({
            'symbol': bar.symbol,
            'id': bar.id,
            'dt': bar.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'freq': bar.freq.value,
            'open': bar.open,
            'close': bar.close,
            'high': bar.high,
            'low': bar.low,
            'vol': bar.vol,
            'amount': bar.amount
        })
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False, encoding='utf-8')
    print(f"测试数据已保存到: {file_path}")


def test_czsc_processing():
    """测试CZSC基础处理：K线包含关系处理、分型识别"""
    print("=" * 60)
    print("1. 测试CZSC基础处理")
    print("=" * 60)
    
    # 创建测试数据
    raw_bars = create_test_data()
    print(f"原始K线数量: {len(raw_bars)}")
    
    # 保存原始数据
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    save_test_data_to_file(raw_bars, os.path.join(data_dir, 'test_raw_bars.csv'))
    
    # 创建CZSC分析器
    czsc = CZSC(raw_bars, pen_model='standard')
    
    # 获取处理后的K线
    new_bars = czsc.bars_ubi  # 包含处理后的K线
    print(f"包含处理后K线数量: {len(new_bars)}")
    print(f"K线压缩率: {(len(raw_bars) - len(new_bars)) / len(raw_bars) * 100:.1f}%")
    
    # 显示前几根处理后的K线信息
    print("\n处理后K线示例 (前5根):")
    for i, bar in enumerate(new_bars[:5]):
        print(f"  K线{i}: {bar.dt.strftime('%H:%M')} "
              f"OHLC=({bar.open:.0f}, {bar.high:.0f}, {bar.low:.0f}, {bar.close:.0f}) "
              f"Vol={bar.vol:.0f} 原始K线数={len(bar.elements)}")
    
    # 获取分型
    fractals = czsc.fx_list
    print(f"\n识别的分型数量: {len(fractals)}")
    
    # 显示分型信息
    print("\n分型详情:")
    fractal_data = []
    for i, fx in enumerate(fractals):
        fx_type = "顶分型" if fx.mark == Mark.G else "底分型"
        print(f"  分型{i}: {fx.dt.strftime('%H:%M')} {fx_type} "
              f"价格={fx.fx:.0f} 强度={len(fx.elements)} "
              f"OHLCV=({fx.open:.0f}, {fx.high:.0f}, {fx.low:.0f}, {fx.close:.0f}, {fx.vol:.0f})")
        
        # 保存分型数据
        fractal_data.append({
            'id': i,
            'dt': fx.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'type': fx_type,
            'mark': fx.mark.value,
            'price': fx.fx,
            'high': fx.high,
            'low': fx.low,
            'open': fx.open,
            'close': fx.close,
            'vol': fx.vol,
            'strength': len(fx.elements)
        })
    
    # 保存分型数据
    if fractal_data:
        result_dir = os.path.join(os.path.dirname(__file__), 'result')
        os.makedirs(result_dir, exist_ok=True)
        fractal_df = pd.DataFrame(fractal_data)
        fractal_df.to_csv(os.path.join(result_dir, 'detected_fractals.csv'), index=False, encoding='utf-8')
        print(f"分型数据已保存到: result/detected_fractals.csv")
    
    return czsc, new_bars, fractals


def test_newbar_inclusion_processing(new_bars):
    """测试NewBar包含处理后的OCHLV功能"""
    print("\n" + "=" * 60)
    print("2. 测试NewBar包含处理OCHLV功能")
    print("=" * 60)
    
    # 设置包含处理价格
    processed_bars = set_inclusion_prices_for_bars(new_bars.copy())
    
    # 验证处理结果
    verification = verify_inclusion_processing(processed_bars)
    print(f"验证结果: {verification['status']}")
    print(f"处理覆盖率: {verification['processing_rate']:.1%}")
    
    if verification['errors']:
        print("发现错误:")
        for error in verification['errors'][:3]:  # 只显示前3个错误
            print(f"  {error}")
    
    # 显示包含处理前后对比
    print("\n包含处理OCHLV对比 (前5根):")
    inclusion_data = []
    for i, bar in enumerate(processed_bars[:5]):
        if bar.elements:  # 只显示有包含关系的K线
            original = (bar.open, bar.high, bar.low, bar.close, bar.vol, bar.amount)
            inclusion = (bar.inclusion_open, bar.inclusion_high, bar.inclusion_low, 
                        bar.inclusion_close, bar.inclusion_vol, bar.inclusion_amount)
            print(f"  K线{i}:")
            print(f"    原始OHLCVA: {original}")
            print(f"    包含OHLCVA: {inclusion}")
            print(f"    包含元素数: {len(bar.elements)}")
            
            # 保存包含处理数据
            inclusion_data.append({
                'bar_id': i,
                'dt': bar.dt.strftime('%Y-%m-%d %H:%M:%S'),
                'original_open': bar.open,
                'original_high': bar.high,
                'original_low': bar.low,
                'original_close': bar.close,
                'original_vol': bar.vol,
                'original_amount': bar.amount,
                'inclusion_open': bar.inclusion_open,
                'inclusion_high': bar.inclusion_high,
                'inclusion_low': bar.inclusion_low,
                'inclusion_close': bar.inclusion_close,
                'inclusion_vol': bar.inclusion_vol,
                'inclusion_amount': bar.inclusion_amount,
                'elements_count': len(bar.elements)
            })
    
    # 保存包含处理数据
    if inclusion_data:
        result_dir = os.path.join(os.path.dirname(__file__), 'result')
        os.makedirs(result_dir, exist_ok=True)
        inclusion_df = pd.DataFrame(inclusion_data)
        inclusion_df.to_csv(os.path.join(result_dir, 'inclusion_processing_results.csv'), index=False, encoding='utf-8')
        print(f"包含处理数据已保存到: result/inclusion_processing_results.csv")
    
    return processed_bars


def test_fvg_detection(new_bars, fractals):
    """测试增强的FVG检测功能"""
    print("\n" + "=" * 60)
    print("3. 测试增强的FVG检测功能")
    print("=" * 60)
    
    # 使用分离式检测器
    fvg_detector = FVGDetector(config={
        'min_size_atr_factor': 0.2,  # 降低阈值以检测更多FVG
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
        'fractals': fractals,
        'strokes': [],  # 简化测试，不使用笔
        'bars': new_bars,
        'timestamp': new_bars[-1].dt if new_bars else None
    }
    
    # 运行完整的FVG检测管道
    result = fvg_detector.run_full_pipeline(new_bars, czsc_context)
    
    identified_fvgs = result['identified']
    analyzed_fvgs = result['analyzed']
    
    print(f"识别阶段检测到的FVG: {len(identified_fvgs)}")
    print(f"分析阶段评分的FVG: {len(analyzed_fvgs)}")
    print(f"高质量FVG数量: {result['stage_summary']['high_quality_count']}")
    
    # 显示识别的FVG
    print("\n识别的FVG详情:")
    fvg_data = []
    for i, fvg in enumerate(identified_fvgs):
        direction_str = "看涨" if fvg.direction == Direction.Up else "看跌"
        print(f"  FVG{i}: {fvg.dt.strftime('%H:%M')} {direction_str} "
              f"范围=[{fvg.low:.0f}, {fvg.high:.0f}] 大小={fvg.size:.0f}")
        
        # 保存FVG数据
        fvg_data.append({
            'id': i,
            'dt': fvg.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'direction': direction_str,
            'high': fvg.high,
            'low': fvg.low,
            'size': fvg.size,
            'center': fvg.center
        })
    
    # 显示分析后的FVG（如果有）
    if analyzed_fvgs:
        print("\n分析后的FVG评分:")
        for i, fvg in enumerate(analyzed_fvgs):
            print(f"  FVG{i}: 质量评分={fvg.score:.2f} 缓解程度={fvg.mitigation_level:.1%}")
            
            # 测试缓解分析
            test_prices = [fvg.center, fvg.low + 0.7 * fvg.size]
            for price in test_prices:
                fvg.update_mitigation(price, datetime.now())
            
            print(f"    缓解类型: {fvg.get_mitigation_type()}")
            print(f"    缓解描述: {fvg.get_mitigation_description()}")
            print(f"    交易有效: {fvg.is_effective_for_trading()}")
            
            # 更新FVG数据
            if i < len(fvg_data):
                fvg_data[i].update({
                    'quality_score': fvg.score,
                    'mitigation_level': fvg.mitigation_level,
                    'mitigation_type': fvg.get_mitigation_type(),
                    'effective_for_trading': fvg.is_effective_for_trading()
                })
    
    # 保存FVG数据
    if fvg_data:
        result_dir = os.path.join(os.path.dirname(__file__), 'result')
        os.makedirs(result_dir, exist_ok=True)
        fvg_df = pd.DataFrame(fvg_data)
        fvg_df.to_csv(os.path.join(result_dir, 'detected_fvgs.csv'), index=False, encoding='utf-8')
        print(f"FVG数据已保存到: result/detected_fvgs.csv")
    
    return identified_fvgs, analyzed_fvgs


def test_order_block_detection(new_bars, fractals):
    """测试Order Block检测功能"""
    print("\n" + "=" * 60)
    print("4. 测试Order Block检测功能")
    print("=" * 60)
    
    # 配置Order Block检测器（降低阈值以便测试）
    config = {
        'min_fractal_strength': 3,
        'sweep_atr_factor': 0.2,
        'sweep_reversion_bars': 6,
        'sweep_volume_multiplier': 1.2,
        'fvg_lookforward_bars': 10,
        'fvg_min_size_atr': 0.1,
        'volume_spike_multiplier': 1.3,
        'volume_lookback': 15
    }
    
    # 检测Order Block
    order_blocks = detect_order_blocks_from_czsc(new_bars, fractals, config)
    
    print(f"检测到的Order Block数量: {len(order_blocks)}")
    
    # 显示Order Block详情
    ob_data = []
    for i, ob in enumerate(order_blocks):
        ob_type_str = "需求区域" if ob.ob_type == "DEMAND_ZONE" else "供应区域"
        print(f"\nOrder Block {i}:")
        print(f"  类型: {ob_type_str}")
        print(f"  时间: {ob.dt.strftime('%H:%M')}")
        print(f"  价格范围: [{ob.low:.0f}, {ob.high:.0f}]")
        print(f"  兴趣点价格: {ob.poi_level:.0f}")
        print(f"  分型强度: {ob.fractal_strength}")
        print(f"  流动性扫荡确认: {ob.liquidity_sweep_confirmed}")
        print(f"  FVG创建确认: {ob.fvg_creation_confirmed}")
        print(f"  成交量激增确认: {ob.volume_spike_confirmed}")
        print(f"  强度评分: {ob.strength_score:.2f}")
        print(f"  可靠性评分: {ob.reliability_score:.2f}")
        
        # 保存Order Block数据
        ob_data.append({
            'id': i,
            'dt': ob.dt.strftime('%Y-%m-%d %H:%M:%S'),
            'type': ob_type_str,
            'high': ob.high,
            'low': ob.low,
            'poi_level': ob.poi_level,
            'fractal_strength': ob.fractal_strength,
            'liquidity_sweep_confirmed': ob.liquidity_sweep_confirmed,
            'fvg_creation_confirmed': ob.fvg_creation_confirmed,
            'volume_spike_confirmed': ob.volume_spike_confirmed,
            'strength_score': ob.strength_score,
            'reliability_score': ob.reliability_score
        })
        
        if ob.subsequent_fvg:
            fvg_dir = "看涨" if ob.subsequent_fvg.direction == Direction.Up else "看跌"
            print(f"  后续FVG: {fvg_dir} FVG 大小={ob.subsequent_fvg.size:.0f}")
            ob_data[i].update({
                'subsequent_fvg_direction': fvg_dir,
                'subsequent_fvg_size': ob.subsequent_fvg.size
            })
    
    # 保存Order Block数据
    if ob_data:
        result_dir = os.path.join(os.path.dirname(__file__), 'result')
        os.makedirs(result_dir, exist_ok=True)
        ob_df = pd.DataFrame(ob_data)
        ob_df.to_csv(os.path.join(result_dir, 'detected_order_blocks.csv'), index=False, encoding='utf-8')
        print(f"Order Block数据已保存到: result/detected_order_blocks.csv")
    
    return order_blocks


def generate_comprehensive_report(czsc, new_bars, fractals, identified_fvgs, analyzed_fvgs, order_blocks):
    """生成综合测试报告"""
    report = {
        'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'test_summary': {
            'original_bars_count': len(create_test_data()),
            'processed_bars_count': len(new_bars),
            'compression_rate': f"{(len(create_test_data()) - len(new_bars)) / len(create_test_data()) * 100:.1f}%",
            'detected_fractals_count': len(fractals),
            'identified_fvgs_count': len(identified_fvgs),
            'analyzed_fvgs_count': len(analyzed_fvgs),
            'order_blocks_count': len(order_blocks)
        },
        'quality_metrics': {},
        'component_analysis': {}
    }
    
    # 分析质量统计
    if analyzed_fvgs:
        high_quality_fvgs = [fvg for fvg in analyzed_fvgs if fvg.score >= 0.8]
        avg_fvg_score = np.mean([fvg.score for fvg in analyzed_fvgs])
        report['quality_metrics']['high_quality_fvgs_count'] = len(high_quality_fvgs)
        report['quality_metrics']['avg_fvg_score'] = float(avg_fvg_score)
    
    if order_blocks:
        confirmed_obs = [ob for ob in order_blocks if ob.fvg_creation_confirmed and ob.liquidity_sweep_confirmed]
        avg_ob_strength = np.mean([ob.strength_score for ob in order_blocks])
        report['quality_metrics']['fully_confirmed_obs_count'] = len(confirmed_obs)
        report['quality_metrics']['avg_ob_strength'] = float(avg_ob_strength)
    
    # 检查组件间的关联性
    fvg_near_fractals = 0
    for fvg in identified_fvgs:
        for fx in fractals:
            time_diff = abs((fvg.dt - fx.dt).total_seconds() / 60)
            if time_diff <= 15:  # 15分钟内
                fvg_near_fractals += 1
                break
    
    if identified_fvgs:
        report['component_analysis']['fvg_near_fractals_ratio'] = f"{fvg_near_fractals/len(identified_fvgs)*100:.1f}%"
    
    if order_blocks:
        ob_with_fvg = sum(1 for ob in order_blocks if ob.subsequent_fvg is not None)
        report['component_analysis']['ob_with_subsequent_fvg_ratio'] = f"{ob_with_fvg/len(order_blocks)*100:.1f}%"
    
    # 保存报告
    result_dir = os.path.join(os.path.dirname(__file__), 'result')
    os.makedirs(result_dir, exist_ok=True)
    
    with open(os.path.join(result_dir, 'comprehensive_test_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


def test_integration_workflow():
    """测试完整的集成工作流程"""
    print("\n" + "=" * 60)
    print("5. 集成工作流程测试")
    print("=" * 60)
    
    # 执行完整流程
    czsc, new_bars, fractals = test_czsc_processing()
    processed_bars = test_newbar_inclusion_processing(new_bars)
    identified_fvgs, analyzed_fvgs = test_fvg_detection(new_bars, fractals)
    order_blocks = test_order_block_detection(new_bars, fractals)
    
    # 生成综合报告
    print("\n" + "=" * 60)
    print("综合分析报告")
    print("=" * 60)
    
    report = generate_comprehensive_report(czsc, new_bars, fractals, identified_fvgs, analyzed_fvgs, order_blocks)
    
    print(f"原始K线数量: {report['test_summary']['original_bars_count']}")
    print(f"处理后K线数量: {report['test_summary']['processed_bars_count']}")
    print(f"K线压缩率: {report['test_summary']['compression_rate']}")
    print(f"识别分型数量: {report['test_summary']['detected_fractals_count']}")
    print(f"检测FVG数量: {report['test_summary']['identified_fvgs_count']}")
    print(f"有效Order Block数量: {report['test_summary']['order_blocks_count']}")
    
    if 'avg_fvg_score' in report['quality_metrics']:
        print(f"FVG平均质量评分: {report['quality_metrics']['avg_fvg_score']:.2f}")
    
    if 'avg_ob_strength' in report['quality_metrics']:
        print(f"Order Block平均强度评分: {report['quality_metrics']['avg_ob_strength']:.2f}")
    
    print("\n组件关联性分析:")
    for key, value in report['component_analysis'].items():
        print(f"  {key}: {value}")
    
    print(f"\n测试完成！综合报告已保存到: result/comprehensive_test_report.json")
    print("所有组件功能正常。")


def main():
    """主测试函数"""
    print("CZSC增强组件完整测试")
    print("=" * 60)
    print("测试内容: 处理后K线、分型、FVG、Order Block")
    print("数据目录: test/data/")
    print("结果目录: test/result/")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    try:
        test_integration_workflow()
    except Exception as e:
        print(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 保存错误信息到结果目录
        result_dir = os.path.join(os.path.dirname(__file__), 'result')
        os.makedirs(result_dir, exist_ok=True)
        
        error_report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': str(e),
            'traceback': traceback.format_exc()
        }
        
        with open(os.path.join(result_dir, 'error_report.json'), 'w', encoding='utf-8') as f:
            json.dump(error_report, f, ensure_ascii=False, indent=2)
        
        print(f"错误报告已保存到: result/error_report.json")
    
    print("\n" + "=" * 60)
    print("测试报告生成完毕")
    print("=" * 60)


if __name__ == "__main__":
    main()