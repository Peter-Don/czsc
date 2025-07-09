# CZSC Enhanced (缠中说禅增强版) 量化分析项目 API 文档

## **1. 项目概述**

本项目是`缠中说禅`理论的Python实现增强版，基于原始CZSC项目进行深度优化和扩展。项目为量化交易者提供了从原始K线数据到完成缠论结构（分型、笔、线段、中枢）分析的自动化工具，具备以下特点：

- 🎯 **高性能分析**：优化的算法实现，支持大规模数据处理
- 🛠️ **灵活配置**：支持配置文件和代码双重参数配置
- 🔄 **三种笔模式**：标准模式、灵活模式、自适应模式
- 📊 **市场适应性**：针对不同市场（股票、期货、加密货币）的专用配置
- 🔍 **可视化增强**：提供丰富的图表分析和调试工具
- 🔗 **向后兼容**：完全兼容原始CZSC项目的API

### **1.1 项目架构**

```
czsc_enhanced/
├── czsc/                    # 核心库
│   ├── analyze.py          # 主分析器 (CZSC类)
│   ├── objects.py          # 数据结构定义
│   ├── config_loader.py    # 配置管理系统
│   ├── signals/            # 信号生成模块
│   ├── utils/              # 工具函数集
│   └── connectors/         # 数据连接器
├── config/                 # 配置文件
│   └── pen_config.json     # 笔判断配置
├── examples/               # 示例代码
├── tests/                  # 单元测试
└── docs/                   # 文档
```

## **2. 核心模块详解**

### **2.1 文件夹结构与模块功能**

| 文件夹/文件 | 模块功能 | 新增功能 |
| :--- | :--- | :--- |
| **`czsc/`** | **核心库文件夹** | 增强的分析能力和配置管理 |
| `czsc/analyze.py` | **分析器模块** - 核心`CZSC`类 | ✅ 三种笔模式、自适应分析、配置系统集成 |
| `czsc/objects.py` | **数据结构定义** | ✅ 增强的BI对象、ZS对象属性 |
| `czsc/config_loader.py` | **配置管理系统** | ✅ 全新的配置文件系统 |
| `czsc/utils/` | **工具函数模块** | ✅ 增强的可视化、性能优化工具 |
| `czsc/signals/` | **信号生成模块** | ✅ 新增多种技术指标信号 |
| `czsc/connectors/` | **数据连接器** | ✅ 支持多种数据源连接 |
| **`config/`** | **配置文件夹** | ✅ 笔判断、市场参数配置 |
| **`examples/`** | **示例代码** | ✅ 增强版使用示例 |
| **`tests/`** | **单元测试** | ✅ 完整的测试覆盖 |

### **2.2 版本对比**

| 功能 | 原始CZSC | CZSC Enhanced |
| :--- | :--- | :--- |
| 笔判断模式 | 固定标准模式 | 标准/灵活/自适应三种模式 |
| 配置管理 | 硬编码参数 | 配置文件 + 代码参数 |
| 市场适应性 | 通用参数 | 股票/期货/加密货币专用配置 |
| 性能优化 | 基础实现 | 优化算法 + 缓存机制 |
| 可视化 | 基础plotly | 增强的图表和分析工具 |
| 错误处理 | 基础异常 | 完善的错误处理和日志 |

-----

## **3. 核心类与API详解**

### **3.1 `CZSC` 类 - 核心分析器**

**位置**：`czsc/analyze.py:201-680`

这是整个框架的"大脑"，负责执行所有缠论分析。

#### **3.1.1 构造函数**

