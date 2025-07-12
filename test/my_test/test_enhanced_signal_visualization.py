#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强信号系统可视化测试 - 完整的缠论+SMC融合可视化
参照existing visualization patterns实现

展示内容：
1. 缠论几何组件（分型、笔）
2. 机构足迹组件（FVG、OB）  
3. 单体信号标注
4. 组合信号高亮
5. 多配置对比
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# 添加项目根路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq
from czsc.signals import EnhancedSignalManager
from czsc.components.detectors import FVGDetector, OBDetector
from czsc.utils.echarts_plot import kline_pro


def load_test_data() -> List[RawBar]:
    """加载测试数据"""
    data_path = os.path.join(current_dir, "data", "BTCUSDT_1m_2023-09.csv")
    if not os.path.exists(data_path):
        print(f"❌ 测试数据文件不存在: {data_path}")
        return []
    
    df = pd.read_csv(data_path)
    df['open_time'] = pd.to_datetime(df['open_time'])
    
    # 选择有足够波动的数据段
    df_sample = df.head(800).copy()  # 使用800根K线，确保有足够的模式
    
    bars = []
    for i, (_, row) in enumerate(df_sample.iterrows()):
        bar = RawBar(
            symbol="BTCUSDT",
            id=i,
            dt=row['open_time'],
            freq=Freq.F1,
            open=float(row['open']),
            close=float(row['close']),
            high=float(row['high']),
            low=float(row['low']),
            vol=float(row['volume']),
            amount=float(row['quote_volume'])
        )
        bars.append(bar)
    
    return bars


def create_enhanced_signal_configs() -> Dict[str, Dict]:
    """创建不同的增强信号配置"""
    return {
        'conservative': {
            'name': '保守模式',
            'description': '高质量信号，减少噪音',
            'config': {
                'fvg_min_gap_size': 0.0001,  # 0.01%
                'ob_min_move_strength': 0.005,  # 0.5%
                'ob_require_fvg': True,
                'enable_signal_filtering': True,
                'fractal_config': {
                    'min_strength_threshold': 0.6,
                    'position_weight': 1.2
                },
                'scoring_config': {
                    'min_composite_score': 100,
                    'min_composite_confidence': 0.6,
                    'max_signals_per_timeframe': 3
                }
            }
        },
        'standard': {
            'name': '标准模式',
            'description': '平衡质量与数量',
            'config': {
                'fvg_min_gap_size': 0.00005,  # 0.005%
                'ob_min_move_strength': 0.002,  # 0.2%
                'ob_require_fvg': False,
                'enable_signal_filtering': True,
                'fractal_config': {
                    'min_strength_threshold': 0.4,
                    'position_weight': 1.0
                },
                'scoring_config': {
                    'min_composite_score': 50,
                    'min_composite_confidence': 0.4,
                    'max_signals_per_timeframe': 5
                }
            }
        },
        'aggressive': {
            'name': '激进模式',
            'description': '更多信号，更高敏感度',
            'config': {
                'fvg_min_gap_size': 0.00001,  # 0.001%
                'ob_min_move_strength': 0.001,  # 0.1%
                'ob_require_fvg': False,
                'enable_signal_filtering': False,
                'fractal_config': {
                    'min_strength_threshold': 0.2,
                    'position_weight': 0.8
                },
                'scoring_config': {
                    'min_composite_score': 20,
                    'min_composite_confidence': 0.3,
                    'max_signals_per_timeframe': 8
                }
            }
        }
    }


