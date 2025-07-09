# -*- coding: utf-8 -*-
"""
czsc的增强版本，提供额外的功能和组件
"""

__version__ = "0.1.0"
__author__ = "moses2204"

# 导入原始czsc包的核心功能
from czsc import (
    CZSC,
    Freq,
    Direction,
    Signal,
    Factor,
    Event,
    RawBar,
    NewBar,
    Position,
    ZS,
)

# 导出增强版本的新功能
from .enhanced_visualization import (
    plot_professional_chart,
    plot_clear_chart,
    plot_enhanced_chart,
)

# 版本检查
import czsc
from packaging import version
if version.parse(czsc.__version__) < version.parse("0.9.68"):
    raise ImportError("需要czsc >= 0.9.68") 