```python
def __init__(self, bars: List[RawBar], 
             get_signals: Callable = None, 
             max_bi_num: int = 50,
             market_type: str = 'stock',
             threshold_mode: str = 'moderate'):
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `bars` | `List[RawBar]` | 必需 | 原始K线数据列表 |
| `get_signals` | `Callable` | `None` | 信号生成回调函数 |
| `max_bi_num` | `int` | `50` | 最大保存笔数量 |
| `market_type` | `str` | `'stock'` | 市场类型：'stock', 'futures', 'crypto' |
| `threshold_mode` | `str` | `'moderate'` | 阈值模式：'conservative', 'moderate', 'aggressive' |

#### **3.1.2 核心方法**

| 方法 | 功能 | 行号 |
| :--- | :--- | :--- |
| `__init__` | 初始化分析器 | 202-243 |
| `update` | 更新分析（增量数据） | 503-554 |
| `__update_bi` | 更新笔序列 | 336-385 |
| `_check_adaptive_bi` | 检查自适应笔 | 387-432 |
| `_create_adaptive_bi` | 创建自适应笔 | 434-501 |
| `_calculate_indicators` | 计算ATR和成交量指标 | 292-334 |
| `_load_pen_config` | 加载笔配置 | 251-290 |

#### **3.1.3 关键属性**

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `bi_list` | `List[BI]` | 笔序列列表 |
| `bars_ubi` | `List[NewBar]` | 无包含关系的K线 |
| `bars_raw` | `List[RawBar]` | 原始K线数据 |
| `pen_model` | `str` | 笔模式：'standard', 'flexible' |
| `use_adaptive_pen` | `bool` | 是否启用自适应笔 |
| `adaptive_vol_ratio` | `float` | 自适应笔成交量阈值 |
| `adaptive_atr_ratio` | `float` | 自适应笔ATR阈值 |

### **3.2 数据对象结构**

#### **3.2.1 `RawBar` - 原始K线**

**位置**：`czsc/objects.py:32-61`

```python
@dataclass
class RawBar:
    symbol: str          # 交易对
    id: int             # 唯一ID（升序）
    dt: datetime        # 时间戳
    freq: Freq          # 频率
    open: float         # 开盘价
    close: float        # 收盘价
    high: float         # 最高价
    low: float          # 最低价
    vol: float          # 成交量
    amount: float       # 成交额
    cache: dict         # 缓存字典
```

**关键属性**：
- `upper`: 上影线长度
- `lower`: 下影线长度  
- `solid`: 实体长度

#### **3.2.2 `NewBar` - 去包含关系K线**

**位置**：`czsc/objects.py:63-83`

```python
@dataclass
class NewBar:
    # ... 基础属性同RawBar
    elements: List[RawBar]  # 包含的原始K线
```

#### **3.2.3 `FX` - 分型对象**

**位置**：`czsc/objects.py:85-100`

```python
@dataclass
class FX:
    symbol: str
    dt: datetime
    mark: Mark          # Mark.G(顶) 或 Mark.D(底)
    high: float
    low: float
    fx: float          # 分型价格
    elements: List[NewBar]  # 构成分型的K线
```

#### **3.2.4 `BI` - 笔对象**

**位置**：`czsc/objects.py:200-366`

```python
@dataclass
class BI:
    symbol: str
    fx_a: FX           # 起始分型
    fx_b: FX           # 结束分型
    fxs: List[FX]      # 内部分型
    direction: Direction  # 方向
    bars: List[NewBar]    # 构成笔的K线
```

**关键属性**：
- `sdt`, `edt`: 开始/结束时间
- `high`, `low`: 最高/最低价
- `power_price`: 价格能量
- `power_volume`: 成交量能量
- `change`: 涨跌幅
- `length`: 笔的长度（K线数量）
- `angle`: 笔的角度
- `slope`: 笔的斜率

#### **3.2.5 `ZS` - 中枢对象**

**位置**：`czsc/objects.py:368-448`

```python
@dataclass
class ZS:
    bis: List[BI]      # 构成中枢的笔