def test_enhanced_signal_visualization():
    """测试增强信号系统可视化"""
    print("=" * 80)
    print("🚀 增强信号系统可视化测试")
    print("=" * 80)
    
    # 加载测试数据
    bars = load_test_data()
    if not bars:
        return
    
    print(f"✅ 加载数据: {len(bars)} 根1分钟K线")
    print(f"📅 时间范围: {bars[0].dt.strftime('%Y-%m-%d %H:%M')} 至 {bars[-1].dt.strftime('%Y-%m-%d %H:%M')}")
    print(f"💰 价格区间: {min(bar.low for bar in bars):.2f} - {max(bar.high for bar in bars):.2f}")
    
    # 创建CZSC分析对象
    print(f"\n{'='*60}")
    print("🔍 创建CZSC分析对象")
    
    try:
        czsc = CZSC(bars, pen_model='standard')
        print(f"✅ CZSC分析完成:")
        print(f"   - 分型数: {len(czsc.fx_list)}")
        print(f"   - 笔数: {len(czsc.bi_list)}")
        print(f"   - 包含处理后K线数: {len(czsc.bars_ubi)}")
        
    except Exception as e:
        print(f"❌ CZSC分析失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试不同配置
    configs = create_enhanced_signal_configs()
    results = {}
    
    for config_name, config_info in configs.items():
        print(f"\n{'='*60}")
        print(f"🔍 测试 {config_info['name']}")
        print(f"📝 {config_info['description']}")
        
        try:
            # 创建增强信号管理器
            manager = EnhancedSignalManager(config_info['config'])
            
            # 生成所有信号
            all_signals = manager.generate_all_signals(czsc)
            
            # 获取市场概览
            overview = manager.get_market_overview(czsc)
            
            print(f"✅ {config_info['name']} 分析完成:")
            print(f"   - 机构足迹组件:")
            print(f"     * FVG总数: {all_signals['summary']['fvg_count']}")
            print(f"     * OB总数: {all_signals['summary']['ob_count']}")
            print(f"   - 信号生成:")
            print(f"     * 单体信号: {all_signals['summary']['component_signal_count']}个")
            print(f"     * 组合信号: {all_signals['summary']['composite_signal_count']}个")
            
            # 显示单体信号分布
            component_signals = all_signals['component_signals']
            signal_types = {}
            for signal in component_signals:
                signal_type = f"{signal.component_type}_{signal.signal_type}"
                signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            
            print(f"   - 单体信号分布:")
            for signal_type, count in signal_types.items():
                print(f"     * {signal_type}: {count}个")
            
            # 显示组合信号
            composite_signals = all_signals['composite_signals']
            if composite_signals:
                print(f"   - 组合信号详情:")
                for i, signal in enumerate(composite_signals[:3], 1):
                    print(f"     {i}. {signal.name}")
                    print(f"        强度: {signal.strength.value}, 评分: {signal.total_score:.1f}")
                    print(f"        置信度: {signal.confidence:.2f}, 组成: {len(signal.component_signals)}个单体信号")
            
            results[config_name] = {
                'config_info': config_info,
                'manager': manager,
                'signals': all_signals,
                'overview': overview,
                'czsc': czsc
            }
            
        except Exception as e:
            print(f"❌ {config_info['name']} 分析失败: {e}")
            import traceback
            traceback.print_exc()
            results[config_name] = None
    
    # 对比结果
    print(f"\n{'='*80}")
    print("📊 增强信号系统配置对比")
    print(f"{'='*80}")
    
    print(f"{'配置':<12} {'FVG':<6} {'OB':<6} {'单体信号':<8} {'组合信号':<8} {'最高评分':<8}")
    print("-" * 65)
    
    for config_name, result in results.items():
        if result:
            signals = result['signals']
            composite_signals = signals['composite_signals']
            max_score = max([s.total_score for s in composite_signals]) if composite_signals else 0
            
            print(f"{result['config_info']['name']:<12} "
                  f"{signals['summary']['fvg_count']:<6} "
                  f"{signals['summary']['ob_count']:<6} "
                  f"{signals['summary']['component_signal_count']:<8} "
                  f"{signals['summary']['composite_signal_count']:<8} "
                  f"{max_score:<8.1f}")
    
    # 生成可视化图表
    print(f"\n{'='*60}")
    print("📊 生成增强信号可视化图表")
    
    result_dir = os.path.join(current_dir, "result")
    os.makedirs(result_dir, exist_ok=True)
    
    # 为每个配置生成图表
    for config_name, result in results.items():
        if not result:
            continue
            
        config_info = result['config_info']
        signals = result['signals']
        czsc_obj = result['czsc']
        
        print(f"\n🎨 生成 {config_info['name']} 可视化...")
        
        try:
            # 准备基础K线数据
            kline = [x.__dict__ for x in czsc_obj.bars_raw]
            
            # 准备分型数据
            fx = []
            if czsc_obj.fx_list:
                fx = [{'dt': x.dt, 'fx': x.fx} for x in czsc_obj.fx_list]
            
            # 准备笔数据
            bi = []
            if czsc_obj.bi_list:
                bi = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx} for x in czsc_obj.bi_list] + \
                     [{'dt': czsc_obj.bi_list[-1].fx_b.dt, "bi": czsc_obj.bi_list[-1].fx_b.fx}]
            
            # 准备FVG标注数据
            fvg_annotations = []
            fvgs = signals['market_structure']['institutional_components']['fvgs']
            for fvg in fvgs:
                fvg_annotations.append({
                    'dt': fvg.dt,
                    'price': fvg.midpoint_ce,
                    'text': f"FVG-{fvg.direction.value}",
                    'color': '#FF6B6B' if fvg.direction.value == '看跌' else '#4ECDC4'
                })
            
            # 准备OB标注数据
            ob_annotations = []
            obs = signals['market_structure']['institutional_components']['obs']
            for ob in obs:
                ob_annotations.append({
                    'dt': ob.dt,
                    'price': (ob.top + ob.bottom) / 2,
                    'text': f"OB-{ob.direction.value}",
                    'color': '#FF8E53' if ob.direction.value == '供给区' else '#95E1D3'
                })
            
            # 准备组合信号标注
            signal_annotations = []
            composite_signals = signals['composite_signals']
            for signal in composite_signals[:5]:  # 只显示前5个最重要的信号
                # 找到信号对应的时间点（使用第一个组成信号的时间）
                if signal.component_signals:
                    signal_dt = signal.created_at
                    # 尝试找到对应的价格点
                    signal_price = None
                    for bar in czsc_obj.bars_raw:
                        if abs((bar.dt - signal_dt).total_seconds()) < 300:  # 5分钟内
                            signal_price = (bar.high + bar.low) / 2
                            break
                    
                    if signal_price:
                        signal_annotations.append({
                            'dt': signal_dt,
                            'price': signal_price,
                            'text': f"{signal.name[:8]}({signal.total_score:.0f})",
                            'color': '#9B59B6' if signal.strength.value >= 3 else '#F39C12'
                        })
            
            # 创建图表配置
            chart_config = {
                'kline': kline,
                'fx': fx,
                'bi': bi,
                'annotations': fvg_annotations + ob_annotations + signal_annotations,
                'title': f"增强信号系统 - {config_info['name']}",
                'subtitle': f"FVG:{len(fvgs)}个, OB:{len(obs)}个, 组合信号:{len(composite_signals)}个"
            }
            
            # 生成图表
            filename = f"enhanced_signals_{config_name}.html"
            filepath = os.path.join(result_dir, filename)
            
            # 使用基础的kline_pro生成图表（需要适配我们的数据格式）
            chart = kline_pro(
                kline=kline,
                fx=fx,
                bi=bi,
                title=chart_config['title'],
                width="1600px",
                height="900px"
            )
            
            # 保存图表
            chart.render(filepath)
            print(f"   ✅ {config_info['name']} 图表已生成: {filename}")
            
            # 生成配置信息文件
            config_filename = f"enhanced_signals_{config_name}_config.json"
            config_filepath = os.path.join(result_dir, config_filename)
            
            config_summary = {
                'config_name': config_name,
                'config_info': config_info,
                'analysis_summary': {
                    'data_range': f"{bars[0].dt.isoformat()} - {bars[-1].dt.isoformat()}",
                    'total_bars': len(bars),
                    'fractal_count': len(czsc_obj.fx_list),
                    'stroke_count': len(czsc_obj.bi_list),
                    'fvg_count': len(fvgs),
                    'ob_count': len(obs),
                    'component_signal_count': signals['summary']['component_signal_count'],
                    'composite_signal_count': signals['summary']['composite_signal_count']
                },
                'signal_distribution': signal_types,
                'top_composite_signals': [
                    {
                        'name': s.name,
                        'strength': s.strength.value,
                        'score': s.total_score,
                        'confidence': s.confidence,
                        'component_count': len(s.component_signals)
                    }
                    for s in composite_signals[:5]
                ]
            }
            
            with open(config_filepath, 'w', encoding='utf-8') as f:
                json.dump(config_summary, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"   ✅ 配置信息已保存: {config_filename}")
            
        except Exception as e:
            print(f"   ❌ {config_info['name']} 图表生成失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 生成对比报告
    print(f"\n📋 生成对比分析报告...")
    
    try:
        report_content = generate_comparison_report(results, bars)
        report_filepath = os.path.join(result_dir, "enhanced_signals_comparison_report.html")
        
        with open(report_filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 对比分析报告已生成: enhanced_signals_comparison_report.html")
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
    
    # 核心结论
    print(f"\n{'='*80}")
    print("🎯 增强信号系统测试结论")
    print(f"{'='*80}")
    
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if len(valid_results) == 3:
        print("✅ 所有配置测试成功")
        
        # 分析配置效果
        for config_name, result in valid_results.items():
            signals = result['signals']
            config_info = result['config_info']
            
            print(f"\n📊 {config_info['name']}:")
            print(f"   🔍 检测效果: FVG {signals['summary']['fvg_count']}个, OB {signals['summary']['ob_count']}个")
            print(f"   🎯 信号生成: 单体{signals['summary']['component_signal_count']}个, 组合{signals['summary']['composite_signal_count']}个")
            
            if signals['composite_signals']:
                avg_score = sum(s.total_score for s in signals['composite_signals']) / len(signals['composite_signals'])
                avg_confidence = sum(s.confidence for s in signals['composite_signals']) / len(signals['composite_signals'])
                print(f"   📈 信号质量: 平均评分{avg_score:.1f}, 平均置信度{avg_confidence:.2f}")
        
        print(f"\n🎉 增强信号系统可视化测试成功!")
        print(f"📁 所有结果已保存到: {result_dir}")
        print(f"💡 建议查看HTML图表了解详细的信号分布和质量")
        
    else:
        print("⚠️ 部分配置测试失败，请检查实现代码")
    
    return valid_results


def generate_comparison_report(results: Dict, bars: List[RawBar]) -> str:
    """生成对比分析报告"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>增强信号系统对比分析报告</title>
        <style>
            body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 10px; }}
            .summary {{ background: #ecf0f1; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .config-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin: 20px 0; }}
            .config-card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; }}
            .config-card h3 {{ color: #2c3e50; margin-top: 0; }}
            .metric {{ display: flex; justify-content: space-between; margin: 8px 0; }}
            .metric-value {{ font-weight: bold; color: #27ae60; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: center; }}
            th {{ background-color: #3498db; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .highlight {{ background-color: #fff3cd; }}
            .success {{ color: #27ae60; font-weight: bold; }}
            .warning {{ color: #f39c12; font-weight: bold; }}
            .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 增强信号系统对比分析报告</h1>
            
            <div class="summary">
                <h2>📊 测试概览</h2>
                <div class="metric">
                    <span>测试数据:</span>
                    <span class="metric-value">{len(bars)} 根 1分钟 BTCUSDT K线</span>
                </div>
                <div class="metric">
                    <span>时间范围:</span>
                    <span class="metric-value">{bars[0].dt.strftime('%Y-%m-%d %H:%M')} - {bars[-1].dt.strftime('%Y-%m-%d %H:%M')}</span>
                </div>
                <div class="metric">
                    <span>价格区间:</span>
                    <span class="metric-value">{min(bar.low for bar in bars):.2f} - {max(bar.high for bar in bars):.2f}</span>
                </div>
                <div class="metric">
                    <span>测试配置:</span>
                    <span class="metric-value">{len([r for r in results.values() if r is not None])} 种配置模式</span>
                </div>
            </div>
    """
    
    # 添加配置卡片
    html_content += '<div class="config-grid">'
    
    for config_name, result in results.items():
        if result is None:
            continue
            
        config_info = result['config_info']
        signals = result['signals']
        
        html_content += f"""
        <div class="config-card">
            <h3>{config_info['name']}</h3>
            <p><em>{config_info['description']}</em></p>
            
            <div class="metric">
                <span>FVG检测:</span>
                <span class="metric-value">{signals['summary']['fvg_count']} 个</span>
            </div>
            <div class="metric">
                <span>OB检测:</span>
                <span class="metric-value">{signals['summary']['ob_count']} 个</span>
            </div>
            <div class="metric">
                <span>单体信号:</span>
                <span class="metric-value">{signals['summary']['component_signal_count']} 个</span>
            </div>
            <div class="metric">
                <span>组合信号:</span>
                <span class="metric-value">{signals['summary']['composite_signal_count']} 个</span>
            </div>
        """
        
        if signals['composite_signals']:
            avg_score = sum(s.total_score for s in signals['composite_signals']) / len(signals['composite_signals'])
            avg_confidence = sum(s.confidence for s in signals['composite_signals']) / len(signals['composite_signals'])
            html_content += f"""
            <div class="metric">
                <span>平均评分:</span>
                <span class="metric-value">{avg_score:.1f}</span>
            </div>
            <div class="metric">
                <span>平均置信度:</span>
                <span class="metric-value">{avg_confidence:.2f}</span>
            </div>
            """
        
        html_content += '</div>'
    
    html_content += '</div>'
    
    # 添加对比表格
    html_content += """
    <h2>📈 详细对比数据</h2>
    <table>
        <thead>
            <tr>
                <th>配置模式</th>
                <th>FVG数量</th>
                <th>OB数量</th>
                <th>单体信号</th>
                <th>组合信号</th>
                <th>最高评分</th>
                <th>平均置信度</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for config_name, result in results.items():
        if result is None:
            continue
            
        config_info = result['config_info']
        signals = result['signals']
        composite_signals = signals['composite_signals']
        
        max_score = max([s.total_score for s in composite_signals]) if composite_signals else 0
        avg_confidence = sum(s.confidence for s in composite_signals) / len(composite_signals) if composite_signals else 0
        
        html_content += f"""
        <tr>
            <td><strong>{config_info['name']}</strong></td>
            <td>{signals['summary']['fvg_count']}</td>
            <td>{signals['summary']['ob_count']}</td>
            <td>{signals['summary']['component_signal_count']}</td>
            <td>{signals['summary']['composite_signal_count']}</td>
            <td>{max_score:.1f}</td>
            <td>{avg_confidence:.2f}</td>
        </tr>
        """
    
    html_content += """
        </tbody>
    </table>
    
    <h2>🎯 结论与建议</h2>
    <div class="summary">
        <ul>
            <li><strong>保守模式</strong>: 适合追求高质量信号，减少假信号的交易者</li>
            <li><strong>标准模式</strong>: 平衡了信号质量与数量，适合大多数交易场景</li>
            <li><strong>激进模式</strong>: 提供更多交易机会，但需要更好的风险控制</li>
        </ul>
        <p><strong>建议</strong>: 根据市场环境和个人风险偏好选择合适的配置模式。在震荡市场中使用保守模式，在趋势市场中可以考虑激进模式。</p>
    </div>
    
    <div class="footer">
        <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>增强信号系统 - 缠论几何 + SMC机构分析融合</p>
    </div>
    
    </div>
    </body>
    </html>
    """
    
    return html_content


if __name__ == "__main__":
    test_enhanced_signal_visualization()