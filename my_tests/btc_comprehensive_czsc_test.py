# -*- coding: utf-8 -*-
"""
基于BTC历史数据的缠论组件完整测试和可视化

参考vnpy测试文件写法，加载挂载目录下BTC历史数据，
完整测试缠论策略、分析和组件识别功能，
生成专业级K线图展示所有缠论组件。

author: claude  
create_dt: 2025/1/8
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置matplotlib中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

import czsc
from czsc.objects import RawBar, Freq
from czsc.analyze import CZSC
from czsc import Event, Position
from czsc.traders.base import CzscSignals
from czsc.utils.bar_generator import BarGenerator


class BTCCzscAnalyzer:
    """BTC缠论分析器"""
    
    def __init__(self, data_path: str = "/mnt/d/trading/storage/csv/crypto/futures/1m/BTCUSDT"):
        self.data_path = data_path
        self.bars = []
        self.czsc = None
        self.signals_history = []
        
    def load_btc_data(self, limit: int = 3000) -> List[RawBar]:
        """加载BTC历史数据"""
        print("📊 开始加载BTC历史数据...")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"BTC数据路径不存在: {self.data_path}")
        
        # 查找BTC数据文件
        csv_files = glob.glob(os.path.join(self.data_path, "BTCUSDT_1m_2023-*.csv"))
        
        if not csv_files:
            raise FileNotFoundError("未找到BTC数据文件")
        
        print(f"   找到 {len(csv_files)} 个BTC数据文件")
        
        # 加载多个月份的数据，确保有足够的数据进行缠论分析
        all_bars = []
        
        for file in sorted(csv_files)[:2]:  # 使用前2个月的数据
            print(f"   加载数据文件: {os.path.basename(file)}")
            
            df = pd.read_csv(file)
            df['datetime'] = pd.to_datetime(df['open_time'])
            
            # 转换为CZSC格式
            for i, row in df.iterrows():
                bar = RawBar(
                    symbol='BTCUSDT',
                    id=len(all_bars),
                    dt=row['datetime'].to_pydatetime(),
                    freq=Freq.F1,  # 1分钟频率
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
        
        self.bars = all_bars
        print(f"   ✅ 成功加载 {len(self.bars)} 根K线数据")
        print(f"   📅 时间范围: {self.bars[0].dt} 到 {self.bars[-1].dt}")
        print(f"   💰 价格范围: ${min(bar.low for bar in self.bars):.1f} - ${max(bar.high for bar in self.bars):.1f}")
        
        return self.bars
    
    def perform_czsc_analysis(self) -> CZSC:
        """执行缠论分析"""
        print("\n🔬 开始缠论技术分析...")
        
        if not self.bars:
            raise ValueError("请先加载数据")
        
        # 创建CZSC分析对象
        self.czsc = CZSC(self.bars)
        
        print(f"   📈 CZSC分析完成:")
        print(f"     - 原始K线数量: {len(self.czsc.bars_raw)}")
        print(f"     - 分型数量: {len(self.czsc.fx_list)}")
        print(f"     - 笔数量: {len(self.czsc.bi_list)}")
        print(f"     - 完成的笔: {len(self.czsc.finished_bis)}")
        
        # 分析笔的统计信息
        if self.czsc.finished_bis:
            up_bis = [bi for bi in self.czsc.finished_bis if str(bi.direction) == 'Up']
            down_bis = [bi for bi in self.czsc.finished_bis if str(bi.direction) == 'Down']
            print(f"     - 向上笔: {len(up_bis)} 个")
            print(f"     - 向下笔: {len(down_bis)} 个")
            
            # 计算笔的平均涨跌幅
            if up_bis:
                up_returns = [(bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100 for bi in up_bis]
                print(f"     - 向上笔平均涨幅: {np.mean(up_returns):.2f}%")
            
            if down_bis:
                down_returns = [(bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100 for bi in down_bis]
                print(f"     - 向下笔平均跌幅: {np.mean(down_returns):.2f}%")
        
        # 分析中枢
        try:
            # 尝试获取中枢信息
            if hasattr(self.czsc, 'zs_list'):
                print(f"     - 中枢数量: {len(self.czsc.zs_list)}")
            else:
                print(f"     - 中枢: 暂未识别到完整中枢")
        except Exception as e:
            print(f"     - 中枢分析: 跳过 ({e})")
        
        return self.czsc
    
    def generate_trading_signals(self):
        """生成交易信号"""
        print("\n🎯 生成缠论交易信号...")
        
        if not self.czsc:
            raise ValueError("请先执行缠论分析")
        
        # 基于笔的完成生成简单信号
        for i, bi in enumerate(self.czsc.finished_bis):
            signal = {
                'index': i,
                'time': bi.edt,  # 笔结束时间
                'direction': str(bi.direction),
                'start_price': bi.fx_a.fx,
                'end_price': bi.fx_b.fx,
                'return_pct': (bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100,
                'advice': self._generate_signal_advice(bi, i)
            }
            self.signals_history.append(signal)
        
        print(f"   📡 生成信号总数: {len(self.signals_history)}")
        
        # 统计信号类型
        buy_signals = [s for s in self.signals_history if '买入' in s['advice']]
        sell_signals = [s for s in self.signals_history if '卖出' in s['advice']]
        hold_signals = [s for s in self.signals_history if '观望' in s['advice']]
        
        print(f"   🔺 买入信号: {len(buy_signals)} 个")
        print(f"   🔻 卖出信号: {len(sell_signals)} 个")
        print(f"   ⏸️ 观望信号: {len(hold_signals)} 个")
        
        return self.signals_history
    
    def _generate_signal_advice(self, bi, index: int) -> str:
        """生成信号建议（简单策略）"""
        direction = str(bi.direction)
        return_pct = (bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100
        
        # 简单的信号策略
        if direction == 'Up' and return_pct > 2:  # 向上笔且涨幅大于2%
            return '买入信号'
        elif direction == 'Down' and return_pct < -2:  # 向下笔且跌幅大于2%
            return '卖出信号'
        else:
            return '观望'
    
    def create_professional_visualization(self):
        """创建专业级缠论可视化图表"""
        print("\n🎨 生成专业级缠论分析图表...")
        
        if not self.czsc:
            raise ValueError("请先执行缠论分析")
        
        # 创建专业布局
        fig = plt.figure(figsize=(24, 16), facecolor='white')
        gs = fig.add_gridspec(4, 2, height_ratios=[4, 1, 1, 1], width_ratios=[4, 1], 
                             hspace=0.15, wspace=0.1)
        
        # 主图：K线 + 缠论分析
        ax_main = fig.add_subplot(gs[0, :])
        # 成交量
        ax_volume = fig.add_subplot(gs[1, :], sharex=ax_main)
        # 笔涨跌统计
        ax_bi_stats = fig.add_subplot(gs[2, 0])
        # 信号统计
        ax_signal_stats = fig.add_subplot(gs[2, 1])
        # 缠论组件统计表
        ax_stats_table = fig.add_subplot(gs[3, :])
        
        # 设置整体标题
        fig.suptitle('CZSC缠论完整分析系统 - BTCUSDT历史数据', 
                    fontsize=20, fontweight='bold', y=0.95)
        
        # 绘制各个子图
        self._plot_main_kline_with_all_components(ax_main)
        self._plot_volume_with_signals(ax_volume)
        self._plot_bi_statistics(ax_bi_stats)
        self._plot_signal_statistics(ax_signal_stats)
        self._plot_comprehensive_stats_table(ax_stats_table)
        
        # 保存图表
        output_path = project_root / 'my_tests' / 'btc_comprehensive_czsc_analysis.png'
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"   ✅ 专业级分析图表已保存: {output_path}")
        
        # 生成简化版图表
        self._create_simplified_visualization()
        
        return output_path
    
    def _plot_main_kline_with_all_components(self, ax):
        """绘制主图：K线 + 所有缠论组件"""
        # 准备数据
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.vol
        } for bar in self.bars])
        
        times = df['datetime']
        opens = df['open']
        highs = df['high']
        lows = df['low']
        closes = df['close']
        
        # 绘制K线图 - 专业风格
        step = max(1, len(df) // 200)  # 显示最多200根K线
        
        for i in range(0, len(df), step):
            time = times.iloc[i]
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            # K线颜色：红涨绿跌
            if close_price >= open_price:
                color = '#ff4444'  # 红色
                edge_color = '#cc0000'
            else:
                color = '#00aa00'  # 绿色
                edge_color = '#006600'
            
            # 影线
            ax.plot([time, time], [low_price, high_price], 
                   color='black', linewidth=1, alpha=0.7)
            
            # K线实体
            body_height = abs(close_price - open_price)
            if body_height > 0:
                rect_bottom = min(open_price, close_price)
                ax.bar(time, body_height, bottom=rect_bottom, 
                      width=pd.Timedelta(minutes=step*0.8), 
                      color=color, alpha=0.8, 
                      edgecolor=edge_color, linewidth=0.5)
            else:
                # 十字星
                ax.plot([time - pd.Timedelta(minutes=step*0.4), 
                        time + pd.Timedelta(minutes=step*0.4)], 
                       [close_price, close_price], 
                       color=edge_color, linewidth=2)
        
        # 绘制分型点
        print("      📍 绘制分型点...")
        fx_list = self.czsc.fx_list
        if fx_list:
            for i, fx in enumerate(fx_list):
                try:
                    fx_time = fx.dt
                    fx_price = fx.fx
                    
                    # 分型标记
                    if str(fx.mark) == 'D':  # 底分型
                        ax.scatter(fx_time, fx_price, color='red', s=60, 
                                 marker='v', alpha=0.8, edgecolors='white', 
                                 linewidth=2, zorder=12)
                        if i < 10:  # 只标注前10个
                            ax.annotate(f'底{i+1}', (fx_time, fx_price), 
                                      xytext=(0, -25), textcoords='offset points',
                                      fontsize=8, ha='center', color='red', weight='bold')
                    elif str(fx.mark) == 'G':  # 顶分型
                        ax.scatter(fx_time, fx_price, color='green', s=60, 
                                 marker='^', alpha=0.8, edgecolors='white', 
                                 linewidth=2, zorder=12)
                        if i < 10:  # 只标注前10个
                            ax.annotate(f'顶{i+1}', (fx_time, fx_price), 
                                      xytext=(0, 25), textcoords='offset points',
                                      fontsize=8, ha='center', color='green', weight='bold')
                except Exception as e:
                    print(f"      ⚠️ 绘制分型{i+1}时出错: {e}")
        
        # 绘制笔
        print("      🖊️ 绘制笔...")
        bi_list = self.czsc.bi_list
        if bi_list:
            for i, bi in enumerate(bi_list):
                try:
                    start_time = bi.fx_a.dt
                    end_time = bi.fx_b.dt
                    start_price = bi.fx_a.fx
                    end_price = bi.fx_b.fx
                    
                    # 笔的颜色
                    if str(bi.direction) == 'Up':
                        line_color = '#0066ff'  # 蓝色向上
                        marker_color = '#004499'
                    else:
                        line_color = '#ff8800'  # 橙色向下
                        marker_color = '#cc6600'
                    
                    # 绘制笔线
                    ax.plot([start_time, end_time], [start_price, end_price], 
                           color=line_color, linewidth=3, alpha=0.9, zorder=10)
                    
                    # 笔的端点标记
                    ax.scatter(start_time, start_price, color=marker_color, s=80, 
                             marker='o', alpha=0.9, edgecolors='white', 
                             linewidth=2, zorder=15)
                    ax.scatter(end_time, end_price, color=marker_color, s=80, 
                             marker='o', alpha=0.9, edgecolors='white', 
                             linewidth=2, zorder=15)
                    
                    # 笔编号（只显示前15个）
                    if i < 15:
                        mid_time = start_time + (end_time - start_time) / 2
                        mid_price = (start_price + end_price) / 2
                        ax.annotate(f'笔{i+1}', (mid_time, mid_price), 
                                  xytext=(0, 15), textcoords='offset points',
                                  fontsize=9, ha='center', weight='bold',
                                  color='white',
                                  bbox=dict(boxstyle="round,pad=0.3", 
                                           facecolor=line_color, alpha=0.8, 
                                           edgecolor='white'))
                
                except Exception as e:
                    print(f"      ⚠️ 绘制笔{i+1}时出错: {e}")
        
        # 绘制中枢（如果存在）
        try:
            print("      🔄 尝试绘制中枢...")
            if hasattr(self.czsc, 'zs_list') and self.czsc.zs_list:
                for i, zs in enumerate(self.czsc.zs_list):
                    try:
                        # 中枢区域
                        start_time = zs.start_bi.fx_a.dt
                        end_time = zs.end_bi.fx_b.dt
                        zs_high = zs.zg
                        zs_low = zs.zd
                        
                        # 绘制中枢区域
                        ax.fill_between([start_time, end_time], 
                                       [zs_low, zs_low], [zs_high, zs_high],
                                       alpha=0.2, color='purple', zorder=5)
                        
                        # 中枢边界线
                        ax.plot([start_time, end_time], [zs_high, zs_high], 
                               color='purple', linewidth=2, linestyle='--', 
                               alpha=0.8, zorder=8)
                        ax.plot([start_time, end_time], [zs_low, zs_low], 
                               color='purple', linewidth=2, linestyle='--', 
                               alpha=0.8, zorder=8)
                        
                        # 中枢标注
                        mid_time = start_time + (end_time - start_time) / 2
                        mid_price = (zs_high + zs_low) / 2
                        ax.text(mid_time, mid_price, f'中枢{i+1}', 
                               fontsize=9, ha='center', va='center',
                               color='white', weight='bold',
                               bbox=dict(boxstyle="round,pad=0.3", 
                                        facecolor="purple", alpha=0.8, 
                                        edgecolor='white'))
                    except Exception as e:
                        print(f"      ⚠️ 绘制中枢{i+1}时出错: {e}")
        except Exception as e:
            print(f"      ⚠️ 中枢处理跳过: {e}")
        
        # 绘制交易信号
        print("      📡 绘制交易信号...")
        buy_count = 0
        sell_count = 0
        
        for signal in self.signals_history[:20]:  # 最多显示20个信号
            time = signal['time']
            price = signal['end_price']
            advice = signal['advice']
            
            if '买入' in advice:
                buy_count += 1
                ax.scatter(time, price, color='red', s=150, marker='^', 
                          alpha=1.0, edgecolors='white', linewidth=3, zorder=20)
                ax.annotate(f'B{buy_count}', (time, price), 
                          xytext=(0, 30), textcoords='offset points',
                          fontsize=10, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.4", 
                                   facecolor="red", alpha=0.9, 
                                   edgecolor='white'))
                
            elif '卖出' in advice:
                sell_count += 1
                ax.scatter(time, price, color='green', s=150, marker='v', 
                          alpha=1.0, edgecolors='white', linewidth=3, zorder=20)
                ax.annotate(f'S{sell_count}', (time, price), 
                          xytext=(0, -35), textcoords='offset points',
                          fontsize=10, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.4", 
                                   facecolor="green", alpha=0.9, 
                                   edgecolor='white'))
        
        # 设置图表属性
        ax.set_title('主图 - K线图 + 完整缠论分析 (分型、笔、中枢、交易信号)', 
                    fontsize=14, pad=15)
        ax.set_ylabel('价格 (USDT)', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # 设置价格轴格式
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # 添加图例
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='#ff4444', lw=3, label='阳线'),
            Line2D([0], [0], color='#00aa00', lw=3, label='阴线'),
            Line2D([0], [0], marker='v', color='red', linestyle='None', 
                   markersize=8, label='底分型'),
            Line2D([0], [0], marker='^', color='green', linestyle='None', 
                   markersize=8, label='顶分型'),
            Line2D([0], [0], color='#0066ff', lw=3, label='向上笔'),
            Line2D([0], [0], color='#ff8800', lw=3, label='向下笔'),
            Line2D([0], [0], color='purple', lw=2, linestyle='--', label='中枢'),
            Line2D([0], [0], marker='^', color='red', linestyle='None', 
                   markersize=10, label='买入信号'),
            Line2D([0], [0], marker='v', color='green', linestyle='None', 
                   markersize=10, label='卖出信号')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=10, 
                 framealpha=0.9, ncol=3)
    
    def _plot_volume_with_signals(self, ax):
        """绘制成交量并标记信号"""
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'volume': bar.vol,
            'close': bar.close,
            'open': bar.open
        } for bar in self.bars])
        
        times = df['datetime']
        volumes = df['volume']
        closes = df['close']
        opens = df['open']
        
        # 根据涨跌设置颜色
        colors = []
        for close, open_price in zip(closes, opens):
            if close >= open_price:
                colors.append('#ff4444')  # 红色
            else:
                colors.append('#00aa00')  # 绿色
        
        ax.bar(times, volumes, width=pd.Timedelta(minutes=0.8), 
               color=colors, alpha=0.7, edgecolor=colors, linewidth=0.3)
        
        # 在信号发生时标记成交量
        for signal in self.signals_history[:10]:
            if '买入' in signal['advice'] or '卖出' in signal['advice']:
                signal_time = signal['time']
                # 找到最接近的成交量数据
                time_diff = abs(times - signal_time)
                closest_idx = time_diff.idxmin()
                signal_volume = volumes.iloc[closest_idx]
                
                color = 'red' if '买入' in signal['advice'] else 'green'
                ax.scatter(signal_time, signal_volume, color=color, s=80, 
                          marker='*', alpha=0.9, edgecolors='white', 
                          linewidth=2, zorder=10)
        
        ax.set_title('成交量 + 信号标记', fontsize=12, pad=10)
        ax.set_ylabel('成交量', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 格式化y轴
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'))
    
    def _plot_bi_statistics(self, ax):
        """绘制笔的统计信息"""
        if not self.czsc.finished_bis:
            ax.text(0.5, 0.5, '暂无完成的笔', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            return
        
        # 统计向上笔和向下笔
        up_bis = [bi for bi in self.czsc.finished_bis if str(bi.direction) == 'Up']
        down_bis = [bi for bi in self.czsc.finished_bis if str(bi.direction) == 'Down']
        
        # 计算涨跌幅
        up_returns = [(bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100 for bi in up_bis]
        down_returns = [(bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100 for bi in down_bis]
        
        # 绘制柱状图
        categories = ['向上笔', '向下笔']
        counts = [len(up_bis), len(down_bis)]
        colors = ['#0066ff', '#ff8800']
        
        bars = ax.bar(categories, counts, color=colors, alpha=0.8, 
                     edgecolor='white', linewidth=2)
        
        # 添加数值标签
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{count}', ha='center', va='bottom', fontsize=12, weight='bold')
        
        # 添加平均涨跌幅信息
        if up_returns:
            avg_up = np.mean(up_returns)
            ax.text(0, max(counts) * 0.8, f'平均涨幅:\n{avg_up:.2f}%', 
                   ha='center', va='center', fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8))
        
        if down_returns:
            avg_down = np.mean(down_returns)
            ax.text(1, max(counts) * 0.8, f'平均跌幅:\n{avg_down:.2f}%', 
                   ha='center', va='center', fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.8))
        
        ax.set_title('笔方向统计', fontsize=12, pad=10)
        ax.set_ylabel('笔数量', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
    
    def _plot_signal_statistics(self, ax):
        """绘制信号统计"""
        if not self.signals_history:
            ax.text(0.5, 0.5, '暂无交易信号', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            return
        
        # 统计信号类型
        buy_signals = [s for s in self.signals_history if '买入' in s['advice']]
        sell_signals = [s for s in self.signals_history if '卖出' in s['advice']]
        hold_signals = [s for s in self.signals_history if '观望' in s['advice']]
        
        # 绘制饼图
        labels = []
        sizes = []
        colors = []
        
        if buy_signals:
            labels.append(f'买入\n{len(buy_signals)}个')
            sizes.append(len(buy_signals))
            colors.append('#ff4444')
        
        if sell_signals:
            labels.append(f'卖出\n{len(sell_signals)}个')
            sizes.append(len(sell_signals))
            colors.append('#00aa00')
        
        if hold_signals:
            labels.append(f'观望\n{len(hold_signals)}个')
            sizes.append(len(hold_signals))
            colors.append('#888888')
        
        if sizes:
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                            autopct='%1.1f%%', startangle=90, 
                                            textprops={'fontsize': 10})
            
            # 设置百分比文字样式
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')
            
        ax.set_title('交易信号分布', fontsize=12, pad=10)
    
    def _plot_comprehensive_stats_table(self, ax):
        """绘制综合统计表格"""
        # 收集所有统计数据
        total_bars = len(self.bars)
        total_fx = len(self.czsc.fx_list)
        total_bi = len(self.czsc.bi_list)
        finished_bi = len(self.czsc.finished_bis)
        
        up_bis = len([bi for bi in self.czsc.finished_bis if str(bi.direction) == 'Up'])
        down_bis = len([bi for bi in self.czsc.finished_bis if str(bi.direction) == 'Down'])
        
        buy_signals = len([s for s in self.signals_history if '买入' in s['advice']])
        sell_signals = len([s for s in self.signals_history if '卖出' in s['advice']])
        
        # 计算效率指标
        fx_efficiency = f'{total_fx/total_bars*100:.2f}%' if total_bars > 0 else '0%'
        bi_efficiency = f'{finished_bi/total_bars*100:.2f}%' if total_bars > 0 else '0%'
        signal_efficiency = f'{(buy_signals+sell_signals)/finished_bi*100:.2f}%' if finished_bi > 0 else '0%'
        
        # 计算时间跨度
        time_span = (self.bars[-1].dt - self.bars[0].dt).days
        
        # 创建统计表格数据
        stats_data = [
            ['数据概览', '数量', '缠论分析', '数量', '交易信号', '数量'],
            ['K线总数', f'{total_bars:,}', '分型总数', f'{total_fx}', '买入信号', f'{buy_signals}'],
            ['时间跨度', f'{time_span}天', '笔总数', f'{total_bi}', '卖出信号', f'{sell_signals}'],
            ['价格区间', f'${min(bar.low for bar in self.bars):.0f}-{max(bar.high for bar in self.bars):.0f}', 
             '完成笔数', f'{finished_bi}', '信号效率', signal_efficiency],
            ['分型效率', fx_efficiency, '向上笔', f'{up_bis}', '总信号数', f'{buy_signals+sell_signals}'],
            ['笔形成效率', bi_efficiency, '向下笔', f'{down_bis}', '观望次数', f'{len(self.signals_history)-(buy_signals+sell_signals)}']
        ]
        
        # 绘制表格
        table = ax.table(cellText=stats_data[1:], 
                        colLabels=stats_data[0],
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.15, 0.15, 0.15, 0.15, 0.15, 0.15])
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # 设置表格样式
        for i in range(len(stats_data)):
            for j in range(6):
                cell = table[(i, j)]
                if i == 0:  # 表头
                    cell.set_facecolor('#4472C4')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    # 交替行颜色
                    cell.set_facecolor('#F8F9FA' if i % 2 == 0 else '#FFFFFF')
                    # 不同列的颜色区分
                    if j in [0, 1]:  # 数据概览列
                        cell.set_facecolor('#E3F2FD' if i % 2 == 0 else '#F3E5F5')
                    elif j in [2, 3]:  # 缠论分析列
                        cell.set_facecolor('#F1F8E9' if i % 2 == 0 else '#E8F5E8')
                    else:  # 交易信号列
                        cell.set_facecolor('#FFF3E0' if i % 2 == 0 else '#FFECB3')
                
                cell.set_edgecolor('#CCCCCC')
                cell.set_linewidth(1)
        
        ax.set_title('缠论分析综合统计表', fontsize=12, pad=20, weight='bold')
        ax.axis('off')
    
    def _create_simplified_visualization(self):
        """创建简化版可视化图表"""
        print("   📊 生成简化版图表...")
        
        # 创建简化布局
        fig, (ax_main, ax_volume) = plt.subplots(2, 1, figsize=(20, 12), 
                                               gridspec_kw={'height_ratios': [3, 1]})
        
        fig.suptitle('CZSC缠论策略分析 - BTCUSDT (简化版)', fontsize=16, fontweight='bold')
        
        # 简化的主图
        self._plot_simplified_kline_with_key_components(ax_main)
        
        # 简化的成交量图
        self._plot_simplified_volume(ax_volume)
        
        # 保存简化版图表
        output_path = project_root / 'my_tests' / 'btc_simplified_czsc_analysis.png'
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"   ✅ 简化版图表已保存: {output_path}")
    
    def _plot_simplified_kline_with_key_components(self, ax):
        """绘制简化版K线图和关键缠论组件"""
        # 准备数据 - 采样显示
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close
        } for bar in self.bars])
        
        # 每隔n根显示一根K线
        step = max(1, len(df) // 100)
        df_sampled = df.iloc[::step].reset_index(drop=True)
        
        times = df_sampled['datetime']
        opens = df_sampled['open']
        highs = df_sampled['high']
        lows = df_sampled['low']
        closes = df_sampled['close']
        
        # 绘制简化K线
        for i in range(len(df_sampled)):
            time = times.iloc[i]
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            color = 'red' if close_price >= open_price else 'green'
            
            # 影线
            ax.plot([time, time], [low_price, high_price], color='black', linewidth=1.5)
            
            # 实体
            body_height = abs(close_price - open_price)
            if body_height > 0:
                rect_bottom = min(open_price, close_price)
                ax.bar(time, body_height, bottom=rect_bottom, 
                      width=pd.Timedelta(minutes=step*20), 
                      color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # 只绘制主要的笔（前20个）
        for i, bi in enumerate(self.czsc.bi_list[:20]):
            try:
                start_time = bi.fx_a.dt
                end_time = bi.fx_b.dt
                start_price = bi.fx_a.fx
                end_price = bi.fx_b.fx
                
                color = 'blue' if str(bi.direction) == 'Up' else 'orange'
                
                ax.plot([start_time, end_time], [start_price, end_price], 
                       color=color, linewidth=3, alpha=0.9)
                
                # 只标注前10个笔
                if i < 10:
                    mid_time = start_time + (end_time - start_time) / 2
                    mid_price = (start_price + end_price) / 2
                    ax.annotate(f'{i+1}', (mid_time, mid_price), 
                              xytext=(0, 15), textcoords='offset points',
                              fontsize=10, ha='center', weight='bold',
                              bbox=dict(boxstyle="circle,pad=0.3", facecolor=color, alpha=0.8))
            except Exception as e:
                continue
        
        # 只绘制主要交易信号（前10个）
        signal_count = 0
        for signal in self.signals_history[:10]:
            if '买入' in signal['advice'] or '卖出' in signal['advice']:
                signal_count += 1
                time = signal['time']
                price = signal['end_price']
                
                if '买入' in signal['advice']:
                    ax.scatter(time, price, color='red', s=120, marker='^', 
                              alpha=0.9, edgecolors='white', linewidth=2)
                    ax.annotate(f'B{signal_count}', (time, price), 
                              xytext=(0, 20), textcoords='offset points',
                              fontsize=9, color='red', weight='bold', ha='center')
                else:
                    ax.scatter(time, price, color='green', s=120, marker='v', 
                              alpha=0.9, edgecolors='white', linewidth=2)
                    ax.annotate(f'S{signal_count}', (time, price), 
                              xytext=(0, -25), textcoords='offset points',
                              fontsize=9, color='green', weight='bold', ha='center')
        
        ax.set_title('K线图 + 缠论分析 (简化版)', fontsize=14)
        ax.set_ylabel('价格 (USDT)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # 格式化时间轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _plot_simplified_volume(self, ax):
        """绘制简化版成交量"""
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'volume': bar.vol,
            'close': bar.close,
            'open': bar.open
        } for bar in self.bars])
        
        # 采样显示
        step = max(1, len(df) // 100)
        df_sampled = df.iloc[::step].reset_index(drop=True)
        
        times = df_sampled['datetime']
        volumes = df_sampled['volume']
        closes = df_sampled['close']
        opens = df_sampled['open']
        
        colors = ['red' if close >= open else 'green' 
                 for close, open in zip(closes, opens)]
        
        ax.bar(times, volumes, width=pd.Timedelta(hours=step), 
               color=colors, alpha=0.7)
        
        ax.set_title('成交量 (简化版)', fontsize=12)
        ax.set_ylabel('成交量', fontsize=10)
        ax.grid(True, alpha=0.3)


def main():
    """主测试函数"""
    print("🚀 BTC历史数据缠论组件完整测试")
    print("=" * 60)
    
    # 确保结果目录存在
    results_dir = project_root / 'my_tests'
    results_dir.mkdir(exist_ok=True)
    
    try:
        # 创建分析器
        analyzer = BTCCzscAnalyzer()
        
        # 1. 加载BTC历史数据
        print("\n📋 第1步：加载BTC历史数据")
        bars = analyzer.load_btc_data(limit=4000)  # 加载4000根K线
        
        # 2. 执行缠论分析
        print("\n📋 第2步：执行缠论分析")
        czsc = analyzer.perform_czsc_analysis()
        
        # 3. 生成交易信号
        print("\n📋 第3步：生成交易信号")
        signals = analyzer.generate_trading_signals()
        
        # 4. 创建可视化图表
        print("\n📋 第4步：创建可视化图表")
        chart_path = analyzer.create_professional_visualization()
        
        print("\n" + "=" * 60)
        print("🎉 BTC缠论组件测试完成！")
        print(f"\n📊 测试结果总结:")
        print(f"   ✅ K线数据: {len(bars)} 根")
        print(f"   ✅ 分型识别: {len(czsc.fx_list)} 个")
        print(f"   ✅ 笔形成: {len(czsc.bi_list)} 个")
        print(f"   ✅ 完成笔: {len(czsc.finished_bis)} 个")
        print(f"   ✅ 交易信号: {len(signals)} 个")
        print(f"   ✅ 图表保存: {chart_path}")
        
        print(f"\n💡 后续可以：")
        print(f"   1. 查看生成的专业级分析图表")
        print(f"   2. 基于识别的组件优化策略参数")
        print(f"   3. 测试不同时间周期的效果")
        print(f"   4. 开发自定义信号函数")
        print(f"   5. 与其他技术指标结合分析")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)