```

**关键属性**：
- `zz`: 中枢中轴
- `zg`: 中枢上沿
- `zd`: 中枢下沿
- `gg`: 中枢最高点
- `dd`: 中枢最低点
- `sdt`, `edt`: 开始/结束时间
- `is_valid`: 中枢有效性验证

-----

## **4. 配置系统详解**

### **4.1 配置文件结构**

**位置**：`config/pen_config.json`

```json
{
    "pen_settings": {
        "default_pen_model": "standard",
        "default_use_adaptive_pen": false,
        "standard_mode": {
            "min_bi_len": 5,
            "description": "标准模式：严格的5根K线笔判断"
        },
        "flexible_mode": {
            "min_bi_len": 3,
            "description": "灵活模式：允许3根K线成笔"
        },
        "adaptive_mode": {
            "enabled": true,
            "volume_ratio": 2.5,
            "atr_ratio": 1.8,
            "atr_period": 14,
            "volume_period": 20
        }
    },
    "adaptive_thresholds": {
        "conservative": {"volume_ratio": 1.5, "atr_ratio": 1.0},
        "moderate": {"volume_ratio": 2.0, "atr_ratio": 1.5},
        "aggressive": {"volume_ratio": 3.0, "atr_ratio": 2.5}
    },
    "market_specific": {
        "crypto": {"volume_ratio": 2.5, "atr_ratio": 2.0},
        "stock": {"volume_ratio": 1.8, "atr_ratio": 1.5},
        "futures": {"volume_ratio": 2.2, "atr_ratio": 1.8}
    }
}
```

### **4.2 配置加载器**

**位置**：`czsc/config_loader.py`

```python
from czsc.config_loader import pen_config

# 获取配置
config = pen_config.get_pen_config_for_market('crypto', 'aggressive')

# 修改配置
pen_config.update_adaptive_config(
    volume_ratio=2.5,
    atr_ratio=1.8,
    enabled=True
)
```

### **4.3 三种笔模式详解**

#### **4.3.1 标准模式 (Standard)**

- **最小笔长度**：5根K线
- **特点**：严格的笔判断，保持与原始CZSC完全一致
- **适用场景**：稳定市场、长期分析
- **代码位置**：`czsc/analyze.py:336-385`

```python
# 使用标准模式
c = CZSC(bars, market_type='stock')  # 默认为标准模式
```

#### **4.3.2 灵活模式 (Flexible)**

- **最小笔长度**：3根K线
- **特点**：更敏感的笔判断，能捕捉短期转折
- **适用场景**：高频交易、短期策略
- **代码位置**：`czsc/analyze.py:141-198`

```python
# 使用灵活模式
c = CZSC(bars, pen_model='flexible')
```

#### **4.3.3 自适应模式 (Adaptive)**

- **触发条件**：成交量放大 + ATR异常 + 价格反转
- **特点**：专门处理极端市场情况
- **适用场景**：突发事件、市场异常波动
- **代码位置**：`czsc/analyze.py:387-501`

```python
# 使用自适应模式
c = CZSC(bars, 
         pen_model='flexible',
         use_adaptive_pen=True,
         adaptive_vol_ratio=2.0,
         adaptive_atr_ratio=1.5)
```

-----

## **5. 实用API接口**

### **5.1 基础使用**

#### **5.1.1 快速开始**

```python
from czsc.analyze import CZSC
from czsc.objects import RawBar
from czsc.enum import Freq
from datetime import datetime

# 创建K线数据
bars = [
    RawBar(symbol='BTCUSDT', id=i, dt=datetime.now(), freq=Freq.F1,
           open=100, close=101, high=102, low=99, vol=1000, amount=100000)
    for i in range(100)
]

# 创建分析器
c = CZSC(bars)

# 查看结果
print(f"笔数量: {len(c.bi_list)}")
print(f"最新笔: {c.bi_list[-1] if c.bi_list else None}")
```

#### **5.1.2 增量更新**

```python
# 添加新的K线数据
new_bar = RawBar(symbol='BTCUSDT', id=100, dt=datetime.now(), 
                 freq=Freq.F1, open=101, close=102, high=103, 
                 low=100, vol=1200, amount=122000)

# 更新分析
c.update(new_bar)
```

### **5.2 高级配置**

#### **5.2.1 市场特定配置**

```python
# 加密货币市场
c_crypto = CZSC(bars, market_type='crypto', threshold_mode='aggressive')

# 股票市场
c_stock = CZSC(bars, market_type='stock', threshold_mode='moderate')

