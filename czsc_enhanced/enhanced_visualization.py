# -*- coding: utf-8 -*-
"""
增强的可视化功能模块
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import List, Dict, Union
from czsc import CZSC

class EnhancedVisualizer:
    """增强的可视化器，提供专业级别的图表绘制功能"""
    
    def __init__(self, style: str = "dark"):
        """初始化可视化器
        
        Args:
            style: 图表风格，可选 "dark" 或 "light"
        """
        self.style = style
        if style == "dark":
            plt.style.use('dark_background')
            self.bg_color = 'black'
            self.text_color = 'white'
            self.grid_color = '#333333'
        else:
            plt.style.use('default')
            self.bg_color = 'white'
            self.text_color = 'black'
            self.grid_color = '#cccccc'
    
    def plot_professional_chart(self, df: pd.DataFrame, analyzer: CZSC, 
                              signals_history: List[Dict], save_path: str = None,
                              title: str = "专业级缠论分析"):
        """绘制专业级别的图表
        
        Args:
            df: K线数据
            analyzer: CZSC分析器
            signals_history: 信号历史
            save_path: 保存路径
            title: 图表标题
        """
        # 创建专业布局
        fig = plt.figure(figsize=(24, 16), facecolor=self.bg_color)
        gs = fig.add_gridspec(4, 1, height_ratios=[4, 1, 1, 1], hspace=0.1)
        
        # 主图：K线 + 缠论分析
        ax_main = fig.add_subplot(gs[0])
        # 成交量
        ax_volume = fig.add_subplot(gs[1], sharex=ax_main)
        # MACD指标
        ax_macd = fig.add_subplot(gs[2], sharex=ax_main)
        # RSI指标
        ax_rsi = fig.add_subplot(gs[3], sharex=ax_main)
        
        # 设置背景色
        for ax in [ax_main, ax_volume, ax_macd, ax_rsi]:
            ax.set_facecolor(self.bg_color)
            ax.grid(True, color=self.grid_color, linestyle='-', linewidth=0.5, alpha=0.5)
            ax.tick_params(colors=self.text_color)
        
        # 绘制各个部分
        self._plot_main_chart(ax_main, df, analyzer, signals_history)
        self._plot_volume(ax_volume, df)
        self._plot_macd(ax_macd, df)
        self._plot_rsi(ax_rsi, df)
        
        # 设置标题
        fig.suptitle(title, fontsize=20, color=self.text_color, y=0.98)
        
        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=200, bbox_inches='tight',
                       facecolor=self.bg_color, edgecolor='none')
            plt.close()
        else:
            return fig

    def _plot_main_chart(self, ax, df: pd.DataFrame, analyzer: CZSC, signals_history: List[Dict]):
        """绘制主图部分"""
        # 绘制K线
        times = df['datetime']
        opens = df['open']
        highs = df['high']
        lows = df['low']
        closes = df['close']
        
        for i in range(len(df)):
            time = times.iloc[i]
            if closes.iloc[i] >= opens.iloc[i]:
                color = '#ff4444'  # 红色
            else:
                color = '#00ff00'  # 绿色
            
            # 影线
            ax.plot([time, time], [lows.iloc[i], highs.iloc[i]], 
                   color=color, linewidth=1, alpha=0.8)
            
            # 实体
            ax.bar(time, closes.iloc[i] - opens.iloc[i], 
                  bottom=opens.iloc[i], width=pd.Timedelta(minutes=0.8),
                  color=color, alpha=0.8)
        
        # 绘制笔
        bi_list = analyzer.get_bi_list()
        for i, bi in enumerate(bi_list):
            if hasattr(bi, 'fx_a') and hasattr(bi, 'fx_b'):
                start_time = bi.fx_a.dt
                end_time = bi.fx_b.dt
                start_price = bi.fx_a.fx
                end_price = bi.fx_b.fx
                
                color = '#00aaff' if str(bi.direction) == 'Up' else '#ffaa00'
                ax.plot([start_time, end_time], [start_price, end_price],
                       color=color, linewidth=2, alpha=0.9)
        
        # 绘制中枢
        try:
            zs_list = analyzer.get_zs_list()
            for zs in zs_list:
                if hasattr(zs, 'start_bi') and hasattr(zs, 'end_bi'):
                    start_time = zs.start_bi.fx_a.dt
                    end_time = zs.end_bi.fx_b.dt
                    zs_high = zs.zg
                    zs_low = zs.zd
                    
                    ax.fill_between([start_time, end_time], 
                                   [zs_low, zs_low], [zs_high, zs_high],
                                   alpha=0.2, color='purple')
        except:
            pass
        
        # 绘制买卖信号
        for signal in signals_history:
            time = signal['time']
            price = signal['price']
            advice = signal['advice']
            
            if '买入' in advice:
                ax.scatter(time, price, color='red', s=100, marker='^')
            elif '卖出' in advice:
                ax.scatter(time, price, color='green', s=100, marker='v')
        
        ax.set_title('K线与缠论分析', color=self.text_color)
        ax.set_ylabel('价格', color=self.text_color)

    def _plot_volume(self, ax, df: pd.DataFrame):
        """绘制成交量"""
        times = df['datetime']
        volumes = df['volume']
        closes = df['close']
        opens = df['open']
        
        colors = ['#ff4444' if c >= o else '#00ff00' 
                 for c, o in zip(closes, opens)]
        
        ax.bar(times, volumes, width=pd.Timedelta(minutes=0.8),
               color=colors, alpha=0.8)
        
        ax.set_title('成交量', color=self.text_color)
        ax.set_ylabel('成交量', color=self.text_color)

    def _plot_macd(self, ax, df: pd.DataFrame):
        """绘制MACD指标"""
        closes = df['close']
        exp1 = closes.ewm(span=12).mean()
        exp2 = closes.ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        hist = macd - signal
        
        ax.plot(df['datetime'], macd, color='#ffff00', label='MACD')
        ax.plot(df['datetime'], signal, color='#ff00ff', label='Signal')
        ax.bar(df['datetime'], hist, color=['#ff4444' if h >= 0 else '#00ff00' for h in hist],
               width=pd.Timedelta(minutes=0.8), alpha=0.5)
        
        ax.set_title('MACD', color=self.text_color)
        ax.legend(loc='upper left')

    def _plot_rsi(self, ax, df: pd.DataFrame):
        """绘制RSI指标"""
        closes = df['close']
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        ax.plot(df['datetime'], rsi, color='#00aaff', linewidth=1)
        ax.axhline(y=70, color='#ff4444', linestyle='--', alpha=0.5)
        ax.axhline(y=30, color='#00ff00', linestyle='--', alpha=0.5)
        
        ax.set_title('RSI', color=self.text_color)
        ax.set_ylabel('RSI', color=self.text_color)
        ax.set_ylim(0, 100)

# 导出便捷函数
def plot_professional_chart(df: pd.DataFrame, analyzer: CZSC, 
                          signals_history: List[Dict], save_path: str = None,
                          style: str = "dark", title: str = "专业级缠论分析"):
    """便捷函数：绘制专业级图表"""
    viz = EnhancedVisualizer(style=style)
    return viz.plot_professional_chart(df, analyzer, signals_history, save_path, title)

def plot_clear_chart(df: pd.DataFrame, analyzer: CZSC,
                    signals_history: List[Dict], save_path: str = None,
                    style: str = "light", title: str = "清晰缠论分析"):
    """便捷函数：绘制清晰的图表"""
    viz = EnhancedVisualizer(style=style)
    return viz.plot_professional_chart(df, analyzer, signals_history, save_path, title)

def plot_enhanced_chart(df: pd.DataFrame, analyzer: CZSC,
                       signals_history: List[Dict], save_path: str = None,
                       style: str = "dark", title: str = "增强型缠论分析"):
    """便捷函数：绘制增强型图表"""
    viz = EnhancedVisualizer(style=style)
    return viz.plot_professional_chart(df, analyzer, signals_history, save_path, title) 