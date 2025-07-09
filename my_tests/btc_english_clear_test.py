# -*- coding: utf-8 -*-
"""
BTC CZSC Analysis - English Clear Version

Generate clear and readable CZSC analysis charts with English labels
to avoid font issues and improve readability.
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

# Use English fonts to avoid Chinese font issues
plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

import czsc
from czsc.objects import RawBar, Freq
from czsc.analyze import CZSC


class EnglishBTCCzscAnalyzer:
    """English BTC CZSC Analyzer - Clear and readable charts"""
    
    def __init__(self, data_path: str = "/mnt/d/trading/storage/csv/crypto/futures/1m/BTCUSDT"):
        self.data_path = data_path
        self.bars = []
        self.czsc = None
        self.signals_history = []
        
    def load_optimal_btc_data(self, target_bars: int = 500) -> List[RawBar]:
        """Load optimal BTC data for clear visualization"""
        print(f"📊 Loading BTC data (target: {target_bars} bars)...")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"BTC data path not found: {self.data_path}")
        
        # Find BTC data files
        csv_files = glob.glob(os.path.join(self.data_path, "BTCUSDT_1m_2023-*.csv"))
        
        if not csv_files:
            raise FileNotFoundError("No BTC data files found")
        
        print(f"   Found {len(csv_files)} BTC data files")
        
        # Use one file and select data from middle section for good volatility
        file = sorted(csv_files)[0]
        print(f"   Using data file: {os.path.basename(file)}")
        
        df = pd.read_csv(file)
        df['datetime'] = pd.to_datetime(df['open_time'])
        
        # Select from middle section for good price action
        total_rows = len(df)
        start_idx = total_rows // 3  # Start from 1/3
        end_idx = start_idx + target_bars
        
        df_selected = df.iloc[start_idx:end_idx].reset_index(drop=True)
        
        # Convert to CZSC format
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
        print(f"   ✅ Successfully loaded {len(self.bars)} bars")
        print(f"   📅 Time range: {self.bars[0].dt} to {self.bars[-1].dt}")
        print(f"   💰 Price range: ${min(bar.low for bar in self.bars):.1f} - ${max(bar.high for bar in self.bars):.1f}")
        
        return self.bars
    
    def perform_czsc_analysis(self) -> CZSC:
        """Perform CZSC technical analysis"""
        print("\n🔬 Performing CZSC analysis...")
        
        if not self.bars:
            raise ValueError("Please load data first")
        
        # Create CZSC analysis object
        self.czsc = CZSC(self.bars)
        
        print(f"   📈 Analysis results:")
        print(f"     - K-line count: {len(self.czsc.bars_raw)}")
        print(f"     - Fractal count: {len(self.czsc.fx_list)}")
        print(f"     - Stroke count: {len(self.czsc.bi_list)}")
        print(f"     - Finished strokes: {len(self.czsc.finished_bis)}")
        
        return self.czsc
    
    def generate_trading_signals(self):
        """Generate trading signals based on strokes"""
        print("\n🎯 Generating trading signals...")
        
        if not self.czsc:
            raise ValueError("Please perform CZSC analysis first")
        
        # Generate signals based on finished strokes
        for i, bi in enumerate(self.czsc.finished_bis):
            return_pct = (bi.fx_b.fx - bi.fx_a.fx) / bi.fx_a.fx * 100
            
            signal = {
                'index': i,
                'time': bi.edt,
                'direction': str(bi.direction),
                'start_price': bi.fx_a.fx,
                'end_price': bi.fx_b.fx,
                'return_pct': return_pct,
                'advice': self._generate_signal_advice(bi, return_pct, i)
            }
            self.signals_history.append(signal)
        
        # Count signals
        buy_signals = [s for s in self.signals_history if 'BUY' in s['advice']]
        sell_signals = [s for s in self.signals_history if 'SELL' in s['advice']]
        
        print(f"   📡 Total signals: {len(self.signals_history)}")
        print(f"   🔺 Buy signals: {len(buy_signals)}")
        print(f"   🔻 Sell signals: {len(sell_signals)}")
        
        return self.signals_history
    
    def _generate_signal_advice(self, bi, return_pct: float, index: int) -> str:
        """Generate signal advice with relaxed conditions"""
        direction = str(bi.direction)
        
        # More relaxed conditions to ensure we have some signals
        if direction == 'Up' and return_pct > 0.8:  # Up stroke with >0.8% gain
            return 'BUY Signal'
        elif direction == 'Down' and return_pct < -0.8:  # Down stroke with >0.8% loss
            return 'SELL Signal'
        elif direction == 'Up' and return_pct > 0.3:  # Smaller up stroke
            return 'Watch Up'
        elif direction == 'Down' and return_pct < -0.3:  # Smaller down stroke
            return 'Watch Down'
        else:
            return 'Hold'
    
    def create_professional_chart(self):
        """Create professional quality chart with clear English labels"""
        print("\n🎨 Creating professional CZSC analysis chart...")
        
        if not self.czsc:
            raise ValueError("Please perform CZSC analysis first")
        
        # Create large high-quality figure
        fig = plt.figure(figsize=(20, 14), facecolor='white', dpi=120)
        gs = fig.add_gridspec(3, 2, height_ratios=[4, 1, 1], width_ratios=[4, 1], 
                             hspace=0.25, wspace=0.15)
        
        # Main chart: K-line + CZSC analysis
        ax_main = fig.add_subplot(gs[0, :])
        # Volume chart
        ax_volume = fig.add_subplot(gs[1, :], sharex=ax_main)
        # Statistics
        ax_stats = fig.add_subplot(gs[2, 0])
        # Signal distribution
        ax_pie = fig.add_subplot(gs[2, 1])
        
        # Set main title
        fig.suptitle('CZSC Technical Analysis - BTCUSDT (Professional)', 
                    fontsize=18, fontweight='bold', y=0.95)
        
        # Plot different sections
        self._plot_main_kline_chart(ax_main)
        self._plot_volume_chart(ax_volume)
        self._plot_statistics_table(ax_stats)
        self._plot_signal_pie_chart(ax_pie)
        
        # Save high-quality chart
        output_path = project_root / 'my_tests' / 'btc_professional_english_czsc.png'
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"   ✅ Professional chart saved: {output_path}")
        
        # Create simplified version
        self._create_simplified_chart()
        
        return output_path
    
    def _plot_main_kline_chart(self, ax):
        """Plot main K-line chart with CZSC components"""
        # Prepare data with smart sampling
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.vol
        } for bar in self.bars])
        
        # Sample data if too dense for clear visualization
        if len(df) > 600:
            step = len(df) // 500  # Show max 500 candlesticks
            df_sampled = df.iloc[::step].reset_index(drop=True)
            print(f"      📊 K-line sampling: {len(df)} -> {len(df_sampled)} bars")
        else:
            df_sampled = df
            step = 1
        
        times = df_sampled['datetime']
        opens = df_sampled['open']
        highs = df_sampled['high']
        lows = df_sampled['low']
        closes = df_sampled['close']
        
        # Plot professional candlesticks
        bar_width = pd.Timedelta(minutes=step*0.7)
        
        for i in range(len(df_sampled)):
            time = times.iloc[i]
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            # Professional colors: Red for up, Green for down
            if close_price >= open_price:
                color = '#FF4444'  # Red for bullish
                edge_color = '#CC0000'
            else:
                color = '#00AA00'  # Green for bearish
                edge_color = '#006600'
            
            # Draw shadows (wicks)
            ax.plot([time, time], [low_price, high_price], 
                   color='black', linewidth=1.8, alpha=0.8)
            
            # Draw candlestick body
            body_height = abs(close_price - open_price)
            if body_height > 0:
                rect_bottom = min(open_price, close_price)
                ax.bar(time, body_height, bottom=rect_bottom, 
                      width=bar_width, color=color, alpha=0.9, 
                      edgecolor=edge_color, linewidth=0.8)
            else:
                # Doji (cross)
                ax.plot([time - bar_width/2, time + bar_width/2], 
                       [close_price, close_price], 
                       color=edge_color, linewidth=2)
        
        # Plot fractals (turning points)
        print("      📍 Drawing fractals...")
        fx_list = self.czsc.fx_list
        bottom_count = 0
        top_count = 0
        
        for i, fx in enumerate(fx_list):
            try:
                fx_time = fx.dt
                fx_price = fx.fx
                
                if str(fx.mark) == 'D':  # Bottom fractal
                    bottom_count += 1
                    ax.scatter(fx_time, fx_price, color='red', s=100, 
                             marker='v', alpha=1.0, edgecolors='white', 
                             linewidth=2, zorder=15)
                    if bottom_count <= 12:  # Label first 12
                        ax.annotate(f'Bot{bottom_count}', (fx_time, fx_price), 
                                  xytext=(0, -25), textcoords='offset points',
                                  fontsize=9, ha='center', color='red', weight='bold')
                        
                elif str(fx.mark) == 'G':  # Top fractal
                    top_count += 1
                    ax.scatter(fx_time, fx_price, color='green', s=100, 
                             marker='^', alpha=1.0, edgecolors='white', 
                             linewidth=2, zorder=15)
                    if top_count <= 12:  # Label first 12
                        ax.annotate(f'Top{top_count}', (fx_time, fx_price), 
                                  xytext=(0, 25), textcoords='offset points',
                                  fontsize=9, ha='center', color='green', weight='bold')
            except Exception as e:
                continue
        
        # Plot strokes (connecting fractals)
        print("      🖊️ Drawing strokes...")
        bi_list = self.czsc.bi_list
        
        for i, bi in enumerate(bi_list):
            try:
                start_time = bi.fx_a.dt
                end_time = bi.fx_b.dt
                start_price = bi.fx_a.fx
                end_price = bi.fx_b.fx
                
                # Stroke colors
                if str(bi.direction) == 'Up':
                    line_color = '#0066FF'  # Blue for up stroke
                    text_color = '#004499'
                else:
                    line_color = '#FF8800'  # Orange for down stroke
                    text_color = '#CC6600'
                
                # Draw thick stroke lines
                ax.plot([start_time, end_time], [start_price, end_price], 
                       color=line_color, linewidth=4, alpha=0.95, zorder=12)
                
                # Mark stroke endpoints
                ax.scatter(start_time, start_price, color=text_color, s=80, 
                         marker='o', alpha=1.0, edgecolors='white', 
                         linewidth=2, zorder=16)
                ax.scatter(end_time, end_price, color=text_color, s=80, 
                         marker='o', alpha=1.0, edgecolors='white', 
                         linewidth=2, zorder=16)
                
                # Number strokes (first 15 only)
                if i < 15:
                    mid_time = start_time + (end_time - start_time) / 2
                    mid_price = (start_price + end_price) / 2
                    ax.annotate(f'{i+1}', (mid_time, mid_price), 
                              xytext=(0, 15), textcoords='offset points',
                              fontsize=10, ha='center', weight='bold',
                              color='white',
                              bbox=dict(boxstyle="circle,pad=0.3", 
                                       facecolor=line_color, alpha=0.9, 
                                       edgecolor='white', linewidth=2))
            except Exception as e:
                continue
        
        # Plot trading signals
        print("      📡 Drawing trading signals...")
        buy_count = 0
        sell_count = 0
        
        for signal in self.signals_history:
            time = signal['time']
            price = signal['end_price']
            advice = signal['advice']
            
            if 'BUY' in advice:
                buy_count += 1
                # Large red upward arrow for buy signal
                ax.scatter(time, price, color='#FF0000', s=250, marker='^', 
                          alpha=1.0, edgecolors='white', linewidth=3, zorder=20)
                ax.annotate(f'B{buy_count}', (time, price), 
                          xytext=(0, 35), textcoords='offset points',
                          fontsize=12, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.4", 
                                   facecolor="#FF0000", alpha=0.95, 
                                   edgecolor='white', linewidth=2))
                
            elif 'SELL' in advice:
                sell_count += 1
                # Large green downward arrow for sell signal
                ax.scatter(time, price, color='#00AA00', s=250, marker='v', 
                          alpha=1.0, edgecolors='white', linewidth=3, zorder=20)
                ax.annotate(f'S{sell_count}', (time, price), 
                          xytext=(0, -35), textcoords='offset points',
                          fontsize=12, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.4", 
                                   facecolor="#00AA00", alpha=0.95, 
                                   edgecolor='white', linewidth=2))
        
        # Set chart properties
        ax.set_title('Main Chart - Candlesticks + CZSC Analysis (Fractals, Strokes, Signals)', 
                    fontsize=14, pad=15, weight='bold')
        ax.set_ylabel('Price (USDT)', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        
        # Format price axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.tick_params(axis='both', which='major', labelsize=11)
        
        # Format time axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        plt.setp(ax.get_xticklabels(), rotation=45, fontsize=11)
        
        # Add legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='#FF4444', lw=3, label='Bullish Candle'),
            Line2D([0], [0], color='#00AA00', lw=3, label='Bearish Candle'),
            Line2D([0], [0], marker='v', color='red', linestyle='None', 
                   markersize=8, label='Bottom Fractal'),
            Line2D([0], [0], marker='^', color='green', linestyle='None', 
                   markersize=8, label='Top Fractal'),
            Line2D([0], [0], color='#0066FF', lw=3, label='Up Stroke'),
            Line2D([0], [0], color='#FF8800', lw=3, label='Down Stroke'),
            Line2D([0], [0], marker='^', color='red', linestyle='None', 
                   markersize=10, label='Buy Signal'),
            Line2D([0], [0], marker='v', color='green', linestyle='None', 
                   markersize=10, label='Sell Signal')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=9, 
                 framealpha=0.9, ncol=2)
    
    def _plot_volume_chart(self, ax):
        """Plot volume chart"""
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'volume': bar.vol,
            'close': bar.close,
            'open': bar.open
        } for bar in self.bars])
        
        # Sample data (consistent with main chart)
        if len(df) > 600:
            step = len(df) // 500
            df_sampled = df.iloc[::step].reset_index(drop=True)
        else:
            df_sampled = df
            step = 1
        
        times = df_sampled['datetime']
        volumes = df_sampled['volume']
        closes = df_sampled['close']
        opens = df_sampled['open']
        
        # Color based on price movement
        colors = []
        for close, open_price in zip(closes, opens):
            if close >= open_price:
                colors.append('#FF4444')
            else:
                colors.append('#00AA00')
        
        ax.bar(times, volumes, width=pd.Timedelta(minutes=step*0.7), 
               color=colors, alpha=0.8, edgecolor=colors, linewidth=0.3)
        
        # Mark volume at signal times
        for signal in self.signals_history[:8]:  # Show first 8 signals
            if 'BUY' in signal['advice'] or 'SELL' in signal['advice']:
                signal_time = signal['time']
                # Find closest volume data
                time_diff = abs(times - signal_time)
                closest_idx = time_diff.idxmin()
                signal_volume = volumes.iloc[closest_idx]
                
                color = 'red' if 'BUY' in signal['advice'] else 'green'
                ax.scatter(signal_time, signal_volume, color=color, s=60, 
                          marker='*', alpha=0.9, edgecolors='white', 
                          linewidth=1, zorder=10)
        
        ax.set_title('Volume + Signal Marks', fontsize=12, pad=10, weight='bold')
        ax.set_ylabel('Volume', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=10)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'))
    
    def _plot_statistics_table(self, ax):
        """Plot statistics table"""
        # Collect statistics
        total_bars = len(self.bars)
        total_fx = len(self.czsc.fx_list)
        total_bi = len(self.czsc.bi_list)
        buy_signals = len([s for s in self.signals_history if 'BUY' in s['advice']])
        sell_signals = len([s for s in self.signals_history if 'SELL' in s['advice']])
        
        # Create table data
        stats_data = [
            ['K-line Count', f'{total_bars:,}'],
            ['Fractal Count', f'{total_fx}'],
            ['Stroke Count', f'{total_bi}'],
            ['Buy Signals', f'{buy_signals}'],
            ['Sell Signals', f'{sell_signals}'],
            ['Total Signals', f'{buy_signals + sell_signals}']
        ]
        
        # Create table
        table = ax.table(cellText=stats_data, 
                        colLabels=['Statistics', 'Value'],
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.6, 0.4])
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.2)
        
        # Style table
        for i in range(len(stats_data) + 1):
            for j in range(2):
                cell = table[(i, j)]
                if i == 0:  # Header
                    cell.set_facecolor('#4472C4')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#F8F9FA' if i % 2 == 0 else '#FFFFFF')
                cell.set_edgecolor('#CCCCCC')
                cell.set_linewidth(1)
        
        ax.set_title('Analysis Statistics', fontsize=12, pad=15, weight='bold')
        ax.axis('off')
    
    def _plot_signal_pie_chart(self, ax):
        """Plot signal distribution pie chart"""
        # Count signal types
        buy_signals = len([s for s in self.signals_history if 'BUY' in s['advice']])
        sell_signals = len([s for s in self.signals_history if 'SELL' in s['advice']])
        other_signals = len(self.signals_history) - buy_signals - sell_signals
        
        if buy_signals + sell_signals == 0:
            ax.text(0.5, 0.5, 'No Trading Signals', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title('Signal Distribution', fontsize=12, pad=15, weight='bold')
            return
        
        # Prepare data
        sizes = []
        labels = []
        colors = []
        
        if buy_signals > 0:
            sizes.append(buy_signals)
            labels.append(f'Buy\n{buy_signals}')
            colors.append('#FF4444')
        
        if sell_signals > 0:
            sizes.append(sell_signals)
            labels.append(f'Sell\n{sell_signals}')
            colors.append('#00AA00')
        
        if other_signals > 0:
            sizes.append(other_signals)
            labels.append(f'Other\n{other_signals}')
            colors.append('#888888')
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                        autopct='%1.1f%%', startangle=90, 
                                        textprops={'fontsize': 11})
        
        # Style percentage text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            autotext.set_fontsize(10)
        
        ax.set_title('Signal Distribution', fontsize=12, pad=15, weight='bold')
    
    def _create_simplified_chart(self):
        """Create simplified chart for better readability"""
        print("   📊 Creating simplified chart...")
        
        # Create simple two-panel layout
        fig, (ax_main, ax_volume) = plt.subplots(2, 1, figsize=(16, 12), 
                                               gridspec_kw={'height_ratios': [3, 1]})
        
        fig.suptitle('CZSC Analysis - BTCUSDT (Simplified)', 
                    fontsize=16, fontweight='bold')
        
        # Plot simplified main chart
        self._plot_simplified_main(ax_main)
        
        # Plot simplified volume
        self._plot_simplified_volume(ax_volume)
        
        # Save simplified chart
        output_path = project_root / 'my_tests' / 'btc_simplified_english_czsc.png'
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"   ✅ Simplified chart saved: {output_path}")
    
    def _plot_simplified_main(self, ax):
        """Plot simplified main chart"""
        # Use fewer data points for clarity
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close
        } for bar in self.bars])
        
        # Sample to max 200 bars for clarity (since we only have 500 total)
        if len(df) > 200:
            step = len(df) // 150
            df_sampled = df.iloc[::step].reset_index(drop=True)
        else:
            df_sampled = df
            step = 1
        
        times = df_sampled['datetime']
        opens = df_sampled['open']
        highs = df_sampled['high']
        lows = df_sampled['low']
        closes = df_sampled['close']
        
        # Plot simplified candlesticks
        bar_width = pd.Timedelta(minutes=step*2)
        
        for i in range(len(df_sampled)):
            time = times.iloc[i]
            open_price = opens.iloc[i]
            high_price = highs.iloc[i]
            low_price = lows.iloc[i]
            close_price = closes.iloc[i]
            
            color = '#FF3333' if close_price >= open_price else '#00AA00'
            edge_color = '#CC0000' if close_price >= open_price else '#006600'
            
            # Shadows
            ax.plot([time, time], [low_price, high_price], 
                   color='black', linewidth=1.5, alpha=0.8)
            
            # Bodies
            body_height = abs(close_price - open_price)
            if body_height > 0:
                rect_bottom = min(open_price, close_price)
                ax.bar(time, body_height, bottom=rect_bottom, 
                      width=bar_width, color=color, alpha=0.9, 
                      edgecolor=edge_color, linewidth=0.8)
        
        # Plot only major fractals
        fx_list = self.czsc.fx_list
        for i, fx in enumerate(fx_list[::2]):  # Every other fractal
            fx_time = fx.dt
            fx_price = fx.fx
            
            if str(fx.mark) == 'D':  # Bottom
                ax.scatter(fx_time, fx_price, color='red', s=80, 
                         marker='v', alpha=1.0, edgecolors='white', 
                         linewidth=2, zorder=15)
            elif str(fx.mark) == 'G':  # Top
                ax.scatter(fx_time, fx_price, color='green', s=80, 
                         marker='^', alpha=1.0, edgecolors='white', 
                         linewidth=2, zorder=15)
        
        # Plot major strokes
        for i, bi in enumerate(self.czsc.bi_list):
            if i >= 20:  # Limit to first 20 strokes
                break
                
            start_time = bi.fx_a.dt
            end_time = bi.fx_b.dt
            start_price = bi.fx_a.fx
            end_price = bi.fx_b.fx
            
            color = '#0066FF' if str(bi.direction) == 'Up' else '#FF8800'
            
            ax.plot([start_time, end_time], [start_price, end_price], 
                   color=color, linewidth=3, alpha=0.9, zorder=12)
        
        # Plot trading signals
        signal_count = 0
        for signal in self.signals_history:
            if signal_count >= 10:  # Limit to 10 signals
                break
                
            time = signal['time']
            price = signal['end_price']
            advice = signal['advice']
            
            if 'BUY' in advice:
                signal_count += 1
                ax.scatter(time, price, color='red', s=150, marker='^', 
                          alpha=1.0, edgecolors='white', linewidth=2, zorder=20)
                ax.annotate(f'B{signal_count}', (time, price), 
                          xytext=(0, 25), textcoords='offset points',
                          fontsize=10, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.3", 
                                   facecolor="red", alpha=0.9))
            elif 'SELL' in advice:
                signal_count += 1
                ax.scatter(time, price, color='green', s=150, marker='v', 
                          alpha=1.0, edgecolors='white', linewidth=2, zorder=20)
                ax.annotate(f'S{signal_count}', (time, price), 
                          xytext=(0, -25), textcoords='offset points',
                          fontsize=10, color='white', weight='bold', ha='center',
                          bbox=dict(boxstyle="round,pad=0.3", 
                                   facecolor="green", alpha=0.9))
        
        ax.set_title('Simplified K-line + CZSC Analysis', fontsize=14, pad=15)
        ax.set_ylabel('Price (USDT)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
        plt.setp(ax.get_xticklabels(), rotation=45, fontsize=10)
    
    def _plot_simplified_volume(self, ax):
        """Plot simplified volume chart"""
        df = pd.DataFrame([{
            'datetime': bar.dt,
            'volume': bar.vol,
            'close': bar.close,
            'open': bar.open
        } for bar in self.bars])
        
        # Sample consistently with main chart
        if len(df) > 200:
            step = len(df) // 150
            df_sampled = df.iloc[::step].reset_index(drop=True)
        else:
            df_sampled = df
            step = 1
        
        times = df_sampled['datetime']
        volumes = df_sampled['volume']
        closes = df_sampled['close']
        opens = df_sampled['open']
        
        colors = ['#FF3333' if close >= open else '#00AA00' 
                 for close, open in zip(closes, opens)]
        
        ax.bar(times, volumes, width=pd.Timedelta(minutes=step*2), 
               color=colors, alpha=0.8)
        
        ax.set_title('Volume (Simplified)', fontsize=12)
        ax.set_ylabel('Volume', fontsize=10)
        ax.grid(True, alpha=0.3)


def main():
    """Main function"""
    print("🚀 BTC CZSC Analysis - English Clear Version")
    print("=" * 60)
    
    try:
        # Create analyzer
        analyzer = EnglishBTCCzscAnalyzer()
        
        # 1. Load optimal data
        print("\n📋 Step 1: Loading optimal data")
        bars = analyzer.load_optimal_btc_data(target_bars=500)
        
        # 2. Perform analysis
        print("\n📋 Step 2: Performing CZSC analysis")
        czsc = analyzer.perform_czsc_analysis()
        
        # 3. Generate signals
        print("\n📋 Step 3: Generating trading signals")
        signals = analyzer.generate_trading_signals()
        
        # 4. Create charts
        print("\n📋 Step 4: Creating professional charts")
        chart_path = analyzer.create_professional_chart()
        
        print("\n" + "=" * 60)
        print("🎉 English CZSC analysis completed!")
        print(f"\n📊 Analysis summary:")
        print(f"   ✅ K-line data: {len(bars)} bars")
        print(f"   ✅ Fractals identified: {len(czsc.fx_list)}")
        print(f"   ✅ Strokes formed: {len(czsc.bi_list)}")
        print(f"   ✅ Trading signals: {len(signals)}")
        
        buy_count = len([s for s in signals if 'BUY' in s['advice']])
        sell_count = len([s for s in signals if 'SELL' in s['advice']])
        print(f"   ✅ Buy signals: {buy_count}")
        print(f"   ✅ Sell signals: {sell_count}")
        
        print(f"\n📁 Generated chart files:")
        print(f"   📊 Professional: btc_professional_english_czsc.png")
        print(f"   📈 Simplified: btc_simplified_english_czsc.png")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)