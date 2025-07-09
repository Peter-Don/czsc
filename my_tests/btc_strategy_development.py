# -*- coding: utf-8 -*-
"""
基于BTC历史数据的策略开发和测试

独立使用BTC数据进行策略开发，不依赖research数据缓存
"""

import os
import sys
import glob
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import czsc
from czsc.objects import RawBar, Freq
from czsc.analyze import CZSC
from czsc import Event, Position
from czsc.traders.base import CzscSignals
from czsc.utils.bar_generator import BarGenerator


def load_btc_data(limit: int = 5000) -> List[RawBar]:
    """加载BTC历史数据"""
    btc_data_path = "/mnt/d/trading/storage/csv/crypto/futures/1m/BTCUSDT"
    
    if not os.path.exists(btc_data_path):
        raise FileNotFoundError(f"BTC数据路径不存在: {btc_data_path}")
    
    # 查找BTC数据文件
    csv_files = glob.glob(os.path.join(btc_data_path, "BTCUSDT_1m_2023-*.csv"))
    
    if not csv_files:
        raise FileNotFoundError("未找到BTC数据文件")
    
    print(f"找到 {len(csv_files)} 个BTC数据文件")
    
    # 加载多个月份的数据
    all_bars = []
    
    for file in sorted(csv_files)[:3]:  # 使用前3个月的数据
        print(f"加载数据文件: {os.path.basename(file)}")
        
        df = pd.read_csv(file)
        df['datetime'] = pd.to_datetime(df['open_time'])
        
        # 转换为CZSC格式
        for i, row in df.iterrows():
            bar = RawBar(
                symbol='BTCUSDT',
                id=len(all_bars),
                dt=row['datetime'].to_pydatetime(),
                freq=Freq.F1,
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                vol=float(row['volume']),
                amount=float(row['quote_volume'])
            )
            all_bars.append(bar)
            
            if len(all_bars) >= limit:
                break
        
        if len(all_bars) >= limit:
            break
    
    print(f"成功加载 {len(all_bars)} 根K线数据")
    return all_bars


def create_btc_long_short_strategy(symbol: str, base_freq: str = '30分钟') -> Position:
    """创建BTC多空策略
    
    基于表里关系信号的简单多空策略
    """
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
                    "signals_not": [],
                }
            ],
        },
        {
            "operate": "开空",
            "signals_all": [],
            "signals_any": [],
            "signals_not": [],
            "factors": [
                {
                    "signals_all": [f"{base_freq}_D1_表里关系V230101_向下_任意_任意_0"],
                    "signals_any": [],
                    "signals_not": [],
                }
            ],
        },
    ]

    exits = []

    pos = Position(
        name=f"BTC_{base_freq}_多空策略",
        symbol=symbol,
        opens=[Event.load(x) for x in opens],
        exits=[Event.load(x) for x in exits],
        interval=3600,  # 1小时间隔
        timeout=24 * 60,  # 24小时超时
        stop_loss=500,  # 500个基点止损
    )
    return pos


