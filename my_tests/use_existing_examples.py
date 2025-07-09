# -*- coding: utf-8 -*-
"""
基于现有 Examples 的快速测试脚本

利用 czsc_enhanced/examples 下的现成功能进行快速测试和开发
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_dummy_backtest():
    """使用 DummyBacktest 进行快速回测测试"""
    print("=== 测试 DummyBacktest 快速回测 ===")
    
    try:
        import czsc
        from czsc.connectors.research import get_raw_bars, get_symbols
        from czsc.strategies import CzscStrategyExample2
        
        # 创建 DummyBacktest 实例
        dummy = czsc.DummyBacktest(
            strategy=CzscStrategyExample2, 
            read_bars=get_raw_bars,
            signals_module_name='czsc.signals',
            sdt='20230101',  # 测试用短期数据
            edt='20231201',
            results_path=str(project_root / 'my_tests' / 'dummy_results')
        )
        
        # 获取测试品种（使用较少品种进行快速测试）
        symbols = get_symbols('A股主要指数')
        test_symbols = symbols[:3]  # 只测试前3个
        
        print(f"测试品种: {test_symbols}")
        
        # 单个品种回放测试
        print(f"\n开始回放测试: {test_symbols[0]}")
        replay_result = dummy.replay(test_symbols[0])
        
        print("✅ DummyBacktest 回放测试成功")
        print(f"回放结果: {replay_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ DummyBacktest 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_30min():
    """测试30分钟笔非多即空策略"""
    print("\n=== 测试30分钟笔非多即空策略 ===")
    
    try:
        import czsc
        from czsc.connectors import research
        from czsc import Event, Position
        
        # 复制 examples/30分钟笔非多即空.py 的策略定义
        def create_long_short_test(symbol, **kwargs):
            base_freq = kwargs.get('base_freq', '30分钟')
            
            opens = [
                {
                    "operate": "开多",
                    "signals_all": [],
                    "signals_any": [],
                    "signals_not": [],
                    "factors": [
                        {
                            "signals_all": [f"{base_freq}_D1_表里关系V230101_向上_任意_任意_0"],
                            "signals_any": [],
                            "signals_not": [f"{base_freq}_D1_涨跌停V230331_涨停_任意_任意_0"],
                        }
                    ],
                }
            ]
            
            exits = []
            
            pos = Position(
                name=f"{base_freq}笔非多即空测试",
                symbol=symbol,
                opens=[Event.load(x) for x in opens],
                exits=[Event.load(x) for x in exits],
                interval=3600 * 4,
                timeout=16 * 30,
                stop_loss=500,
            )
            return pos
        
        # 定义测试策略类
        class TestStrategy(czsc.CzscStrategyBase):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.is_stocks = kwargs.get('is_stocks', True)
            
            @property
            def positions(self):
                return [create_long_short_test(self.symbol, base_freq='30分钟')]
        
        # 获取测试品种
        symbols = research.get_symbols('A股主要指数')
        symbol = symbols[0]
        
        print(f"测试品种: {symbol}")
        
        # 创建策略实例
        tactic = TestStrategy(symbol=symbol, is_stocks=True)
        
        print(f"K线周期列表: {tactic.freqs}")
        print(f"信号函数配置列表: {tactic.signals_config}")
        
        # 获取测试数据
        bars = research.get_raw_bars(symbol, freq=tactic.base_freq, sdt='20230101', edt='20230601')
        print(f"加载K线数据: {len(bars)} 根")
        
        # 执行策略回放
        results_path = project_root / 'my_tests' / 'strategy_results'
        trader = tactic.replay(bars, sdt='20230301', res_path=str(results_path), refresh=True)
        
        print("✅ 30分钟策略测试成功")
        print(f"交易结果: {trader.results if hasattr(trader, 'results') else '无结果'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 30分钟策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cta_research():
    """测试 CTAResearch 专业回测"""
    print("\n=== 测试 CTAResearch 专业回测 ===")
    
    try:
        from czsc import CTAResearch
        from czsc.strategies import CzscStrategyExample2
        from czsc.connectors.research import get_raw_bars, get_symbols
        
        # 创建 CTAResearch 实例
        bot = CTAResearch(
            results_path=str(project_root / 'my_tests' / 'cta_results'),
            signals_module_name='czsc.signals',
            strategy=CzscStrategyExample2,
            read_bars=get_raw_bars
        )
        
        # 获取测试品种
        symbols = get_symbols("A股主要指数")
        test_symbol = symbols[0]
        
        print(f"测试品种: {test_symbol}")
        
        # 单品种回放测试
        print("开始策略回放...")
        replay_result = bot.replay(
            symbol=test_symbol,
            sdt='20230101',
            edt='20230601',
            refresh=True
        )
        
        print("✅ CTAResearch 回放测试成功")
        print(f"回放结果路径: {bot.results_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ CTAResearch 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signals_development():
    """测试信号开发功能"""
    print("\n=== 测试信号开发功能 ===")
    
    try:
        # 导入信号相关模块
        from czsc.traders.base import CzscSignals
        from czsc.utils.bar_generator import BarGenerator
        from czsc.connectors.research import get_raw_bars, get_symbols
        
        # 获取测试数据
        symbols = get_symbols("A股主要指数")
        symbol = symbols[0]
        
        print(f"测试品种: {symbol}")
        
        # 获取K线数据
        bars = get_raw_bars(symbol, freq='30分钟', sdt='20230601', edt='20230701')
        print(f"加载K线数据: {len(bars)} 根")
        
        # 配置信号
        signals_config = [
            {
                'name': 'czsc.signals.cxt_bi_status_V230101',
                'freq': '30分钟',
                'di': 1
            },
            {
                'name': 'czsc.signals.tas_ma_base_V221101',
                'freq': '30分钟',
                'di': 1,
                'ma_type': 'SMA',
                'timeperiod': 20
            }
        ]
        
        # 创建K线生成器
        bg = BarGenerator(base_freq='30分钟', freqs=['30分钟'], max_count=2000)
        
        # 初始化信号计算器
        cs = CzscSignals(bg, signals_config=signals_config)
        
        # 逐根K线更新信号
        signal_results = []
        for i, bar in enumerate(bars):
            cs.update_signals(bar)
            
            # 每10根K线记录一次信号
            if i % 10 == 0:
                current_signals = dict(cs.s)
                signal_results.append({
                    'bar_index': i,
                    'dt': bar.dt,
                    'signals_count': len(current_signals),
                    'key_signals': {k: v for k, v in current_signals.items() if '表里关系' in k or 'MA基础' in k}
                })
                
                if len(signal_results) <= 3:  # 只打印前3次
                    print(f"第{i}根K线信号: {signal_results[-1]['key_signals']}")
        
        print(f"✅ 信号开发测试成功，共计算 {len(signal_results)} 次信号")
        
        return True
        
    except Exception as e:
        print(f"❌ 信号开发测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streamlit_components():
    """测试 Streamlit 策略分析组件"""
    print("\n=== 测试 Streamlit 分析组件 ===")
    
    try:
        # 测试导入分析组件
        from czsc.mock import generate_strategy_returns, generate_portfolio
        
        print("✅ 成功导入模拟数据生成器")
        
        # 生成测试数据
        df_strategies = generate_strategy_returns(5, 252)  # 5个策略，1年数据
        print(f"生成策略收益数据: {df_strategies.shape}")
        
        df_portfolio = generate_portfolio()
        print(f"生成组合数据: {df_portfolio.shape}")
        
        # 测试导入分析组件
        try:
            from czsc.svc import (
                show_returns_contribution,
                show_strategies_recent,
                show_quarterly_effect,
                show_portfolio
            )
            print("✅ 成功导入策略分析组件")
            
            print("\n💡 可以运行以下命令启动 Streamlit 界面:")
            print(f"cd {project_root}")
            print("streamlit run examples/develop/策略分析组件_svc版本.py")
            
        except ImportError as e:
            print(f"⚠️ Streamlit 组件导入失败（需要安装 streamlit）: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit 组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_btc_data_integration():
    """测试BTC历史数据集成"""
    print("\n=== 测试BTC历史数据集成 ===")
    
    btc_data_path = "/mnt/d/trading/storage/csv/crypto/futures/1m/BTCUSDT"
    
    if not os.path.exists(btc_data_path):
        print(f"⚠️ BTC数据路径不存在: {btc_data_path}")
        return False
    
    try:
        import pandas as pd
        import glob
        from czsc.objects import RawBar, Freq
        from czsc.analyze import CZSC
        
        # 查找BTC数据文件
        csv_files = glob.glob(os.path.join(btc_data_path, "BTCUSDT_1m_2023-*.csv"))
        
        if not csv_files:
            print("⚠️ 未找到BTC数据文件")
            return False
        
        # 使用第一个文件
        file = sorted(csv_files)[0]
        print(f"使用数据文件: {os.path.basename(file)}")
        
        df = pd.read_csv(file)
        df['datetime'] = pd.to_datetime(df['open_time'])
        
        # 取前1000根K线
        df = df.iloc[:1000].reset_index(drop=True)
        
        # 转换为CZSC格式
        bars = []
        for i, row in df.iterrows():
            bar = RawBar(
                symbol='BTCUSDT',
                id=i,
                dt=row['datetime'].to_pydatetime(),
                freq=Freq.F1,
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                vol=float(row['volume']),
                amount=float(row['quote_volume'])
            )
            bars.append(bar)
        
        print(f"转换BTC数据: {len(bars)} 根K线")
        
        # 创建CZSC分析
        c = CZSC(bars)
        
        print(f"CZSC分析结果:")
        print(f"  分型数量: {len(c.fx_list)}")
        print(f"  笔数量: {len(c.bi_list)}")
        print(f"  完成的笔: {len(c.finished_bis)}")
        
        # 生成图表
        try:
            from czsc.utils.echarts_plot import kline_pro
            
            kline_data = [bar.__dict__ for bar in c.bars_raw]
            chart = kline_pro(kline_data, title="BTC CZSC分析")
            
            chart_path = project_root / 'my_tests' / 'btc_czsc_analysis.html'
            chart.render(str(chart_path))
            print(f"✅ BTC分析图表已保存: {chart_path}")
            
        except Exception as e:
            print(f"⚠️ 图表生成失败: {e}")
        
        print("✅ BTC数据集成测试成功")
        return True
        
    except Exception as e:
        print(f"❌ BTC数据集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数：运行所有测试"""
    print("🚀 基于现有 Examples 的 CZSC 测试")
    print("=" * 60)
    
    # 确保结果目录存在
    results_dir = project_root / 'my_tests'
    results_dir.mkdir(exist_ok=True)
    
    test_results = {}
    
    # 运行各项测试
    test_functions = [
        ("BTC历史数据集成", test_btc_data_integration),
        ("信号开发功能", test_signals_development),
        ("30分钟策略测试", test_strategy_30min),
        ("DummyBacktest快速回测", test_dummy_backtest),
        ("CTAResearch专业回测", test_cta_research),
        ("Streamlit分析组件", test_streamlit_components),
    ]
    
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            test_results[test_name] = result
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断测试")
            break
        except Exception as e:
            print(f"\n❌ 测试 {test_name} 出现异常: {e}")
            test_results[test_name] = False
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    for test_name, result in test_results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    successful_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 项测试通过")
    
    if successful_tests > 0:
        print(f"\n📁 结果文件保存在: {results_dir}")
        print("\n💡 后续建议:")
        print("  1. 查看生成的图表和回测结果")
        print("  2. 基于成功的测试进行策略开发")
        print("  3. 使用 Streamlit 进行深度分析")
        print("  4. 参考 examples/ 目录下的更多案例")


if __name__ == "__main__":
    main()