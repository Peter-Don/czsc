# -*- coding: utf-8 -*-
"""
CZSC Enhanced VNPy Integration Module

基于CZSC Enhanced的VNPy量化交易集成模块
提供完整的缠论技术分析与VNPy框架的无缝集成

Author: CZSC Team
Version: 1.0.0
"""

from .adapters.data_adapter import VnpyToCzscConverter, CzscDataManager
from .signals.signal_processor import CzscSignalProcessor  
from .strategies.strategy_engine import CzscStrategyEngine
from .strategies.vnpy_strategy import CzscVnpyStrategyTemplate
from .config.config_manager import CzscConfigManager
from .risk.risk_controller import CzscRiskController

__version__ = "1.0.0"
__author__ = "CZSC Team"

__all__ = [
    # 数据适配
    'VnpyToCzscConverter',
    'CzscDataManager',
    
    # 信号处理
    'CzscSignalProcessor',
    
    # 策略引擎
    'CzscStrategyEngine', 
    'CzscVnpyStrategyTemplate',
    
    # 配置管理
    'CzscConfigManager',
    
    # 风险控制
    'CzscRiskController',
]


def get_version():
    """获取版本信息"""
    return __version__


def get_integration_info():
    """获取集成信息"""
    return {
        'name': 'CZSC Enhanced VNPy Integration',
        'version': __version__,
        'author': __author__,
        'description': '基于CZSC Enhanced的VNPy量化交易集成模块',
        'features': [
            '完整的缠论技术分析',
            '多周期K线数据处理',
            '丰富的信号系统',
            '事件驱动交易',
            '风险控制管理',
            '性能监控',
        ]
    }