class BTCStrategy(czsc.CzscStrategyBase):
    """BTC策略类"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_stocks = False  # 加密货币不是股票
    
    @property
    def positions(self):
        """定义策略持仓"""
        return [
            create_btc_long_short_strategy(self.symbol, base_freq='30分钟'),
            create_btc_long_short_strategy(self.symbol, base_freq='60分钟'),
        ]


def test_btc_strategy():
    """测试BTC策略"""
    print("=== 测试BTC策略 ===")
    
    try:
        # 加载BTC数据
        bars = load_btc_data(limit=10000)
        
        # 创建策略实例
        strategy = BTCStrategy(symbol='BTCUSDT')
        
        print(f"K线周期列表: {strategy.freqs}")
        print(f"信号函数配置列表: {len(strategy.signals_config)} 个信号")
        
        # 策略回放测试
        results_path = project_root / 'my_tests' / 'btc_strategy_results'
        results_path.mkdir(exist_ok=True)
        
        print("开始策略回放...")
        trader = strategy.replay(
            bars, 
            sdt='20230201',  # 从2月开始回放
            res_path=str(results_path), 
            refresh=True
        )
        
        print("✅ BTC策略测试成功")
        print(f"结果保存路径: {results_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ BTC策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_btc_signals():
    """测试BTC信号计算"""
    print("\n=== 测试BTC信号计算 ===")
    
    try:
        # 加载少量数据进行信号测试
        bars = load_btc_data(limit=3000)
        
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
        bg = BarGenerator(base_freq='1分钟', freqs=['30分钟'], max_count=3000)
        
        # 初始化信号计算器
        cs = CzscSignals(bg, signals_config=signals_config)
        
        print(f"开始计算 {len(bars)} 根K线的信号...")
        
        # 逐根K线更新信号
        signal_results = []
        for i, bar in enumerate(bars):
            cs.update_signals(bar)
            
            # 每100根K线记录一次信号
            if i % 100 == 0 and i > 0:
                current_signals = dict(cs.s)
                signal_results.append({
                    'bar_index': i,
                    'dt': bar.dt,
                    'signals_count': len(current_signals),
                    'key_signals': {k: v for k, v in current_signals.items() if '表里关系' in k or 'MA基础' in k}
                })
                
                if len(signal_results) <= 5:  # 只打印前5次
                    print(f"第{i}根K线信号: {signal_results[-1]['key_signals']}")
        
        print(f"✅ BTC信号计算成功，共计算 {len(signal_results)} 次信号")
        
        return True
        
    except Exception as e:
        print(f"❌ BTC信号计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_btc_czsc_analysis():
    """测试BTC的CZSC分析"""
    print("\n=== 测试BTC的CZSC分析 ===")
    
    try:
        # 加载数据
        bars = load_btc_data(limit=2000)
        
        # 创建CZSC分析
        c = CZSC(bars)
        
        print(f"CZSC分析结果:")
        print(f"  分型数量: {len(c.fx_list)}")
        print(f"  笔数量: {len(c.bi_list)}")
        print(f"  完成的笔: {len(c.finished_bis)}")
        
        # 分析最近的几笔
        if len(c.finished_bis) > 0:
            print(f"\n最近完成的笔:")
            for i, bi in enumerate(c.finished_bis[-3:]):
                print(f"  笔{i+1}: {bi.sdt} -> {bi.edt}, 方向: {bi.direction}, "
                      f"涨跌幅: {(bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100:.2f}%")
        
        # 生成图表
        try:
            from czsc.utils.echarts_plot import kline_pro
            
            kline_data = [bar.__dict__ for bar in c.bars_raw]
            chart = kline_pro(kline_data, title="BTC CZSC技术分析")
            
            chart_path = project_root / 'my_tests' / 'btc_detailed_analysis.html'
            chart.render(str(chart_path))
            print(f"✅ BTC详细分析图表已保存: {chart_path}")
            
        except Exception as e:
            print(f"⚠️ 图表生成失败: {e}")
        
        print("✅ BTC CZSC分析成功")
        return True
        
    except Exception as e:
        print(f"❌ BTC CZSC分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 BTC策略开发测试")
    print("=" * 60)
    
    # 确保结果目录存在
    results_dir = project_root / 'my_tests'
    results_dir.mkdir(exist_ok=True)
    
    test_results = {}
    
    # 运行各项测试
    test_functions = [
        ("BTC数据加载和CZSC分析", test_btc_czsc_analysis),
        ("BTC信号计算", test_btc_signals),
        ("BTC策略回放测试", test_btc_strategy),
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
        print("  1. 查看生成的BTC分析图表")
        print("  2. 基于成功的测试修改策略参数")
        print("  3. 测试不同周期的策略效果")
        print("  4. 开发自定义信号函数")
        print("  5. 优化止损和止盈逻辑")


if __name__ == "__main__":
    main()