# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/3/10 11:21
describe: 缠论分型、笔的识别
"""
import os
import webbrowser
from loguru import logger
from typing import List
from collections import OrderedDict
from czsc.enum import Mark, Direction
from czsc.objects import BI, FX, RawBar, NewBar
from czsc.utils.echarts_plot import kline_pro
from czsc import envs
from czsc.config_loader import pen_config

logger.disable('czsc.analyze')


def remove_include_smart(k1: NewBar, k2: NewBar, k3: RawBar):
    """智能包含关系处理：改进版本的包含关系去除算法
    
    改进点：
    1. 更精确的方向判断：同时考虑高点和低点
    2. 更合理的开收盘价计算：保持价格连续性
    3. 更稳定的elements管理：避免过大数组问题
    4. 更智能的时间戳选择：基于价格重要性
    
    :param k1: 前两根处理好的K线，用于判断方向
    :param k2: 前一根处理好的K线
    :param k3: 当前原始K线
    :return: (is_included, new_bar)
    """
    # 改进1：更精确的方向判断，同时考虑高点和低点
    if k1.high < k2.high or (k1.high == k2.high and k1.low < k2.low):
        direction = Direction.Up
    elif k1.high > k2.high or (k1.high == k2.high and k1.low > k2.low):
        direction = Direction.Down
    else:
        # 完全相等的情况，直接返回新K线
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, amount=k3.amount, elements=[k3])
        return False, k4

    # 判断 k2 和 k3 之间是否存在包含关系
    if (k2.high <= k3.high and k2.low >= k3.low) or (k2.high >= k3.high and k2.low <= k3.low):
        
        if direction == Direction.Up:
            high = max(k2.high, k3.high)
            low = max(k2.low, k3.low)
            # 改进4：更智能的时间戳选择，基于价格重要性
            dt = k2.dt if k2.high >= k3.high else k3.dt

        elif direction == Direction.Down:
            high = min(k2.high, k3.high)
            low = min(k2.low, k3.low)
            dt = k2.dt if k2.low <= k3.low else k3.dt

        else:
            raise ValueError

        # 改进2：更合理的开收盘价计算，保持价格连续性
        open_ = k2.open  # 开盘价使用前一根K线的开盘价，保持连续性
        close = k3.close  # 收盘价使用当前K线的收盘价，反映最新状态
        
        vol = k2.vol + k3.vol
        amount = k2.amount + k3.amount

        # 改进3：更稳定的elements管理，避免过大数组问题
        # 限制elements数量在合理范围内，同时保持时间顺序
        max_elements = 50  # 设置合理的上限
        existing_elements = [x for x in k2.elements if x.dt != k3.dt]
        
        # 如果超过上限，保留最近的elements
        if len(existing_elements) > max_elements - 1:
            existing_elements = existing_elements[-(max_elements - 1):]
            
        elements = existing_elements + [k3]
        
        k4 = NewBar(symbol=k3.symbol, id=k2.id, freq=k2.freq, dt=dt, open=open_,
                    close=close, high=high, low=low, vol=vol, amount=amount, elements=elements)
        return True, k4

    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, amount=k3.amount, elements=[k3])
        return False, k4


def remove_include_legacy(k1: NewBar, k2: NewBar, k3: RawBar):
    """传统包含关系处理：原始版本的包含关系去除算法
    
    保留作为备用方案，默认使用新的智能处理方式
    """
    if k1.high < k2.high:
        direction = Direction.Up
    elif k1.high > k2.high:
        direction = Direction.Down
    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, amount=k3.amount, elements=[k3])
        return False, k4

    # 判断 k2 和 k3 之间是否存在包含关系，有则处理
    if (k2.high <= k3.high and k2.low >= k3.low) or (k2.high >= k3.high and k2.low <= k3.low):

        if direction == Direction.Up:
            high = max(k2.high, k3.high)
            low = max(k2.low, k3.low)
            dt = k2.dt if k2.high > k3.high else k3.dt

        elif direction == Direction.Down:
            high = min(k2.high, k3.high)
            low = min(k2.low, k3.low)
            dt = k2.dt if k2.low < k3.low else k3.dt

        else:
            raise ValueError

        open_, close = (high, low) if k3.open > k3.close else (low, high)
        vol = k2.vol + k3.vol
        amount = k2.amount + k3.amount

        # 这里有一个隐藏Bug，len(k2.elements) 在一些及其特殊的场景下会有超大的数量，具体问题还没找到；
        # 临时解决方案是直接限定len(k2.elements)<=100
        elements = [x for x in k2.elements[:100] if x.dt != k3.dt] + [k3]
        k4 = NewBar(symbol=k3.symbol, id=k2.id, freq=k2.freq, dt=dt, open=open_,
                    close=close, high=high, low=low, vol=vol, amount=amount, elements=elements)
        return True, k4

    else:
        k4 = NewBar(symbol=k3.symbol, id=k3.id, freq=k3.freq, dt=k3.dt, open=k3.open,
                    close=k3.close, high=k3.high, low=k3.low, vol=k3.vol, amount=k3.amount, elements=[k3])
        return False, k4


def remove_include(k1: NewBar, k2: NewBar, k3: RawBar):
    """默认包含关系处理：使用新的智能处理方式"""
    return remove_include_smart(k1, k2, k3)


def check_fx(k1: NewBar, k2: NewBar, k3: NewBar):
    """查找分型

    函数计算逻辑：

    1. 如果第二个`NewBar`对象的最高价和最低价都高于第一个和第三个`NewBar`对象的对应价格，那么它被认为是顶分型（G）。
       在这种情况下，函数会创建一个新的`FX`对象，其标记为`Mark.G`，并将其赋值给`fx`。

    2. 如果第二个`NewBar`对象的最高价和最低价都低于第一个和第三个`NewBar`对象的对应价格，那么它被认为是底分型（D）。
       在这种情况下，函数会创建一个新的`FX`对象，其标记为`Mark.D`，并将其赋值给`fx`。

    3. 函数最后返回`fx`，如果没有找到分型，`fx`将为`None`。

    :param k1: 第一个`NewBar`对象
    :param k2: 第二个`NewBar`对象
    :param k3: 第三个`NewBar`对象
    :return: `FX`对象或`None`
    """
    fx = None
    if k1.high < k2.high > k3.high and k1.low < k2.low > k3.low:
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.G, high=k2.high,
                low=k2.low, fx=k2.high, elements=[k1, k2, k3])

    if k1.low > k2.low < k3.low and k1.high > k2.high < k3.high:
        fx = FX(symbol=k1.symbol, dt=k2.dt, mark=Mark.D, high=k2.high,
                low=k2.low, fx=k2.low, elements=[k1, k2, k3])

    return fx


def check_fxs(bars: List[NewBar]) -> List[FX]:
    """输入一串无包含关系K线，查找其中所有分型

    函数的主要步骤：

    1. 创建一个空列表`fxs`用于存储找到的分型。
    2. 遍历`bars`列表中的每个元素（除了第一个和最后一个），并对每三个连续的`NewBar`对象调用`check_fx`函数。
    3. 如果`check_fx`函数返回一个`FX`对象，检查它的标记是否与`fxs`列表中最后一个`FX`对象的标记相同。如果相同，记录一个错误日志。
       如果不同，将这个`FX`对象添加到`fxs`列表中。
    4. 最后返回`fxs`列表，它包含了`bars`列表中所有找到的分型。

    这个函数的主要目的是找出`bars`列表中所有的顶分型和底分型，并确保它们是交替出现的。如果发现连续的两个分型标记相同，它会记录一个错误日志。

    :param bars: 无包含关系K线列表
    :return: 分型列表
    """
    fxs = []
    for i in range(1, len(bars) - 1):
        fx = check_fx(bars[i - 1], bars[i], bars[i + 1])
        if isinstance(fx, FX):
            # 默认情况下，fxs本身是顶底交替的，但是对于一些特殊情况下不是这样; 临时强制要求fxs序列顶底交替
            if len(fxs) >= 2 and fx.mark == fxs[-1].mark:
                logger.error(f"check_fxs错误: {bars[i].dt}，{fx.mark}，{fxs[-1].mark}")
            else:
                fxs.append(fx)
    return fxs


def enhance_fx_level(fx: FX, bi_list: List[BI], all_fxs: List[FX]) -> None:
    """增强分型级别
    
    基于缠论分型增强理论，对分型进行级别判断和增强：
    1. 分型的基本级别为1级
    2. 二级分型条件：分型被后续一笔破坏，且该笔力度较强
    3. 三级分型条件：分型被后续两笔破坏，且两笔都有较强力度
    
    :param fx: 待增强的分型
    :param bi_list: 笔列表
    :param all_fxs: 所有分型列表
    """
    if not bi_list:
        return
        
    # 找到与此分型相关的笔
    related_bis = []
    for bi in bi_list:
        if bi.fx_a.dt == fx.dt or bi.fx_b.dt == fx.dt:
            related_bis.append(bi)
        elif any(f.dt == fx.dt for f in bi.fxs):
            related_bis.append(bi)
    
    # 分析分型后的价格行为
    later_fxs = [f for f in all_fxs if f.dt > fx.dt]
    
    # 二级分型判断
    level_2_reasons = []
    if related_bis:
        for bi in related_bis:
            # 检查笔的力度
            if bi.power_price > 0:
                # 根据分型类型判断是否被破坏
                if fx.mark == Mark.G:  # 顶分型
                    if bi.direction == Direction.Down and bi.fx_b.fx < fx.fx:
                        level_2_reasons.append(f"被{bi.direction.value}笔破坏,力度{bi.power_price:.2f}")
                elif fx.mark == Mark.D:  # 底分型
                    if bi.direction == Direction.Up and bi.fx_b.fx > fx.fx:
                        level_2_reasons.append(f"被{bi.direction.value}笔破坏,力度{bi.power_price:.2f}")
    
    # 三级分型判断
    level_3_reasons = []
    if len(related_bis) >= 2:
        strong_bis = [bi for bi in related_bis if bi.power_price > 0]
        if len(strong_bis) >= 2:
            level_3_reasons.append(f"被{len(strong_bis)}笔连续破坏")
    
    # 基于后续分型的反弹/回调判断
    if later_fxs:
        opposite_fxs = [f for f in later_fxs[:5] if f.mark != fx.mark]  # 取前5个相反分型
        if opposite_fxs:
            first_opposite = opposite_fxs[0]
            if fx.mark == Mark.G:  # 顶分型
                if first_opposite.fx < fx.fx * 0.95:  # 跌幅超过5%
                    level_2_reasons.append(f"后续{first_opposite.mark.value}分型大幅破坏")
            elif fx.mark == Mark.D:  # 底分型
                if first_opposite.fx > fx.fx * 1.05:  # 涨幅超过5%
                    level_2_reasons.append(f"后续{first_opposite.mark.value}分型大幅破坏")
    
    # 更新分型级别
    fx.level_2_reasons = level_2_reasons
    fx.level_3_reasons = level_3_reasons
    
    if level_3_reasons:
        fx.gfc_level = 3
    elif level_2_reasons:
        fx.gfc_level = 2
    else:
        fx.gfc_level = 1


def enhance_bi_level(bi: BI, all_bis: List[BI]) -> None:
    """增强笔级别
    
    基于缠论笔增强理论，对笔进行级别判断和增强：
    1. 笔的基本级别为1级
    2. 二级笔条件：笔的起始或结束分型为二级分型
    3. 三级笔条件：笔的起始或结束分型为三级分型，或笔本身具有特殊结构
    
    :param bi: 待增强的笔
    :param all_bis: 所有笔列表
    """
    level_2_reasons = []
    level_3_reasons = []
    
    # 基于分型级别判断笔级别
    if bi.fx_a.gfc_level >= 2:
        level_2_reasons.append(f"起始分型为{bi.fx_a.level_description}")
    if bi.fx_b.gfc_level >= 2:
        level_2_reasons.append(f"结束分型为{bi.fx_b.level_description}")
    
    if bi.fx_a.gfc_level >= 3:
        level_3_reasons.append(f"起始分型为{bi.fx_a.level_description}")
    if bi.fx_b.gfc_level >= 3:
        level_3_reasons.append(f"结束分型为{bi.fx_b.level_description}")
    
    # 基于笔的力度判断
    if bi.power_price > 0:
        # 找到相邻的笔
        bi_index = all_bis.index(bi) if bi in all_bis else -1
        if bi_index > 0:
            prev_bi = all_bis[bi_index - 1]
            if prev_bi.power_price > 0:
                power_ratio = bi.power_price / prev_bi.power_price
                if power_ratio > 1.5:  # 力度比前一笔大50%以上
                    level_2_reasons.append(f"力度比前笔强{power_ratio:.2f}倍")
                elif power_ratio > 2.0:  # 力度比前一笔大100%以上
                    level_3_reasons.append(f"力度比前笔强{power_ratio:.2f}倍")
    
    # 基于笔的内部结构判断
    if len(bi.fxs) > 3:  # 内部分型较多
        high_level_fxs = [fx for fx in bi.fxs if fx.gfc_level >= 2]
        if high_level_fxs:
            level_2_reasons.append(f"内部有{len(high_level_fxs)}个高级分型")
    
    # 基于SNR判断
    if hasattr(bi, 'SNR') and bi.SNR > 0:
        if bi.SNR > 0.8:  # 信噪比较高
            level_2_reasons.append(f"信噪比高{bi.SNR:.3f}")
        elif bi.SNR > 0.9:
            level_3_reasons.append(f"信噪比极高{bi.SNR:.3f}")
    
    # 更新笔级别
    bi.level_2_reasons = level_2_reasons
    bi.level_3_reasons = level_3_reasons
    
    if level_3_reasons:
        bi.gbc_level = 3
    elif level_2_reasons:
        bi.gbc_level = 2
    else:
        bi.gbc_level = 1


def check_bi(bars: List[NewBar], pen_model: str = 'standard', **kwargs):
    """输入一串无包含关系K线，查找其中的一笔

    :param bars: 无包含关系K线列表 (NewBar序列，已去除包含关系)
    :param pen_model: 笔模式，'standard'(严格模式，至少3根) 或 'flexible'(灵活模式，至少1根)
    :return:
    """
    fxs = check_fxs(bars)
    if len(fxs) < 2:
        return None, bars

    fx_a = fxs[0]
    if fx_a.mark == Mark.D:
        direction = Direction.Up
        fxs_b = [x for x in fxs if x.mark == Mark.G and x.dt > fx_a.dt and x.fx > fx_a.fx]
        if len(fxs_b) == 0:
            return None, bars
        fx_b = max(fxs_b, key=lambda fx: fx.high)

    elif fx_a.mark == Mark.G:
        direction = Direction.Down
        fxs_b = [x for x in fxs if x.mark == Mark.D and x.dt > fx_a.dt and x.fx < fx_a.fx]
        if len(fxs_b) == 0:
            return None, bars
        fx_b = min(fxs_b, key=lambda fx: fx.low)

    else:
        raise ValueError

    bars_a = [x for x in bars if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
    bars_b = [x for x in bars if x.dt >= fx_b.elements[0].dt]

    # 判断fx_a和fx_b价格区间是否存在包含关系
    ab_include = (fx_a.high > fx_b.high and fx_a.low < fx_b.low) or (fx_a.high < fx_b.high and fx_a.low > fx_b.low)

    # 根据笔模式设置最小K线数量要求
    if pen_model == 'standard':
        min_bars = 5  # 严格模式：至少5根K线(相邻分型间隔至少3根)
    elif pen_model == 'flexible':
        min_bars = 4  # 灵活模式：至少3根K线(相邻分型间隔至少2根)
    else:
        min_bars = envs.get_min_bi_len()  # 默认值

    # 成笔的条件
    if (not ab_include) and (len(bars_a) >= min_bars):
        fxs_ = [x for x in fxs if fx_a.elements[0].dt <= x.dt <= fx_b.elements[2].dt]
        bi = BI(symbol=fx_a.symbol, fx_a=fx_a, fx_b=fx_b, fxs=fxs_, direction=direction, bars=bars_a)
        return bi, bars_b
    else:
        return None, bars


class CZSC:
    def __init__(self,
                 bars: List[RawBar],
                 get_signals = None,
                 max_bi_num=envs.get_max_bi_num(),
                 pen_model: str = 'standard',
                 ):
        """

        :param bars: K线数据
        :param max_bi_num: 最大允许保留的笔数量
        :param get_signals: 自定义的信号计算函数
        :param pen_model: 笔模式，'standard'(标准5K线) 或 'flexible'(灵活3K线)
        """
        self.verbose = envs.get_verbose()
        self.max_bi_num = max_bi_num
        self.bars_raw: List[RawBar] = []  # 原始K线序列
        self.bars_ubi: List[NewBar] = []  # 未完成笔的无包含K线序列
        self.bi_list: List[BI] = []
        self.symbol = bars[0].symbol
        self.freq = bars[0].freq
        self.get_signals = get_signals
        self.signals = None
        # cache 是信号计算过程的缓存容器，需要信号计算函数自行维护
        self.cache = OrderedDict()
        
        # 笔模式参数
        self.pen_model = pen_model
        
        # 分级分型增强功能开关
        self.enable_level_enhancement = True  # 是否启用分级分型增强
        self.enhancement_update_interval = 10  # 每10根K线更新一次分级分型
        self.enhancement_counter = 0  # 增强计数器
        
        # FVG检测器
        from czsc.poi.fvg import FVGDetector
        self.fvg_detector = FVGDetector()
        
        # OB检测器 - 使用更适合加密货币的宽松参数
        from czsc.poi.ob import OBDetector
        self.ob_detector = OBDetector({
            'min_breakout_ratio': 0.8,      # 降低突破比例要求
            'min_volume_ratio': 0.8,        # 降低成交量要求
            'min_ob_bars': 3,               # 最少K线数
            'max_ob_bars': 20,              # 增加最大K线数
            'test_threshold': 0.5           # 测试阈值
        })
        
        # 组件保存路径
        self.save_components = True  # 是否保存组件信息
        self.components_file = None  # 组件保存文件路径
        
        if self.verbose:
            print(f"[CZSC] 笔模式: {self.pen_model}")

        for bar in bars:
            self.update(bar)

    def __repr__(self):
        return "<CZSC~{}~{}>".format(self.symbol, self.freq.value)
    
    def __update_level_enhancement(self):
        """更新分级分型增强"""
        if not self.enable_level_enhancement:
            return
            
        # 获取所有分型列表
        all_fxs = self.fx_list
        if not all_fxs:
            return
            
        # 对所有分型进行级别增强
        for fx in all_fxs:
            enhance_fx_level(fx, self.bi_list, all_fxs)
        
        # 对所有笔进行级别增强
        for bi in self.bi_list:
            enhance_bi_level(bi, self.bi_list)
        
        if self.verbose:
            level_2_fxs = [fx for fx in all_fxs if fx.gfc_level >= 2]
            level_3_fxs = [fx for fx in all_fxs if fx.gfc_level >= 3]
            level_2_bis = [bi for bi in self.bi_list if bi.gbc_level >= 2]
            level_3_bis = [bi for bi in self.bi_list if bi.gbc_level >= 3]
            
            if level_2_fxs or level_3_fxs or level_2_bis or level_3_bis:
                print(f"[CZSC] 分级分型增强 - 二级分型:{len(level_2_fxs)}个, 三级分型:{len(level_3_fxs)}个")
                print(f"[CZSC] 分级分型增强 - 二级笔:{len(level_2_bis)}个, 三级笔:{len(level_3_bis)}个")
    
    

    def __update_bi(self):
        bars_ubi = self.bars_ubi
        
        if len(bars_ubi) < 3:
            return

        # 查找笔
        if not self.bi_list:
            # 第一笔的查找
            fxs = check_fxs(bars_ubi)
            if not fxs:
                return

            fx_a = fxs[0]
            fxs_a = [x for x in fxs if x.mark == fx_a.mark]
            for fx in fxs_a:
                if (fx_a.mark == Mark.D and fx.low <= fx_a.low) \
                        or (fx_a.mark == Mark.G and fx.high >= fx_a.high):
                    fx_a = fx
            bars_ubi = [x for x in bars_ubi if x.dt >= fx_a.elements[0].dt]

            bi, bars_ubi_ = check_bi(bars_ubi, pen_model=self.pen_model)
            if isinstance(bi, BI):
                self.bi_list.append(bi)
            self.bars_ubi = bars_ubi_
            return

        if self.verbose and len(bars_ubi) > 100:
            logger.info(f"{self.symbol} - {self.freq} - {bars_ubi[-1].dt} 未完成笔延伸数量: {len(bars_ubi)}")

        bi, bars_ubi_ = check_bi(bars_ubi, pen_model=self.pen_model)
        self.bars_ubi = bars_ubi_
        if isinstance(bi, BI):
            self.bi_list.append(bi)

        # 后处理：如果当前笔被破坏，将当前笔的bars与bars_ubi进行合并，并丢弃
        last_bi = self.bi_list[-1]
        bars_ubi = self.bars_ubi
        if (last_bi.direction == Direction.Up and bars_ubi[-1].high > last_bi.high) \
                or (last_bi.direction == Direction.Down and bars_ubi[-1].low < last_bi.low):
            # 当前笔被破坏，将当前笔的bars与bars_ubi进行合并，并丢弃
            # 添加安全检查防止索引越界
            if len(last_bi.bars) >= 2:
                self.bars_ubi = last_bi.bars[:-2] + [x for x in bars_ubi if x.dt >= last_bi.bars[-2].dt]
            else:
                # 如果笔的bars太少，直接使用当前bars_ubi
                self.bars_ubi = last_bi.bars + bars_ubi
            self.bi_list.pop(-1)
    
    

    def update(self, bar: RawBar):
        """更新分析结果

        :param bar: 单根K线对象
        """
        # 更新K线序列
        if not self.bars_raw or bar.dt != self.bars_raw[-1].dt:
            self.bars_raw.append(bar)
            last_bars = [bar]
        else:
            # 当前 bar 是上一根 bar 的时间延伸
            self.bars_raw[-1] = bar
            last_bars = self.bars_ubi.pop(-1).raw_bars
            assert bar.dt == last_bars[-1].dt, f"{bar.dt} != {last_bars[-1].dt}，时间错位"
            last_bars[-1] = bar

        # 去除包含关系
        bars_ubi = self.bars_ubi
        for bar in last_bars:
            if len(bars_ubi) < 2:
                bars_ubi.append(NewBar(symbol=bar.symbol, id=bar.id, freq=bar.freq, dt=bar.dt,
                                       open=bar.open, close=bar.close, amount=bar.amount,
                                       high=bar.high, low=bar.low, vol=bar.vol, elements=[bar]))
            else:
                k1, k2 = bars_ubi[-2:]
                has_include, k3 = remove_include(k1, k2, bar)
                if has_include:
                    bars_ubi[-1] = k3
                else:
                    bars_ubi.append(k3)
        self.bars_ubi = bars_ubi

        # 更新笔
        self.__update_bi()

        # 根据最大笔数量限制完成 bi_list, bars_raw 序列的数量控制
        self.bi_list = self.bi_list[-self.max_bi_num:]
        if self.bi_list:
            sdt = self.bi_list[0].fx_a.elements[0].dt
            s_index = 0
            for i, bar in enumerate(self.bars_raw):
                if bar.dt >= sdt:
                    s_index = i
                    break
            self.bars_raw = self.bars_raw[s_index:]
        
        # 更新FVG检测器 - 基于分型检测FVG
        if len(self.fx_list) >= 3:
            # 将原始K线转换为NewBar格式用于FVG检测
            newbars = []
            for bar in self.bars_raw:
                newbar = NewBar(
                    symbol=bar.symbol,
                    id=bar.id,
                    dt=bar.dt,
                    freq=bar.freq,
                    open=bar.open,
                    close=bar.close,
                    high=bar.high,
                    low=bar.low,
                    vol=bar.vol,
                    amount=bar.amount,
                    elements=[bar]
                )
                newbars.append(newbar)
            
            # 使用分型和原始K线进行FVG检测
            self.fvg_detector.update_fvgs(newbars, self.fx_list)
            
            # 使用原始K线进行OB检测
            self.ob_detector.update_obs(newbars)

        
        # 分级分型增强逻辑
        if self.enable_level_enhancement:
            self.enhancement_counter += 1
            # 每隔一定数量的K线更新一次分级分型，以提高效率
            if self.enhancement_counter >= self.enhancement_update_interval:
                self.__update_level_enhancement()
                self.enhancement_counter = 0
        
        # 如果有信号计算函数，则进行信号计算
        self.signals = self.get_signals(c=self) if self.get_signals else OrderedDict()
    
    def save_components_to_csv(self, file_path: str = None):
        """保存组件信息到CSV文件"""
        import pandas as pd
        import os
        
        if file_path is None:
            file_path = f"{self.symbol}_{self.freq.value}_components.csv"
        
        # 准备数据
        components_data = []
        
        # 保存分型信息
        for fx in self.fx_list:
            components_data.append({
                'type': 'FX',
                'symbol': self.symbol,
                'freq': self.freq.value,
                'dt': fx.dt,
                'mark': fx.mark.value,
                'price': fx.fx,
                'high': fx.high,
                'low': fx.low,
                'direction': str(fx.mark),
                'bar_count': len(fx.elements),
                'raw_data': str(fx.elements[0].dt) + '-' + str(fx.elements[-1].dt),
                'level': fx.gfc_level,
                'level_description': fx.level_description,
                'level_2_reasons': ';'.join(fx.level_2_reasons),
                'level_3_reasons': ';'.join(fx.level_3_reasons),
                'enhancement_summary': fx.enhancement_summary
            })
        
        # 保存笔信息
        for bi in self.bi_list:
            components_data.append({
                'type': 'BI',
                'symbol': self.symbol,
                'freq': self.freq.value,
                'dt': bi.fx_a.dt,
                'mark': f"{bi.fx_a.mark.value}-{bi.fx_b.mark.value}",
                'price': f"{bi.fx_a.fx}-{bi.fx_b.fx}",
                'high': max(bi.fx_a.fx, bi.fx_b.fx),
                'low': min(bi.fx_a.fx, bi.fx_b.fx),
                'direction': str(bi.direction),
                'bar_count': len(bi.fx_a.elements) + len(bi.fx_b.elements),
                'raw_data': f"{bi.fx_a.dt}-{bi.fx_b.dt}",
                'level': bi.gbc_level,
                'level_description': bi.level_description,
                'level_2_reasons': ';'.join(bi.level_2_reasons),
                'level_3_reasons': ';'.join(bi.level_3_reasons),
                'enhancement_summary': bi.enhancement_summary
            })
        
        # 保存FVG信息
        for fvg in self.fvg_detector.fvgs:
            components_data.append({
                'type': 'FVG',
                'symbol': self.symbol,
                'freq': self.freq.value,
                'dt': fvg.dt,
                'mark': 'Up' if fvg.is_bullish_fvg() else 'Down',
                'price': f"{fvg.low}-{fvg.high}",
                'high': fvg.high,
                'low': fvg.low,
                'direction': 'Up' if fvg.is_bullish_fvg() else 'Down',
                'bar_count': 3,  # FVG由3根K线组成
                'raw_data': f"size:{fvg.size:.2f},strength:{fvg.strength:.3f},valid:{fvg.is_valid},mitigated:{fvg.is_mitigated}"
            })
        
        # 保存OB信息
        for ob in self.ob_detector.obs:
            components_data.append({
                'type': 'OB',
                'symbol': self.symbol,
                'freq': self.freq.value,
                'dt': ob.dt,
                'mark': 'Up' if ob.is_bullish_ob() else 'Down',
                'price': f"{ob.low}-{ob.high}",
                'high': ob.high,
                'low': ob.low,
                'direction': 'Up' if ob.is_bullish_ob() else 'Down',
                'bar_count': len(ob.ob_bars),
                'raw_data': f"size:{ob.size:.2f},strength:{ob.strength:.3f},valid:{ob.is_valid},tested:{ob.is_tested},broken:{ob.is_broken}"
            })
        
        # 创建DataFrame并保存
        df = pd.DataFrame(components_data)
        df = df.sort_values('dt')
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        
        df.to_csv(file_path, index=False, encoding='utf-8')
        
        if self.verbose:
            print(f"[CZSC] 组件信息已保存到: {file_path}")
            print(f"[CZSC] 保存了 {len(components_data)} 个组件")
        
        return file_path
    
    def load_components_from_csv(self, file_path: str):
        """从CSV文件加载组件信息"""
        import pandas as pd
        
        if not os.path.exists(file_path):
            if self.verbose:
                print(f"[CZSC] 组件文件不存在: {file_path}")
            return None
        
        df = pd.read_csv(file_path)
        
        if self.verbose:
            print(f"[CZSC] 从文件加载了 {len(df)} 个组件")
            print(f"[CZSC] 分型: {len(df[df['type'] == 'FX'])} 个")
            print(f"[CZSC] 笔: {len(df[df['type'] == 'BI'])} 个")
            print(f"[CZSC] FVG: {len(df[df['type'] == 'FVG'])} 个")
            print(f"[CZSC] OB: {len(df[df['type'] == 'OB'])} 个")
        
        return df

    def to_echarts(self, width: str = "1400px", height: str = '580px', bs=[]):
        """绘制K线分析图

        :param width: 宽
        :param height: 高
        :param bs: 交易标记，默认为空
        :return:
        """
        kline = [x.__dict__ for x in self.bars_raw]
        if len(self.bi_list) > 0:
            bi = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx} for x in self.bi_list] + \
                 [{'dt': self.bi_list[-1].fx_b.dt, "bi": self.bi_list[-1].fx_b.fx}]
            fx = [{'dt': x.dt, "fx": x.fx} for x in self.fx_list]
        else:
            bi = []
            fx = []
        
        # 获取FVG数据
        fvg = self.fvg_detector.to_echarts_data()
        
        # 获取OB数据
        ob = self.ob_detector.to_echarts_data()
        
        chart = kline_pro(kline, bi=bi, fx=fx, fvg=fvg, ob=ob, width=width, height=height, bs=bs,
                          title="{}-{}".format(self.symbol, self.freq.value))
        return chart

    def to_plotly(self):
        """使用 plotly 绘制K线分析图"""
        import pandas as pd
        from czsc.utils.plotly_plot import KlineChart

        bi_list = self.bi_list
        df = pd.DataFrame(self.bars_raw)
        kline = KlineChart(n_rows=3, title="{}-{}".format(self.symbol, self.freq.value))
        kline.add_kline(df, name="")
        kline.add_sma(df, ma_seq=(5, 10, 21), row=1, visible=True, line_width=1.2)
        kline.add_sma(df, ma_seq=(34, 55, 89, 144), row=1, visible=False, line_width=1.2)
        kline.add_vol(df, row=2)
        kline.add_macd(df, row=3)

        if len(bi_list) > 0:
            bi1 = [{'dt': x.fx_a.dt, "bi": x.fx_a.fx, "text": x.fx_a.mark.value} for x in bi_list]
            bi2 = [{'dt': bi_list[-1].fx_b.dt, "bi": bi_list[-1].fx_b.fx, "text": bi_list[-1].fx_b.mark.value[0]}]
            bi = pd.DataFrame(bi1 + bi2)
            fx = pd.DataFrame([{'dt': x.dt, "fx": x.fx} for x in self.fx_list])
            kline.add_scatter_indicator(fx['dt'], fx['fx'], name="分型", row=1, line_width=2)
            kline.add_scatter_indicator(bi['dt'], bi['bi'], name="笔", text=bi['text'], row=1, line_width=2)
        return kline.fig

    def open_in_browser(self, width: str = "1400px", height: str = '580px'):
        """直接在浏览器中打开分析结果

        :param width: 图表宽度
        :param height: 图表高度
        :return:
        """
        home_path = os.path.expanduser("~")
        file_html = os.path.join(home_path, "temp_czsc.html")
        chart = self.to_echarts(width, height)
        chart.render(file_html)
        webbrowser.open(file_html)

    @property
    def last_bi_extend(self):
        """判断最后一笔是否在延伸中，True 表示延伸中"""
        if self.bi_list[-1].direction == Direction.Up \
                and max([x.high for x in self.bars_ubi]) > self.bi_list[-1].high:
            return True

        if self.bi_list[-1].direction == Direction.Down \
                and min([x.low for x in self.bars_ubi]) < self.bi_list[-1].low:
            return True

        return False

    @property
    def finished_bis(self) -> List[BI]:
        """已完成的笔"""
        if not self.bi_list:
            return []
        if len(self.bars_ubi) < 5:
            return self.bi_list[:-1]
        return self.bi_list

    @property
    def ubi_fxs(self) -> List[FX]:
        """bars_ubi 中的分型"""
        if not self.bars_ubi:
            return []
        else:
            return check_fxs(self.bars_ubi)

    @property
    def ubi(self):
        """Unfinished Bi，未完成的笔"""
        ubi_fxs = self.ubi_fxs
        if not self.bars_ubi or not self.bi_list or not ubi_fxs:
            return None

        bars_raw = [y for x in self.bars_ubi for y in x.raw_bars]
        # 获取最高点和最低点，以及对应的时间
        high_bar = max(bars_raw, key=lambda x: x.high)
        low_bar = min(bars_raw, key=lambda x: x.low)
        direction = Direction.Up if self.bi_list[-1].direction == Direction.Down else Direction.Down

        bi = {
            "symbol": self.symbol,
            "direction": direction,
            "high": high_bar.high,
            "low": low_bar.low,
            "high_bar": high_bar,
            "low_bar": low_bar,
            "bars": self.bars_ubi,
            "raw_bars": bars_raw,
            "fxs": ubi_fxs,
            "fx_a": ubi_fxs[0],
        }
        return bi

    @property
    def fx_list(self) -> List[FX]:
        """分型列表，包括 bars_ubi 中的分型"""
        fxs = []
        for bi_ in self.bi_list:
            fxs.extend(bi_.fxs[1:])
        ubi = self.ubi_fxs
        for x in ubi:
            if not fxs or x.dt > fxs[-1].dt:
                fxs.append(x)
        return fxs
    
    # 分级分型增强查询方法
    @property
    def level_2_fxs(self) -> List[FX]:
        """二级及以上分型列表"""
        return [fx for fx in self.fx_list if fx.gfc_level >= 2]
    
    @property
    def level_3_fxs(self) -> List[FX]:
        """三级及以上分型列表"""
        return [fx for fx in self.fx_list if fx.gfc_level >= 3]
    
    @property
    def level_2_bis(self) -> List[BI]:
        """二级及以上笔列表"""
        return [bi for bi in self.bi_list if bi.gbc_level >= 2]
    
    @property
    def level_3_bis(self) -> List[BI]:
        """三级及以上笔列表"""
        return [bi for bi in self.bi_list if bi.gbc_level >= 3]
    
    def get_fxs_by_level(self, level: int) -> List[FX]:
        """根据级别获取分型列表"""
        return [fx for fx in self.fx_list if fx.gfc_level == level]
    
    def get_bis_by_level(self, level: int) -> List[BI]:
        """根据级别获取笔列表"""
        return [bi for bi in self.bi_list if bi.gbc_level == level]
    
    def get_latest_high_level_fx(self, min_level: int = 2) -> FX:
        """获取最新的高级分型"""
        high_level_fxs = [fx for fx in self.fx_list if fx.gfc_level >= min_level]
        return high_level_fxs[-1] if high_level_fxs else None
    
    def get_latest_high_level_bi(self, min_level: int = 2) -> BI:
        """获取最新的高级笔"""
        high_level_bis = [bi for bi in self.bi_list if bi.gbc_level >= min_level]
        return high_level_bis[-1] if high_level_bis else None
    
    def get_level_statistics(self) -> dict:
        """获取分级分型统计信息"""
        all_fxs = self.fx_list
        all_bis = self.bi_list
        
        fx_stats = {}
        bi_stats = {}
        
        # 统计分型级别分布
        for level in range(1, 6):
            fx_count = len([fx for fx in all_fxs if fx.gfc_level == level])
            bi_count = len([bi for bi in all_bis if bi.gbc_level == level])
            fx_stats[f"level_{level}"] = fx_count
            bi_stats[f"level_{level}"] = bi_count
        
        return {
            "fx_statistics": fx_stats,
            "bi_statistics": bi_stats,
            "total_fxs": len(all_fxs),
            "total_bis": len(all_bis),
            "high_level_fxs": len([fx for fx in all_fxs if fx.gfc_level >= 2]),
            "high_level_bis": len([bi for bi in all_bis if bi.gbc_level >= 2])
        }
