# -*- coding: utf-8 -*-
"""
CZSC组件层 - 客观识别市场技术结构

本模块实现了各种技术组件的客观识别：
- 缠论几何组件：分型(FX)、笔(BI)
- 机构足迹组件：价格价值缺口(FVG)、订单块(OB)
"""

from czsc.components.institutional import FVG, OB
from czsc.components.detectors import FVGDetector, OBDetector

__all__ = [
    'FVG', 'OB',
    'FVGDetector', 'OBDetector'
]