# -*- coding: utf-8 -*-
"""
组件适配器 - 在原CZSC组件与新信号系统之间建立桥梁

设计原则：
1. 不修改原有组件代码
2. 提供统一的组件接口给信号层
3. 保持向后兼容性
"""

from typing import Dict, Any, Optional
from czsc.objects import FX, BI
from czsc.enum import Mark, Direction


class ComponentAdapter:
    """
    组件适配器 - 在原CZSC组件与新信号系统之间建立桥梁
    
    设计原则：
    1. 不修改原有组件代码
    2. 提供统一的组件接口给信号层
    3. 保持向后兼容性
    """
    
    @staticmethod
    def extract_objective_properties(fx: FX) -> Dict[str, Any]:
        """从原FX对象提取客观属性"""
        return {
            'symbol': fx.symbol,
            'dt': fx.dt,
            'mark': fx.mark,
            'price': fx.fx,
            'high': fx.high,
            'low': fx.low,
            
            # 客观测量属性
            'power_str': getattr(fx, 'power_str', '弱'),
            'element_count': len(fx.elements) if fx.elements else 0,
            'duration_bars': len(fx.elements) if fx.elements else 0,
            
            # 位置属性
            'is_boundary': fx.dt == fx.elements[0].dt if fx.elements else False,
            
            # 缓存原有扩展属性（将来迁移到信号层）
            '_legacy_level': getattr(fx, 'gfc_level', 1),
            '_legacy_reasons_2': getattr(fx, 'level_2_reasons', []),
            '_legacy_reasons_3': getattr(fx, 'level_3_reasons', [])
        }
    
    @staticmethod
    def extract_objective_properties_bi(bi: BI) -> Dict[str, Any]:
        """从原BI对象提取客观属性"""
        return {
            'symbol': bi.symbol,
            'direction': bi.direction,
            'start_dt': bi.fx_a.dt,
            'end_dt': bi.fx_b.dt,
            'start_price': bi.fx_a.fx,
            'end_price': bi.fx_b.fx,
            
            # 客观测量属性
            'length': abs(bi.fx_b.fx - bi.fx_a.fx),
            'duration_bars': len(bi.bars) if bi.bars else 0,
            'power': getattr(bi, 'power', 0.0),
            'angle': getattr(bi, 'angle', 0.0),
            
            # 组成分型
            'start_fractal': bi.fx_a,
            'end_fractal': bi.fx_b,
            
            # 缓存原有扩展属性
            '_legacy_level': getattr(bi, 'gbc_level', 1),
            '_legacy_reasons_2': getattr(bi, 'level_2_reasons', []),
            '_legacy_reasons_3': getattr(bi, 'level_3_reasons', [])
        }
    
    @staticmethod
    def is_legacy_mode_enabled() -> bool:
        """检查是否启用兼容模式"""
        # 可以从配置文件或环境变量读取
        return True  # 默认启用兼容模式
    
    @staticmethod
    def get_legacy_signal_strength(component: Any) -> str:
        """获取原有的信号强度表示"""
        if hasattr(component, 'gfc_level'):
            level = getattr(component, 'gfc_level', 1)
        elif hasattr(component, 'gbc_level'):
            level = getattr(component, 'gbc_level', 1)
        else:
            level = 1
            
        if level >= 4:
            return "极强"
        elif level >= 3:
            return "强"
        elif level >= 2:
            return "中"
        else:
            return "弱"