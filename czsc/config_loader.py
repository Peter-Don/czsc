# -*- coding: utf-8 -*-
"""
CZSC笔判断配置加载器
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class PenConfigLoader:
    """笔判断配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        :param config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "config" / "pen_config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")
    
    def get_default_pen_model(self) -> str:
        """获取默认笔模式"""
        return self.config['pen_settings']['default_pen_model']
    
    def get_default_adaptive_enabled(self) -> bool:
        """获取默认自适应笔启用状态"""
        return self.config['pen_settings']['default_use_adaptive_pen']
    
    def get_standard_mode_config(self) -> Dict[str, Any]:
        """获取标准模式配置"""
        return self.config['pen_settings']['standard_mode']
    
    def get_flexible_mode_config(self) -> Dict[str, Any]:
        """获取灵活模式配置"""
        return self.config['pen_settings']['flexible_mode']
    
    def get_adaptive_mode_config(self) -> Dict[str, Any]:
        """获取自适应模式配置"""
        return self.config['pen_settings']['adaptive_mode']
    
    def get_indicator_config(self, indicator: str) -> Dict[str, Any]:
        """
        获取指标配置
        
        :param indicator: 指标名称 ('atr' 或 'volume_ma')
        :return: 指标配置
        """
        return self.config['indicator_settings'].get(indicator, {})
    
    def get_adaptive_threshold(self, mode: str) -> Dict[str, Any]:
        """
        获取自适应阈值配置
        
        :param mode: 模式名称 ('conservative', 'moderate', 'aggressive')
        :return: 阈值配置
        """
        return self.config['adaptive_thresholds'].get(mode, {})
    
    def get_market_specific_config(self, market: str) -> Dict[str, Any]:
        """
        获取市场特定配置
        
        :param market: 市场类型 ('crypto', 'stock', 'futures')
        :return: 市场特定配置
        """
        return self.config['market_specific'].get(market, {})
    
    def get_pen_config_for_market(self, market: str = 'stock', 
                                  threshold_mode: str = 'moderate') -> Dict[str, Any]:
        """
        获取特定市场的完整笔配置
        
        :param market: 市场类型
        :param threshold_mode: 阈值模式
        :return: 完整配置
        """
        base_config = self.get_adaptive_mode_config()
        threshold_config = self.get_adaptive_threshold(threshold_mode)
        market_config = self.get_market_specific_config(market)
        
        # 合并配置，优先级：市场特定 > 阈值模式 > 基础配置
        result = {
            'pen_model': self.get_default_pen_model(),
            'use_adaptive_pen': base_config.get('enabled', False),
            'adaptive_vol_ratio': market_config.get('volume_ratio', 
                                 threshold_config.get('volume_ratio', 
                                 base_config.get('volume_ratio', 2.0))),
            'adaptive_atr_ratio': market_config.get('atr_ratio',
                                 threshold_config.get('atr_ratio',
                                 base_config.get('atr_ratio', 2.0))),
            'atr_period': base_config.get('atr_period', 14),
            'volume_period': base_config.get('volume_period', 20)
        }
        
        return result
    
    def save_config(self, config: Dict[str, Any]):
        """
        保存配置到文件
        
        :param config: 要保存的配置
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"保存配置文件失败: {e}")
    
    def update_adaptive_config(self, volume_ratio: float = None, 
                              atr_ratio: float = None,
                              enabled: bool = None):
        """
        更新自适应模式配置
        
        :param volume_ratio: 成交量比率
        :param atr_ratio: ATR比率
        :param enabled: 是否启用
        """
        adaptive_config = self.config['pen_settings']['adaptive_mode']
        
        if volume_ratio is not None:
            adaptive_config['volume_ratio'] = volume_ratio
        if atr_ratio is not None:
            adaptive_config['atr_ratio'] = atr_ratio
        if enabled is not None:
            adaptive_config['enabled'] = enabled
        
        self.save_config(self.config)
    
    def print_config_info(self):
        """打印配置信息"""
        print("=== CZSC笔判断配置信息 ===")
        print(f"配置文件路径: {self.config_path}")
        print(f"默认笔模式: {self.get_default_pen_model()}")
        print(f"默认自适应笔启用: {self.get_default_adaptive_enabled()}")
        
        print("\n--- 标准模式配置 ---")
        standard = self.get_standard_mode_config()
        print(f"最小笔长度: {standard['min_bi_len']}")
        print(f"描述: {standard['description']}")
        
        print("\n--- 灵活模式配置 ---")
        flexible = self.get_flexible_mode_config()
        print(f"最小笔长度: {flexible['min_bi_len']}")
        print(f"描述: {flexible['description']}")
        
        print("\n--- 自适应模式配置 ---")
        adaptive = self.get_adaptive_mode_config()
        print(f"启用状态: {adaptive['enabled']}")
        print(f"成交量比率: {adaptive['volume_ratio']}")
        print(f"ATR比率: {adaptive['atr_ratio']}")
        print(f"描述: {adaptive['description']}")
        
        print("\n--- 可用的阈值模式 ---")
        for mode in ['conservative', 'moderate', 'aggressive']:
            threshold = self.get_adaptive_threshold(mode)
            print(f"{mode}: 成交量比率={threshold['volume_ratio']}, ATR比率={threshold['atr_ratio']}")
        
        print("\n--- 市场特定配置 ---")
        for market in ['crypto', 'stock', 'futures']:
            market_config = self.get_market_specific_config(market)
            print(f"{market}: 成交量比率={market_config['volume_ratio']}, ATR比率={market_config['atr_ratio']}")


# 创建全局配置实例
try:
    pen_config = PenConfigLoader()
except Exception as e:
    print(f"警告: 无法加载笔判断配置: {e}")
    pen_config = None