# 期货市场
c_futures = CZSC(bars, market_type='futures', threshold_mode='conservative')
```

#### **5.2.2 自定义参数**

```python
# 完全自定义配置
c = CZSC(bars,
         pen_model='flexible',           # 灵活模式
         use_adaptive_pen=True,          # 启用自适应
         adaptive_vol_ratio=2.5,         # 成交量阈值
         adaptive_atr_ratio=1.8,         # ATR阈值
         market_type='crypto',           # 市场类型
         threshold_mode='moderate')      # 阈值模式
```

### **5.3 数据分析接口**

#### **5.3.1 笔分析**

```python
# 获取最新笔
latest_bi = c.bi_list[-1] if c.bi_list else None

if latest_bi:
    print(f"笔方向: {latest_bi.direction}")
    print(f"笔长度: {latest_bi.length}")
    print(f"价格变化: {latest_bi.change:.2%}")
    print(f"笔角度: {latest_bi.angle:.2f}°")
    print(f"成交量能量: {latest_bi.power_volume}")
```

#### **5.3.2 分型分析**

```python
# 检查分型
from czsc.analyze import check_fx

if len(c.bars_ubi) >= 3:
    fx = check_fx(c.bars_ubi[-3], c.bars_ubi[-2], c.bars_ubi[-1])
    if fx:
        print(f"发现分型: {fx.mark} at {fx.fx}")
```

#### **5.3.3 中枢分析**

```python
# 分析中枢（需要至少3笔）
from czsc.objects import ZS

if len(c.bi_list) >= 3:
    zs = ZS(c.bi_list[-3:])
    if zs.is_valid:
        print(f"中枢区间: {zs.zd:.2f} - {zs.zg:.2f}")
        print(f"中枢强度: {(zs.zg - zs.zd) / zs.zz:.2%}")
```

-----

## **6. 信号生成系统**

### **6.1 信号模块结构**

**位置**：`czsc/signals/`

| 模块 | 功能 | 主要信号 |
| :--- | :--- | :--- |
| `bar.py` | K线信号 | 大阳线、大阴线、十字星 |
| `bi.py` | 笔信号 | 笔长度、笔角度、笔强度 |
| `zs.py` | 中枢信号 | 中枢突破、中枢震荡 |
| `vol.py` | 成交量信号 | 量价配合、异常放量 |
| `tas.py` | 技术指标信号 | MACD、RSI、布林带 |

### **6.2 信号使用示例**

```python
from czsc.signals.bar import bar_big_yang_V240101
from czsc.signals.bi import bi_angle_V240101

# 定义信号函数
def get_signals(c: CZSC) -> Dict[str, Any]:
    signals = {}
    
    # K线信号
    signals.update(bar_big_yang_V240101(c))
    
    # 笔信号
    signals.update(bi_angle_V240101(c))
    
    return signals

# 使用信号
c = CZSC(bars, get_signals=get_signals)
```

-----

## **7. 性能优化与最佳实践**

### **7.1 性能优化**

#### **7.1.1 大数据处理**

```python
# 限制保存的笔数量
c = CZSC(bars, max_bi_num=100)

# 使用缓存
bar.cache['atr'] = calculate_atr(bars)
```

#### **7.1.2 增量更新**

```python
# 批量更新（推荐）
for bar in new_bars:
    c.update(bar)

# 避免频繁重建
# 不推荐：c = CZSC(all_bars)  # 每次都重建
```

### **7.2 错误处理**

```python
try:
    c = CZSC(bars)
except Exception as e:
    logger.error(f"CZSC初始化失败: {e}")
    # 使用默认配置重试
    c = CZSC(bars, market_type='stock')
```

### **7.3 调试工具**

```python
from czsc.config_loader import pen_config

# 查看配置
pen_config.print_config_info()

# 日志调试
import logging
logging.basicConfig(level=logging.DEBUG)
```

-----

## **8. 可视化与分析工具**

### **8.1 基础可视化**

```python
# 使用内置可视化（如果可用）
if hasattr(c, 'show'):
    c.show()

