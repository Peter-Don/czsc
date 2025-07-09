# -*- coding: utf-8 -*-
"""
优化版BTC缠论分析 - 清晰可视化

使用较少K线数据，生成清晰易读的缠论分析图表
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

# 设置matplotlib支持中文（改用支持中文的字体）
plt.rcParams['font.family'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

import czsc
from czsc.objects import RawBar, Freq
from czsc.analyze import CZSC


class ClearBTCCzscAnalyzer:
    """清晰版BTC缠论分析器"""
    
    def __init__(self, data_path: str = "/mnt/d/trading/storage/csv/crypto/futures/1m/BTCUSDT"):
        self.data_path = data_path
        self.bars = []
        self.czsc = None
        self.signals_history = []
        
    def load_optimized_btc_data(self, target_bars: int = 2000) -> List[RawBar]:
        """加载优化的BTC数据 - 使用较少K线确保图表清晰"""
        print(f"📊 加载BTC数据 (目标: {target_bars}根K线)...")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"BTC数据路径不存在: {self.data_path}")
        
        # 查找BTC数据文件
        csv_files = glob.glob(os.path.join(self.data_path, "BTCUSDT_1m_2023-*.csv"))
        
        if not csv_files:
            raise FileNotFoundError("未找到BTC数据文件")
        
        print(f"   找到 {len(csv_files)} 个BTC数据文件")
        
        # 只使用一个文件，从中间部分取数据
        file = sorted(csv_files)[0]
        print(f"   使用数据文件: {os.path.basename(file)}")
        
        df = pd.read_csv(file)
        df['datetime'] = pd.to_datetime(df['open_time'])
        
        # 从中间部分取数据，确保有波动
        total_rows = len(df)
        start_idx = total_rows // 3  # 从1/3处开始
        end_idx = start_idx + target_bars
        
        df_selected = df.iloc[start_idx:end_idx].reset_index(drop=True)
        
        # 转换为CZSC格式
        bars = []
        for i, row in df_selected.iterrows():
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
        
        self.bars = bars
        print(f"   ✅ 成功加载 {len(self.bars)} 根K线数据")
        print(f"   📅 时间范围: {self.bars[0].dt} 到 {self.bars[-1].dt}")
        print(f"   💰 价格范围: ${min(bar.low for bar in self.bars):.1f} - ${max(bar.high for bar in self.bars):.1f}")
        
        return self.bars
    
    def perform_czsc_analysis(self) -> CZSC:
        """执行缠论分析"""
        print("\n🔬 执行缠论分析...")
        
        if not self.bars:
            raise ValueError("请先加载数据")
        
        # 创建CZSC分析对象
        self.czsc = CZSC(self.bars)
        
        print(f"   📈 分析结果:")
        print(f"     - K线数量: {len(self.czsc.bars_raw)}")
        print(f"     - 分型数量: {len(self.czsc.fx_list)}")
        print(f"     - 笔数量: {len(self.czsc.bi_list)}")
        print(f"     - 完成笔数: {len(self.czsc.finished_bis)}")
        
        return self.czsc
    
    def generate_clear_signals(self):
        """生成清晰的交易信号"""
        print("\n🎯 生成交易信号...")
        
        if not self.czsc:
            raise ValueError("请先执行缠论分析")
        
        # 基于笔的完成生成信号，使用更宽松的条件
        for i, bi in enumerate(self.czsc.finished_bis):
            return_pct = (bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100
            
            signal = {
                'index': i,
                'time': bi.edt,
                'direction': str(bi.direction),
                'start_price': bi.fx_a.fx,
                'end_price': bi.fx_b.fx,
                'return_pct': return_pct,
                'advice': self._generate_clear_signal_advice(bi, return_pct, i)
            }
            self.signals_history.append(signal)
        
        # 统计信号
        buy_signals = [s for s in self.signals_history if '买入' in s['advice']]
        sell_signals = [s for s in self.signals_history if '卖出' in s['advice']]
        
        print(f"   📡 总信号数: {len(self.signals_history)}")
        print(f"   🔺 买入信号: {len(buy_signals)}")
        print(f"   🔻 卖出信号: {len(sell_signals)}")
        
        return self.signals_history
    
    def _generate_clear_signal_advice(self, bi, return_pct: float, index: int) -> str:
        """生成信号建议 - 使用更明确的条件"""
        direction = str(bi.direction)
        
        # 更宽松的信号条件，确保有买卖信号
        if direction == 'Up' and return_pct > 1.0:  # 向上笔且涨幅大于1%
            return '买入信号'
        elif direction == 'Down' and return_pct < -1.0:  # 向下笔且跌幅大于1%
            return '卖出信号'
        elif direction == 'Up' and return_pct > 0.5:  # 较小的向上笔
            return '关注向上'
        elif direction == 'Down' and return_pct < -0.5:  # 较小的向下笔
            return '关注向下'
        else:
            return '观望'
    
    def create_clear_visualization(self):
        """创建清晰的可视化图表"""
        print("\n🎨 生成清晰版缠论分析图表...")
        
        if not self.czsc:
            raise ValueError("请先执行缠论分析")
        
        # 创建大尺寸图表，确保清晰度
        fig = plt.figure(figsize=(28, 18), facecolor='white', dpi=100)
        gs = fig.add_gridspec(3, 2, height_ratios=[4, 1, 1], width_ratios=[5, 1], 
                             hspace=0.2, wspace=0.15)
        
        # 主图：K线 + 缠论分析
        ax_main = fig.add_subplot(gs[0, :])
        # 成交量
        ax_volume = fig.add_subplot(gs[1, :], sharex=ax_main)
        # 统计信息
        ax_stats = fig.add_subplot(gs[2, 0])
        ax_pie = fig.add_subplot(gs[2, 1])
        
        # 设置标题
        fig.suptitle('CZSC缠论清晰分析 - BTCUSDT (优化版)', 
                    fontsize=24, fontweight='bold', y=0.96)
        
        # 绘制各部分
        self._plot_clear_main_chart(ax_main)
        self._plot_clear_volume(ax_volume)  
        self._plot_stats_table(ax_stats)
        self._plot_signal_pie(ax_pie)
        
        # 保存高质量图表
        output_path = project_root / 'my_tests' / 'btc_clear_czsc_analysis.png'
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"   ✅ 清晰版图表已保存: {output_path}")
        
        # 生成超清晰版（更少K线）
        self._create_ultra_clear_chart()
        
        return output_path
    
    def _plot_clear_main_chart(self, ax):
        """绘制清晰的主图"""
        # 准备数据 - 适当采样避免过于密集
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.vol
        } for bar in self.bars])
        
        # 如果K线太多，进行采样
        if len(df) > 800:
            step = len(df) // 600  # 最多显示600根K线
            df_sampled = df.iloc[::step].reset_index(drop=True)
            print(f"      📊 K线采样: {len(df)} -> {len(df_sampled)} 根")
        else:
            df_sampled = df
            step = 1
        
        times = df_sampled['datetime']
        opens = df_sampled['open']
        highs = df_sampled['high']
        lows = df_sampled['low']
        closes = df_sampled['close']
        
        # 绘制清晰的K线图
        bar_width = pd.Timedelta(minutes=step*0.8)
        
        for i in range(len(df_sampled)):
            time = times.iloc[i]
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            # 专业配色
            if close_price >= open_price:
                color = '#FF4444'  # 红色阳线
                edge_color = '#CC0000'
            else:
                color = '#00AA00'  # 绿色阴线
                edge_color = '#006600'
            
            # 影线 - 加粗
            ax.plot([time, time], [low_price, high_price], 
                   color='black', linewidth=2, alpha=0.8)
            
            # 实体 - 更明显
            body_height = abs(close_price - open_price)
            if body_height > 0:
                rect_bottom = min(open_price, close_price)
                ax.bar(time, body_height, bottom=rect_bottom, 
                      width=bar_width, color=color, alpha=0.9, 
                      edgecolor=edge_color, linewidth=1)
            else:
                # 十字星
                ax.plot([time - bar_width/2, time + bar_width/2], 
                       [close_price, close_price], 
                       color=edge_color, linewidth=3)
        
        # 绘制分型 - 更大更明显
        print("      📍 绘制分型点...")
        fx_list = self.czsc.fx_list
        fx_count = 0
        
        for i, fx in enumerate(fx_list):
            try:
                fx_time = fx.dt
                fx_price = fx.fx
                
                if str(fx.mark) == 'D':  # 底分型
                    ax.scatter(fx_time, fx_price, color='red', s=120, 
                             marker='v', alpha=1.0, edgecolors='white', 
                             linewidth=3, zorder=15)
                    fx_count += 1
                    if fx_count <= 15:  # 只标注前15个
                        ax.annotate(f'底{fx_count}', (fx_time, fx_price), 
                                  xytext=(0, -30), textcoords='offset points',
                                  fontsize=11, ha='center', color='red', weight='bold')
                        
                elif str(fx.mark) == 'G':  # 顶分型
                    ax.scatter(fx_time, fx_price, color='green', s=120, 
                             marker='^', alpha=1.0, edgecolors='white', 
                             linewidth=3, zorder=15)
                    fx_count += 1
                    if fx_count <= 15:  # 只标注前15个
                        ax.annotate(f'顶{fx_count}', (fx_time, fx_price), 
                                  xytext=(0, 30), textcoords='offset points',
                                  fontsize=11, ha='center', color='green', weight='bold')
            except Exception as e:
                continue
        
        # 绘制笔 - 更粗更明显
        print("      🖊️ 绘制笔...")
        bi_list = self.czsc.bi_list
        
        for i, bi in enumerate(bi_list):
            try:
                start_time = bi.fx_a.dt
                end_time = bi.fx_b.dt
                start_price = bi.fx_a.fx
                end_price = bi.fx_b.fx
                
                # 笔的颜色 - 更鲜明
                if str(bi.direction) == 'Up':
                    line_color = '#0066FF'  # 蓝色
                    text_color = '#004499'
                else:
                    line_color = '#FF8800'  # 橙色
                    text_color = '#CC6600'
                
                # 绘制更粗的笔线
                ax.plot([start_time, end_time], [start_price, end_price], 
                       color=line_color, linewidth=5, alpha=0.95, zorder=12)
                
                # 笔端点
                ax.scatter(start_time, start_price, color=text_color, s=100, 
                         marker='o', alpha=1.0, edgecolors='white', 
                         linewidth=3, zorder=16)
                ax.scatter(end_time, end_price, color=text_color, s=100, 
                         marker='o', alpha=1.0, edgecolors='white', 
                         linewidth=3, zorder=16)
                
                # 笔编号 - 只显示前20个
                if i < 20:
                    mid_time = start_time + (end_time - start_time) / 2
                    mid_price = (start_price + end_price) / 2
                    ax.annotate(f'{i+1}', (mid_time, mid_price), 
                              xytext=(0, 20), textcoords='offset points',
                              fontsize=12, ha='center', weight='bold',
                              color='white',
                              bbox=dict(boxstyle="circle,pad=0.4", 
                                       facecolor=line_color, alpha=0.9, 
                                       edgecolor='white', linewidth=2))
            except Exception as e:
                continue
        
        # 绘制交易信号 - 超大超明显
        print("      📡 绘制交易信号...")
        buy_count = 0
        sell_count = 0
        
        for signal in self.signals_history:
            time = signal['time']
            price = signal['end_price']
            advice = signal['advice']
            
            if '买入' in advice:
                buy_count += 1
                # 买入信号 - 超大红色箭头
                ax.scatter(time, price, color='#FF0000', s=300, marker='^', 
                          alpha=1.0, edgecolors='white', linewidth=4, zorder=20)
                ax.annotate(f'买{buy_count}', (time, price), 
                          xytext=(0, 40), textcoords='offset points',
                          fontsize=14, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.5", 
                                   facecolor="#FF0000", alpha=0.95, 
                                   edgecolor='white', linewidth=3))
                
            elif '卖出' in advice:
                sell_count += 1
                # 卖出信号 - 超大绿色箭头
                ax.scatter(time, price, color='#00AA00', s=300, marker='v', 
                          alpha=1.0, edgecolors='white', linewidth=4, zorder=20)
                ax.annotate(f'卖{sell_count}', (time, price), 
                          xytext=(0, -40), textcoords='offset points',
                          fontsize=14, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.5", 
                                   facecolor="#00AA00", alpha=0.95, 
                                   edgecolor='white', linewidth=3))
        
        # 设置图表属性
        ax.set_title('主图 - K线 + 缠论完整分析', fontsize=18, pad=20, weight='bold')
        ax.set_ylabel('价格 (USDT)', fontsize=14)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.8)
        
        # 设置价格轴格式 - 更大字体
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.tick_params(axis='both', which='major', labelsize=12)
        
        # 时间轴格式 - 更合理间隔
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        plt.setp(ax.get_xticklabels(), rotation=45, fontsize=12)
    
    def _plot_clear_volume(self, ax):
        """绘制清晰的成交量"""
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'volume': bar.vol,
            'close': bar.close,
            'open': bar.open
        } for bar in self.bars])
        
        # 采样（与主图一致）
        if len(df) > 800:
            step = len(df) // 600
            df_sampled = df.iloc[::step].reset_index(drop=True)
        else:
            df_sampled = df
            step = 1
        
        times = df_sampled['datetime']
        volumes = df_sampled['volume']
        closes = df_sampled['close']
        opens = df_sampled['open']
        
        # 颜色设置
        colors = []
        for close, open_price in zip(closes, opens):
            if close >= open_price:
                colors.append('#FF4444')
            else:
                colors.append('#00AA00')
        
        ax.bar(times, volumes, width=pd.Timedelta(minutes=step*0.8), 
               color=colors, alpha=0.8, edgecolor=colors, linewidth=0.5)
        
        ax.set_title('成交量', fontsize=16, pad=15, weight='bold')
        ax.set_ylabel('成交量', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=11)
        
        # 格式化y轴
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'))
    
    def _plot_stats_table(self, ax):
        """绘制统计表格"""
        # 统计数据
        total_bars = len(self.bars)
        total_fx = len(self.czsc.fx_list)
        total_bi = len(self.czsc.bi_list)
        buy_signals = len([s for s in self.signals_history if '买入' in s['advice']])
        sell_signals = len([s for s in self.signals_history if '卖出' in s['advice']])
        
        # 创建表格数据
        stats_data = [
            ['K线数量', f'{total_bars:,}'],
            ['分型数量', f'{total_fx}'],
            ['笔数量', f'{total_bi}'],
            ['买入信号', f'{buy_signals}'],
            ['卖出信号', f'{sell_signals}'],
            ['信号总数', f'{buy_signals + sell_signals}']
        ]
        
        # 绘制表格
        table = ax.table(cellText=stats_data, 
                        colLabels=['统计项目', '数值'],
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.6, 0.4])
        
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2.5)
        
        # 设置表格样式
        for i in range(len(stats_data) + 1):
            for j in range(2):
                cell = table[(i, j)]
                if i == 0:  # 表头
                    cell.set_facecolor('#4472C4')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#F8F9FA' if i % 2 == 0 else '#FFFFFF')
                cell.set_edgecolor('#CCCCCC')
                cell.set_linewidth(1)
        
        ax.set_title('数据统计', fontsize=16, pad=20, weight='bold')
        ax.axis('off')
    
    def _plot_signal_pie(self, ax):
        """绘制信号饼图"""
        # 统计信号类型
        buy_signals = len([s for s in self.signals_history if '买入' in s['advice']])
        sell_signals = len([s for s in self.signals_history if '卖出' in s['advice']])
        other_signals = len(self.signals_history) - buy_signals - sell_signals
        
        if buy_signals + sell_signals == 0:
            ax.text(0.5, 0.5, '暂无交易信号', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14)
            ax.set_title('信号分布', fontsize=16, pad=20, weight='bold')
            return
        
        # 数据和标签
        sizes = []
        labels = []
        colors = []
        
        if buy_signals > 0:
            sizes.append(buy_signals)
            labels.append(f'买入\n{buy_signals}个')
            colors.append('#FF4444')
        
        if sell_signals > 0:
            sizes.append(sell_signals)
            labels.append(f'卖出\n{sell_signals}个')
            colors.append('#00AA00')
        
        if other_signals > 0:
            sizes.append(other_signals)
            labels.append(f'其他\n{other_signals}个')
            colors.append('#888888')
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                        autopct='%1.1f%%', startangle=90, 
                                        textprops={'fontsize': 12})
        
        # 设置样式
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            autotext.set_fontsize(11)
        
        ax.set_title('信号分布', fontsize=16, pad=20, weight='bold')
    
    def _create_ultra_clear_chart(self):
        """创建超清晰版本（使用更少K线）"""
        print("   📊 生成超清晰版图表 (1000根K线)...")
        
        # 重新加载更少的数据
        original_bars = self.bars.copy()
        
        # 只取1000根K线
        if len(self.bars) > 1000:
            step = len(self.bars) // 1000
            selected_bars = self.bars[::step][:1000]
            self.bars = selected_bars
            
            # 重新分析
            self.czsc = CZSC(self.bars)
            self.signals_history = []
            self.generate_clear_signals()
        
        # 创建超清晰图表
        fig, (ax_main, ax_volume) = plt.subplots(2, 1, figsize=(24, 16), 
                                               gridspec_kw={'height_ratios': [3, 1]})
        
        fig.suptitle(f'CZSC缠论超清晰分析 - BTCUSDT ({len(self.bars)}根K线)', 
                    fontsize=20, fontweight='bold')
        
        # 使用原有方法绘制
        self._plot_ultra_clear_main(ax_main)
        self._plot_ultra_clear_volume(ax_volume)
        
        # 保存
        output_path = project_root / 'my_tests' / 'btc_ultra_clear_czsc_analysis.png'
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"   ✅ 超清晰版图表已保存: {output_path}")
        
        # 恢复原始数据
        self.bars = original_bars
    
    def _plot_ultra_clear_main(self, ax):
        """绘制超清晰主图"""
        # 直接使用所有K线，不再采样
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close
        } for bar in self.bars])
        
        times = df['datetime']
        opens = df['open']
        highs = df['high']
        lows = df['low']
        closes = df['close']
        
        # 绘制每根K线
        bar_width = pd.Timedelta(minutes=2)  # 固定宽度
        
        for i in range(len(df)):
            time = times.iloc[i]
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            color = '#FF3333' if close_price >= open_price else '#00AA00'
            edge_color = '#CC0000' if close_price >= open_price else '#006600'
            
            # 影线
            ax.plot([time, time], [low_price, high_price], 
                   color='black', linewidth=1.5, alpha=0.8)
            
            # 实体
            body_height = abs(close_price - open_price)
            if body_height > 0:
                rect_bottom = min(open_price, close_price)
                ax.bar(time, body_height, bottom=rect_bottom, 
                      width=bar_width, color=color, alpha=0.9, 
                      edgecolor=edge_color, linewidth=0.8)
        
        # 绘制所有分型
        for i, fx in enumerate(self.czsc.fx_list):
            fx_time = fx.dt
            fx_price = fx.fx
            
            if str(fx.mark) == 'D':  # 底分型
                ax.scatter(fx_time, fx_price, color='red', s=100, 
                         marker='v', alpha=1.0, edgecolors='white', 
                         linewidth=2, zorder=15)
            elif str(fx.mark) == 'G':  # 顶分型
                ax.scatter(fx_time, fx_price, color='green', s=100, 
                         marker='^', alpha=1.0, edgecolors='white', 
                         linewidth=2, zorder=15)
        
        # 绘制所有笔
        for i, bi in enumerate(self.czsc.bi_list):
            start_time = bi.fx_a.dt
            end_time = bi.fx_b.dt
            start_price = bi.fx_a.fx
            end_price = bi.fx_b.fx
            
            color = '#0066FF' if str(bi.direction) == 'Up' else '#FF8800'
            
            ax.plot([start_time, end_time], [start_price, end_price], 
                   color=color, linewidth=4, alpha=0.9, zorder=12)
        
        # 绘制交易信号
        buy_count = 0
        sell_count = 0
        
        for signal in self.signals_history:
            time = signal['time']
            price = signal['end_price']
            advice = signal['advice']
            
            if '买入' in advice:
                buy_count += 1
                ax.scatter(time, price, color='red', s=200, marker='^', 
                          alpha=1.0, edgecolors='white', linewidth=3, zorder=20)
                ax.annotate(f'B{buy_count}', (time, price), 
                          xytext=(0, 30), textcoords='offset points',
                          fontsize=12, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.4", 
                                   facecolor="red", alpha=0.9))
            elif '卖出' in advice:
                sell_count += 1
                ax.scatter(time, price, color='green', s=200, marker='v', 
                          alpha=1.0, edgecolors='white', linewidth=3, zorder=20)
                ax.annotate(f'S{sell_count}', (time, price), 
                          xytext=(0, -35), textcoords='offset points',
                          fontsize=12, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.4", 
                                   facecolor="green", alpha=0.9))
        
        ax.set_title('超清晰K线图 + 缠论分析', fontsize=16, pad=15)
        ax.set_ylabel('价格 (USDT)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # 时间轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        plt.setp(ax.get_xticklabels(), rotation=45, fontsize=11)
    
    def _plot_ultra_clear_volume(self, ax):
        """绘制超清晰成交量"""
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
        
        colors = ['#FF3333' if close >= open else '#00AA00' 
                 for close, open in zip(closes, opens)]
        
        ax.bar(times, volumes, width=pd.Timedelta(minutes=2), 
               color=colors, alpha=0.8)
        
        ax.set_title('成交量 (超清晰版)', fontsize=14)
        ax.set_ylabel('成交量', fontsize=11)
        ax.grid(True, alpha=0.3)


def main():
    """主函数"""
    print("🚀 BTC缠论清晰版分析测试")
    print("=" * 60)
    
    try:
        # 创建分析器
        analyzer = ClearBTCCzscAnalyzer()
        
        # 1. 加载优化的数据
        print("\n📋 第1步：加载优化数据")
        bars = analyzer.load_optimized_btc_data(target_bars=2000)
        
        # 2. 执行分析
        print("\n📋 第2步：执行缠论分析")
        czsc = analyzer.perform_czsc_analysis()
        
        # 3. 生成信号
        print("\n📋 第3步：生成交易信号")
        signals = analyzer.generate_clear_signals()
        
        # 4. 创建清晰图表
        print("\n📋 第4步：生成清晰图表")
        chart_path = analyzer.create_clear_visualization()
        
        print("\n" + "=" * 60)
        print("🎉 清晰版缠论分析完成！")
        print(f"\n📊 分析结果:")
        print(f"   ✅ K线数据: {len(bars)} 根")
        print(f"   ✅ 分型识别: {len(czsc.fx_list)} 个")
        print(f"   ✅ 笔形成: {len(czsc.bi_list)} 个")
        print(f"   ✅ 交易信号: {len(signals)} 个")
        
        buy_count = len([s for s in signals if '买入' in s['advice']])
        sell_count = len([s for s in signals if '卖出' in s['advice']])
        print(f"   ✅ 买入信号: {buy_count} 个")
        print(f"   ✅ 卖出信号: {sell_count} 个")
        
        print(f"\n📁 生成的图表文件:")
        print(f"   📊 清晰版: btc_clear_czsc_analysis.png")
        print(f"   📈 超清晰版: btc_ultra_clear_czsc_analysis.png")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 分析过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)