# 使用增强可视化
from czsc_enhanced.enhanced_visualization import plot_czsc_analysis
plot_czsc_analysis(c)
```

### **8.2 分析报告**

```python
# 生成分析报告
def generate_analysis_report(c: CZSC):
    report = {
        'total_bi': len(c.bi_list),
        'latest_bi': c.bi_list[-1] if c.bi_list else None,
        'avg_bi_length': sum(bi.length for bi in c.bi_list) / len(c.bi_list) if c.bi_list else 0,
        'config': {
            'pen_model': c.pen_model,
            'use_adaptive_pen': c.use_adaptive_pen,
            'market_type': getattr(c, 'market_type', 'unknown')
        }
    }
    return report
```

-----

## **9. 扩展开发指南**

### **9.1 自定义信号**

```python
def custom_signal_V240101(c: CZSC) -> Dict[str, Any]:
    """
    自定义信号示例
    """
    signals = {}
    
    if len(c.bi_list) >= 2:
        bi1, bi2 = c.bi_list[-2:]
        
        # 自定义逻辑
        if bi1.direction != bi2.direction and bi2.power_volume > bi1.power_volume * 1.5:
            signals['custom_signal'] = 'strong_reversal'
        else:
            signals['custom_signal'] = 'normal'
    
    return signals
```

### **9.2 自定义配置**

```python
# 添加新的市场类型
custom_config = {
    "market_specific": {
        "commodity": {
            "volume_ratio": 2.0,
            "atr_ratio": 1.6,
            "description": "商品市场"
        }
    }
}

# 保存配置
pen_config.save_config(custom_config)
```

### **9.3 插件开发**

```python
class CustomAnalyzer:
    def __init__(self, czsc: CZSC):
        self.czsc = czsc
    
    def analyze_trend(self):
        """自定义趋势分析"""
        if len(self.czsc.bi_list) >= 3:
            # 实现自定义逻辑
            pass
    
    def generate_signals(self):
        """生成自定义信号"""
        pass
```

-----

## **10. 故障排除与FAQ**

### **10.1 常见问题**

**Q: 配置文件修改后不生效？**
A: 需要重新导入配置或重启程序。

**Q: 自适应笔不触发？**
A: 检查`adaptive_vol_ratio`和`adaptive_atr_ratio`参数是否过于严格。

**Q: 内存使用过高？**
A: 设置`max_bi_num`限制保存的笔数量。

**Q: 计算速度慢？**
A: 使用增量更新而非全量重建。

### **10.2 调试技巧**

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查数据质量
def check_data_quality(bars):
    for i, bar in enumerate(bars):
        if bar.high < bar.low:
            print(f"数据异常: 第{i}根K线高点小于低点")
        if bar.vol < 0:
            print(f"数据异常: 第{i}根K线成交量为负")

# 性能监控
import time
start_time = time.time()
c = CZSC(bars)
print(f"初始化耗时: {time.time() - start_time:.2f}秒")
```

-----

## **11. 版本更新日志**

### **v2.0.0 (Enhanced)**
- ✅ 新增三种笔模式
- ✅ 配置文件系统
- ✅ 市场适应性配置
- ✅ 性能优化
- ✅ 增强的可视化

### **v1.0.0 (Original)**
- ✅ 基础缠论分析
- ✅ 分型、笔、中枢识别
- ✅ 基础信号生成

-----

## **12. 总结**

CZSC Enhanced 在保持与原始CZSC项目完全兼容的基础上，提供了：

1. **🎯 更强的适应性**：三种笔模式适应不同市场环境
2. **🛠️ 更好的可配置性**：配置文件系统支持灵活参数调整
3. **📊 更高的性能**：优化的算法和缓存机制
4. **🔍 更丰富的功能**：增强的分析工具和可视化
5. **📚 更完善的文档**：详细的API文档和使用指南

建议用户从基础使用开始，逐步探索高级功能，根据自己的交易策略选择合适的配置参数。

---

**技术支持**: 如有问题，请提交Issue或查看示例代码。
**许可证**: 遵循原始CZSC项目的开源许可证。