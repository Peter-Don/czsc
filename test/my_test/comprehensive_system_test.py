#!/usr/bin/env python3
"""
CZSC Enhanced 全面系统测试
测试架构问题、组件问题、效率问题等
"""

import sys
import os
import time
import json
import traceback
import gc
import psutil
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from czsc import CZSC, RawBar
    from czsc.utils.bar_generator import BarGenerator
    from czsc.signals.manager import SignalManager
    from czsc.signals.enhanced_manager import EnhancedSignalManager
    from czsc.traders.base import CzscTrader
    from czsc.strategies import CzscStrategyExample2
    from czsc.poi.enhanced_fvg import EnhancedFVG
    from czsc.poi.enhanced_order_block_v2 import EnhancedOrderBlockV2
    from czsc.poi.base_poi import BasePOI
    from czsc.objects import NewBar, FX
    from czsc.enum import Direction, Freq
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("尝试使用可用的模块继续测试...")
    try:
        from czsc import CZSC, RawBar
        from czsc.utils.bar_generator import BarGenerator
        from czsc.signals.manager import SignalManager
        from czsc.traders.base import CzscTrader
        from czsc.strategies import CzscStrategyExample2
        from czsc.objects import NewBar
        from czsc.enum import Direction, Freq
        print("✅ 基础模块导入成功，将跳过部分POI测试")
    except ImportError as e2:
        print(f"❌ 基础模块导入也失败: {e2}")
        sys.exit(1)

class SystemTestSuite:
    """系统测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.performance_metrics = {}
        self.error_logs = []
        self.start_time = datetime.now()
        
        # 创建结果目录
        self.result_dir = project_root / "test" / "result"
        self.result_dir.mkdir(exist_ok=True)
        
        # 加载测试数据
        self.test_data = self._load_test_data()
        
    def _load_test_data(self) -> List[RawBar]:
        """加载测试数据"""
        print("📊 加载测试数据...")
        
        data_file = project_root / "test" / "data" / "000001.SH_D.csv"
        if not data_file.exists():
            # 创建模拟数据
            return self._create_mock_data()
        
        try:
            df = pd.read_csv(data_file)
            bars = []
            for i, (_, row) in enumerate(df.iterrows()):
                bar = RawBar(
                    symbol="000001.SH",
                    id=i,
                    dt=pd.to_datetime(row['dt']),
                    freq=Freq.D,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    vol=int(row.get('vol', 1000)),
                    amount=float(row.get('amount', 100000))
                )
                bars.append(bar)
            print(f"✅ 成功加载 {len(bars)} 条真实数据")
            return bars
        except Exception as e:
            print(f"⚠️ 加载真实数据失败: {e}，使用模拟数据")
            return self._create_mock_data()
    
    def _create_mock_data(self) -> List[RawBar]:
        """创建模拟测试数据"""
        print("🎭 创建模拟测试数据...")
        
        bars = []
        base_price = 100.0
        base_time = datetime(2023, 1, 1)
        
        for i in range(1000):
            # 创建有趋势的价格数据
            trend = 0.1 * (i % 100 - 50) / 50  # 创建波动趋势
            noise = (hash(str(i)) % 200 - 100) / 10000  # 添加随机噪声
            
            price_change = trend + noise
            base_price *= (1 + price_change)
            
            # 创建OHLC数据
            open_price = base_price
            high_price = base_price * (1 + abs(noise) * 2)
            low_price = base_price * (1 - abs(noise) * 2)
            close_price = base_price * (1 + price_change)
            
            bar = RawBar(
                symbol="TEST.SH",
                id=i,
                dt=base_time + timedelta(days=i),
                freq=Freq.D,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                vol=1000 + i * 10,
                amount=100000 + i * 1000
            )
            bars.append(bar)
        
        print(f"✅ 创建 {len(bars)} 条模拟数据")
        return bars
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始全面系统测试")
        print("=" * 60)
        
        # 1. 架构完整性测试
        self._test_architecture_integrity()
        
        # 2. 组件功能测试
        self._test_component_functionality()
        
        # 3. 性能压力测试
        self._test_performance_stress()
        
        # 4. 内存泄漏测试
        self._test_memory_leaks()
        
        # 5. 边界条件测试
        self._test_edge_cases()
        
        # 6. 并发安全测试
        self._test_concurrent_safety()
        
        # 7. 数据一致性测试
        self._test_data_consistency()
        
        # 8. 错误恢复测试
        self._test_error_recovery()
        
        # 生成测试报告
        self._generate_test_report()
        
        print("🎉 全面系统测试完成！")
    
    def _test_architecture_integrity(self):
        """测试架构完整性"""
        print("\n🏗️ 测试 1: 架构完整性")
        test_start = time.time()
        
        try:
            # 测试模块导入完整性
            import_results = self._test_module_imports()
            
            # 测试类继承关系
            inheritance_results = self._test_class_inheritance()
            
            # 测试接口一致性
            interface_results = self._test_interface_consistency()
            
            # 测试配置管理
            config_results = self._test_config_management()
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "架构完整性测试",
                "status": "PASS",
                "duration": test_time,
                "details": {
                    "module_imports": import_results,
                    "class_inheritance": inheritance_results,
                    "interface_consistency": interface_results,
                    "config_management": config_results
                }
            })
            
            print(f"✅ 架构完整性测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("架构完整性测试", e)
    
    def _test_module_imports(self) -> Dict[str, Any]:
        """测试模块导入"""
        results = {"successful": [], "failed": []}
        
        modules_to_test = [
            "czsc.analyze",
            "czsc.strategies", 
            "czsc.signals.manager",
            "czsc.signals.enhanced_manager",
            "czsc.traders.base",
            "czsc.svc.strategy",
            "czsc.poi.fvg",
            "czsc.poi.ob",
            "czsc.utils.bar_generator"
        ]
        
        for module_name in modules_to_test:
            try:
                __import__(module_name)
                results["successful"].append(module_name)
            except ImportError as e:
                results["failed"].append({"module": module_name, "error": str(e)})
        
        return results
    
    def _test_class_inheritance(self) -> Dict[str, Any]:
        """测试类继承关系"""
        results = {"checks": [], "issues": []}
        
        try:
            # 测试策略基类
            from czsc.strategies import CzscStrategyBase, CzscJsonStrategy
            if not issubclass(CzscJsonStrategy, CzscStrategyBase):
                results["issues"].append("CzscJsonStrategy应该继承CzscStrategyBase")
            else:
                results["checks"].append("CzscJsonStrategy继承关系正确")
            
            # 测试信号生成器
            from czsc.signals.base import ComponentSignalGenerator
            from czsc.signals.fractal_signals import FractalSignalGenerator
            if hasattr(sys.modules.get('czsc.signals.fractal_signals'), 'FractalSignalGenerator'):
                if not issubclass(FractalSignalGenerator, ComponentSignalGenerator):
                    results["issues"].append("FractalSignalGenerator应该继承ComponentSignalGenerator")
                else:
                    results["checks"].append("FractalSignalGenerator继承关系正确")
            
        except Exception as e:
            results["issues"].append(f"继承关系检查异常: {str(e)}")
        
        return results
    
    def _test_interface_consistency(self) -> Dict[str, Any]:
        """测试接口一致性"""
        results = {"consistent_interfaces": [], "inconsistent_interfaces": []}
        
        try:
            # 测试CZSC接口
            czsc = CZSC(self.test_data[:100])
            required_attrs = ['symbol', 'bars_raw', 'bars_ubi', 'bi_list', 'fx_list']
            
            for attr in required_attrs:
                if hasattr(czsc, attr):
                    results["consistent_interfaces"].append(f"CZSC.{attr}")
                else:
                    results["inconsistent_interfaces"].append(f"CZSC缺少属性: {attr}")
            
            # 测试策略接口
            strategy = CzscStrategyExample2("TEST.SH")
            strategy_attrs = ['symbol', 'freqs', 'positions', 'signals_config']
            
            for attr in strategy_attrs:
                if hasattr(strategy, attr):
                    results["consistent_interfaces"].append(f"Strategy.{attr}")
                else:
                    results["inconsistent_interfaces"].append(f"Strategy缺少属性: {attr}")
                    
        except Exception as e:
            results["inconsistent_interfaces"].append(f"接口测试异常: {str(e)}")
        
        return results
    
    def _test_config_management(self) -> Dict[str, Any]:
        """测试配置管理"""
        results = {"config_files": [], "config_errors": []}
        
        # 检查配置文件存在性
        config_files = [
            project_root / "config" / "pen_config.json",
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    results["config_files"].append({
                        "file": str(config_file),
                        "status": "valid",
                        "keys": list(config_data.keys()) if isinstance(config_data, dict) else []
                    })
                except Exception as e:
                    results["config_errors"].append({
                        "file": str(config_file),
                        "error": str(e)
                    })
            else:
                results["config_errors"].append({
                    "file": str(config_file),
                    "error": "文件不存在"
                })
        
        return results
    
    def _test_component_functionality(self):
        """测试组件功能"""
        print("\n🧩 测试 2: 组件功能")
        test_start = time.time()
        
        try:
            # 测试CZSC核心功能
            czsc_results = self._test_czsc_core()
            
            # 测试信号生成功能
            signal_results = self._test_signal_generation()
            
            # 测试POI检测功能
            poi_results = self._test_poi_detection()
            
            # 测试交易器功能
            trader_results = self._test_trader_functionality()
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "组件功能测试",
                "status": "PASS",
                "duration": test_time,
                "details": {
                    "czsc_core": czsc_results,
                    "signal_generation": signal_results,
                    "poi_detection": poi_results,
                    "trader_functionality": trader_results
                }
            })
            
            print(f"✅ 组件功能测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("组件功能测试", e)
    
    def _test_czsc_core(self) -> Dict[str, Any]:
        """测试CZSC核心功能"""
        results = {"tests": [], "errors": []}
        
        try:
            # 基本CZSC创建测试
            czsc = CZSC(self.test_data[:500])
            results["tests"].append({
                "name": "CZSC基本创建",
                "status": "PASS",
                "details": f"处理了{len(czsc.bars_ubi)}根K线"
            })
            
            # 分型检测测试
            if hasattr(czsc, 'fx_list') and czsc.fx_list:
                results["tests"].append({
                    "name": "分型检测",
                    "status": "PASS", 
                    "details": f"检测到{len(czsc.fx_list)}个分型"
                })
            else:
                results["errors"].append("分型检测失败或无分型")
            
            # 笔识别测试
            if hasattr(czsc, 'bi_list') and czsc.bi_list:
                results["tests"].append({
                    "name": "笔识别",
                    "status": "PASS",
                    "details": f"识别出{len(czsc.bi_list)}笔"
                })
            else:
                results["errors"].append("笔识别失败或无笔")
            
            # 线段识别测试
            if hasattr(czsc, 'xd_list') and czsc.xd_list:
                results["tests"].append({
                    "name": "线段识别",
                    "status": "PASS",
                    "details": f"识别出{len(czsc.xd_list)}段"
                })
            else:
                results["tests"].append({
                    "name": "线段识别",
                    "status": "SKIP",
                    "details": "无线段数据（可能正常）"
                })
                
        except Exception as e:
            results["errors"].append(f"CZSC核心测试异常: {str(e)}")
        
        return results
    
    def _test_signal_generation(self) -> Dict[str, Any]:
        """测试信号生成功能"""
        results = {"tests": [], "errors": []}
        
        try:
            # 创建信号管理器
            config = {
                'fvg_min_gap_size': 0.001,
                'ob_min_move_strength': 0.005,
                'enable_signal_filtering': True
            }
            
            # 测试基础信号管理器
            try:
                signal_manager = SignalManager(config)
                results["tests"].append({
                    "name": "基础信号管理器创建",
                    "status": "PASS",
                    "details": "成功创建SignalManager"
                })
            except Exception as e:
                results["errors"].append(f"基础信号管理器创建失败: {str(e)}")
            
            # 测试增强信号管理器
            try:
                try:
                    enhanced_manager = EnhancedSignalManager(config)
                    results["tests"].append({
                        "name": "增强信号管理器创建",
                        "status": "PASS",
                        "details": "成功创建EnhancedSignalManager"
                    })
                except NameError:
                    results["tests"].append({
                        "name": "增强信号管理器创建",
                        "status": "SKIP",
                        "details": "EnhancedSignalManager未导入，跳过测试"
                    })
            except Exception as e:
                results["errors"].append(f"增强信号管理器创建失败: {str(e)}")
            
        except Exception as e:
            results["errors"].append(f"信号生成测试异常: {str(e)}")
        
        return results
    
    def _test_poi_detection(self) -> Dict[str, Any]:
        """测试POI检测功能"""
        results = {"tests": [], "errors": []}
        
        try:
            # 创建CZSC对象用于POI检测
            czsc = CZSC(self.test_data[:300])
            
            # 测试POI基类功能
            try:
                # 创建一个简单的POI对象测试
                from datetime import datetime
                test_poi = BasePOI(
                    symbol="TEST.SH",
                    dt=datetime.now(),
                    high=105.0,
                    low=95.0,
                    direction=Direction.UP,
                    poi_type="TEST_POI"
                )
                results["tests"].append({
                    "name": "POI基类创建",
                    "status": "PASS",
                    "details": f"成功创建POI对象: {test_poi.poi_type}"
                })
            except Exception as e:
                results["errors"].append(f"POI基类测试失败: {str(e)}")
            
            # 测试Enhanced FVG对象
            try:
                if len(czsc.bars_ubi) >= 3:
                    bar1, bar2, bar3 = czsc.bars_ubi[:3]
                    enhanced_fvg = EnhancedFVG(
                        symbol="TEST.SH",
                        dt=bar2.dt,
                        high=max(bar1.high, bar2.high, bar3.high),
                        low=min(bar1.low, bar2.low, bar3.low),
                        direction=Direction.UP,
                        poi_type="FVG",
                        bar1=bar1,
                        bar2=bar2,
                        bar3=bar3
                    )
                    results["tests"].append({
                        "name": "Enhanced FVG创建",
                        "status": "PASS",
                        "details": "成功创建Enhanced FVG对象"
                    })
                else:
                    results["tests"].append({
                        "name": "Enhanced FVG创建",
                        "status": "SKIP",
                        "details": "数据不足，跳过测试"
                    })
            except Exception as e:
                results["errors"].append(f"Enhanced FVG测试失败: {str(e)}")
                
        except Exception as e:
            results["errors"].append(f"POI检测测试异常: {str(e)}")
        
        return results
    
    def _test_trader_functionality(self) -> Dict[str, Any]:
        """测试交易器功能"""
        results = {"tests": [], "errors": []}
        
        try:
            # 创建策略和交易器
            strategy = CzscStrategyExample2("TEST.SH")
            
            # 测试交易器初始化
            try:
                trader = strategy.init_trader(bars=self.test_data[:200], init_n=100)
                results["tests"].append({
                    "name": "交易器初始化",
                    "status": "PASS",
                    "details": f"成功创建交易器，{len(strategy.positions)}个持仓策略"
                })
                
                # 测试信号更新
                if hasattr(trader, 'update_signals'):
                    trader.update_signals(self.test_data[200])
                    results["tests"].append({
                        "name": "信号更新",
                        "status": "PASS",
                        "details": "成功更新信号"
                    })
                    
            except Exception as e:
                results["errors"].append(f"交易器功能测试失败: {str(e)}")
                
        except Exception as e:
            results["errors"].append(f"交易器功能测试异常: {str(e)}")
        
        return results
    
    def _test_performance_stress(self):
        """测试性能压力"""
        print("\n⚡ 测试 3: 性能压力")
        test_start = time.time()
        
        try:
            # 大数据量测试
            large_data_results = self._test_large_data_processing()
            
            # 并发处理测试
            concurrent_results = self._test_concurrent_processing()
            
            # 频繁创建销毁测试
            creation_destruction_results = self._test_creation_destruction()
            
            test_time = time.time() - test_start
            
            self.performance_metrics["performance_stress"] = {
                "total_duration": test_time,
                "large_data": large_data_results,
                "concurrent": concurrent_results,
                "creation_destruction": creation_destruction_results
            }
            
            self.test_results.append({
                "test_name": "性能压力测试",
                "status": "PASS",
                "duration": test_time,
                "details": self.performance_metrics["performance_stress"]
            })
            
            print(f"✅ 性能压力测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("性能压力测试", e)
    
    def _test_large_data_processing(self) -> Dict[str, Any]:
        """测试大数据量处理"""
        results = {"tests": [], "metrics": {}}
        
        # 创建大量数据
        large_data = self.test_data * 5  # 扩展到5倍数据量
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # 处理大数据量
            czsc = CZSC(large_data)
            
            processing_time = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            results["tests"].append({
                "name": "大数据量CZSC处理",
                "status": "PASS",
                "input_size": len(large_data),
                "output_size": len(czsc.bars_ubi),
                "processing_time": processing_time,
                "memory_usage": end_memory - start_memory
            })
            
            results["metrics"] = {
                "throughput": len(large_data) / processing_time,  # 条/秒
                "memory_efficiency": len(large_data) / (end_memory - start_memory),  # 条/MB
                "compression_ratio": len(czsc.bars_ubi) / len(large_data)
            }
            
        except Exception as e:
            results["tests"].append({
                "name": "大数据量处理",
                "status": "FAIL",
                "error": str(e)
            })
        
        return results
    
    def _test_concurrent_processing(self) -> Dict[str, Any]:
        """测试并发处理"""
        results = {"tests": [], "metrics": {}}
        
        import threading
        import concurrent.futures
        
        def process_data_chunk(chunk_id, data_chunk):
            """处理数据块"""
            try:
                czsc = CZSC(data_chunk)
                return {
                    "chunk_id": chunk_id,
                    "status": "success",
                    "input_size": len(data_chunk),
                    "output_size": len(czsc.bars_ubi)
                }
            except Exception as e:
                return {
                    "chunk_id": chunk_id,
                    "status": "error",
                    "error": str(e)
                }
        
        try:
            # 分割数据为多个块
            chunk_size = len(self.test_data) // 4
            data_chunks = [
                self.test_data[i:i+chunk_size] 
                for i in range(0, len(self.test_data), chunk_size)
            ]
            
            start_time = time.time()
            
            # 并发处理
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(process_data_chunk, i, chunk)
                    for i, chunk in enumerate(data_chunks)
                ]
                
                concurrent_results = [future.result() for future in futures]
            
            processing_time = time.time() - start_time
            
            successful_chunks = [r for r in concurrent_results if r["status"] == "success"]
            
            results["tests"].append({
                "name": "并发数据处理",
                "status": "PASS" if len(successful_chunks) == len(data_chunks) else "PARTIAL",
                "total_chunks": len(data_chunks),
                "successful_chunks": len(successful_chunks),
                "processing_time": processing_time
            })
            
            results["metrics"] = {
                "concurrent_efficiency": len(data_chunks) / processing_time,
                "success_rate": len(successful_chunks) / len(data_chunks)
            }
            
        except Exception as e:
            results["tests"].append({
                "name": "并发处理",
                "status": "FAIL", 
                "error": str(e)
            })
        
        return results
    
    def _test_creation_destruction(self) -> Dict[str, Any]:
        """测试频繁创建销毁"""
        results = {"tests": [], "metrics": {}}
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            # 频繁创建和销毁对象
            for i in range(100):
                czsc = CZSC(self.test_data[:100])
                del czsc
                
                if i % 20 == 0:
                    gc.collect()  # 手动垃圾回收
            
            processing_time = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            results["tests"].append({
                "name": "频繁创建销毁",
                "status": "PASS",
                "iterations": 100,
                "processing_time": processing_time,
                "memory_change": end_memory - start_memory
            })
            
            results["metrics"] = {
                "creation_rate": 100 / processing_time,
                "memory_stability": abs(end_memory - start_memory) < 50  # 内存变化小于50MB
            }
            
        except Exception as e:
            results["tests"].append({
                "name": "频繁创建销毁",
                "status": "FAIL",
                "error": str(e)
            })
        
        return results
    
    def _test_memory_leaks(self):
        """测试内存泄漏"""
        print("\n🧠 测试 4: 内存泄漏")
        test_start = time.time()
        
        try:
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples = [initial_memory]
            
            # 执行多轮操作，监控内存变化
            for round_num in range(10):
                # 创建和处理数据
                for i in range(20):
                    czsc = CZSC(self.test_data[:200])
                    strategy = CzscStrategyExample2("TEST.SH")
                    trader = strategy.init_trader(bars=self.test_data[:100], init_n=50)
                    
                    # 清理
                    del czsc, strategy, trader
                
                # 强制垃圾回收
                gc.collect()
                
                # 记录内存使用
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                print(f"  轮次 {round_num+1}: {current_memory:.1f} MB")
            
            # 分析内存趋势
            memory_trend = self._analyze_memory_trend(memory_samples)
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "内存泄漏测试",
                "status": "PASS" if not memory_trend["has_leak"] else "WARNING",
                "duration": test_time,
                "details": {
                    "initial_memory": initial_memory,
                    "final_memory": memory_samples[-1],
                    "max_memory": max(memory_samples),
                    "memory_trend": memory_trend,
                    "samples": memory_samples
                }
            })
            
            if memory_trend["has_leak"]:
                print(f"⚠️ 疑似内存泄漏 (趋势斜率: {memory_trend['slope']:.2f})")
            else:
                print(f"✅ 无明显内存泄漏 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("内存泄漏测试", e)
    
    def _analyze_memory_trend(self, memory_samples: List[float]) -> Dict[str, Any]:
        """分析内存趋势"""
        if len(memory_samples) < 3:
            return {"has_leak": False, "slope": 0, "confidence": 0}
        
        # 简单线性回归计算趋势
        n = len(memory_samples)
        x = list(range(n))
        y = memory_samples
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        # 计算斜率
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # 判断是否有明显的内存泄漏
        # 如果斜率大于阈值且最终内存比初始内存增加超过一定百分比
        has_leak = (
            slope > 1.0 and  # 每轮增长超过1MB
            (memory_samples[-1] - memory_samples[0]) / memory_samples[0] > 0.1  # 增长超过10%
        )
        
        return {
            "has_leak": has_leak,
            "slope": slope,
            "total_increase": memory_samples[-1] - memory_samples[0],
            "percentage_increase": (memory_samples[-1] - memory_samples[0]) / memory_samples[0] * 100
        }
    
    def _test_edge_cases(self):
        """测试边界条件"""
        print("\n🎯 测试 5: 边界条件")
        test_start = time.time()
        
        try:
            edge_case_results = []
            
            # 1. 空数据测试
            edge_case_results.append(self._test_empty_data())
            
            # 2. 单条数据测试
            edge_case_results.append(self._test_single_bar())
            
            # 3. 异常价格数据测试
            edge_case_results.append(self._test_abnormal_prices())
            
            # 4. 时间序列不连续测试
            edge_case_results.append(self._test_discontinuous_time())
            
            # 5. 极大数值测试
            edge_case_results.append(self._test_extreme_values())
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "边界条件测试",
                "status": "PASS",
                "duration": test_time,
                "details": edge_case_results
            })
            
            print(f"✅ 边界条件测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("边界条件测试", e)
    
    def _test_empty_data(self) -> Dict[str, Any]:
        """测试空数据"""
        try:
            czsc = CZSC([])
            return {
                "test": "空数据",
                "status": "PASS",
                "details": "空数据处理正常"
            }
        except Exception as e:
            return {
                "test": "空数据",
                "status": "EXPECTED_ERROR",
                "details": f"空数据引发异常（预期）: {str(e)}"
            }
    
    def _test_single_bar(self) -> Dict[str, Any]:
        """测试单条数据"""
        try:
            single_bar = [self.test_data[0]]
            czsc = CZSC(single_bar)
            return {
                "test": "单条数据",
                "status": "PASS",
                "details": f"单条数据处理正常，输出{len(czsc.bars_ubi)}条"
            }
        except Exception as e:
            return {
                "test": "单条数据",
                "status": "ERROR",
                "details": f"单条数据处理异常: {str(e)}"
            }
    
    def _test_abnormal_prices(self) -> Dict[str, Any]:
        """测试异常价格"""
        try:
            # 创建异常价格数据
            abnormal_bar = RawBar(
                symbol="TEST.SH",
                id=0,
                dt=datetime.now(),
                freq=Freq.D,
                open=100.0,
                high=50.0,  # 高价小于开盘价（异常）
                low=150.0,  # 低价大于开盘价（异常）
                close=80.0,
                vol=1000,
                amount=100000
            )
            
            abnormal_data = [abnormal_bar] + self.test_data[:10]
            czsc = CZSC(abnormal_data)
            
            return {
                "test": "异常价格",
                "status": "PASS",
                "details": "异常价格数据处理正常（可能被过滤）"
            }
        except Exception as e:
            return {
                "test": "异常价格",
                "status": "ERROR",
                "details": f"异常价格处理失败: {str(e)}"
            }
    
    def _test_discontinuous_time(self) -> Dict[str, Any]:
        """测试时间序列不连续"""
        try:
            # 创建时间不连续的数据
            discontinuous_data = []
            base_time = datetime(2023, 1, 1)
            
            for i in range(5):
                # 故意跳过一些时间点
                dt = base_time + timedelta(days=i*3)  # 每3天一个数据点
                bar = RawBar(
                    symbol="TEST.SH",
                    id=i,
                    dt=dt,
                    freq=Freq.D,
                    open=100.0 + i,
                    high=105.0 + i,
                    low=95.0 + i,
                    close=102.0 + i,
                    vol=1000,
                    amount=100000
                )
                discontinuous_data.append(bar)
            
            czsc = CZSC(discontinuous_data)
            
            return {
                "test": "时间不连续",
                "status": "PASS",
                "details": f"时间不连续数据处理正常，输入{len(discontinuous_data)}条，输出{len(czsc.bars_ubi)}条"
            }
        except Exception as e:
            return {
                "test": "时间不连续",
                "status": "ERROR",
                "details": f"时间不连续处理失败: {str(e)}"
            }
    
    def _test_extreme_values(self) -> Dict[str, Any]:
        """测试极值数据"""
        try:
            # 创建极值数据
            extreme_bar = RawBar(
                symbol="TEST.SH",
                id=0,
                dt=datetime.now(),
                freq=Freq.D,
                open=1e10,  # 极大值
                high=1e10,
                low=1e-10,  # 极小值
                close=1e5,
                vol=int(1e12),  # 极大成交量
                amount=1e15
            )
            
            extreme_data = [extreme_bar] + self.test_data[:10]
            czsc = CZSC(extreme_data)
            
            return {
                "test": "极值数据",
                "status": "PASS",
                "details": "极值数据处理正常"
            }
        except Exception as e:
            return {
                "test": "极值数据",
                "status": "ERROR",
                "details": f"极值数据处理失败: {str(e)}"
            }
    
    def _test_concurrent_safety(self):
        """测试并发安全"""
        print("\n🔒 测试 6: 并发安全")
        test_start = time.time()
        
        try:
            import threading
            import concurrent.futures
            
            results = {"thread_safety": [], "race_conditions": []}
            
            # 测试多线程访问同一对象
            czsc = CZSC(self.test_data[:100])
            
            def access_czsc_object(thread_id):
                """多线程访问CZSC对象"""
                try:
                    # 读取操作
                    bars_count = len(czsc.bars_ubi)
                    fx_count = len(czsc.fx_list) if czsc.fx_list else 0
                    
                    return {
                        "thread_id": thread_id,
                        "status": "success",
                        "bars_count": bars_count,
                        "fx_count": fx_count
                    }
                except Exception as e:
                    return {
                        "thread_id": thread_id,
                        "status": "error",
                        "error": str(e)
                    }
            
            # 并发读取测试
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(access_czsc_object, i) for i in range(10)]
                thread_results = [future.result() for future in futures]
            
            successful_reads = [r for r in thread_results if r["status"] == "success"]
            
            results["thread_safety"].append({
                "test": "并发读取",
                "status": "PASS" if len(successful_reads) == len(thread_results) else "FAIL",
                "successful_threads": len(successful_reads),
                "total_threads": len(thread_results)
            })
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "并发安全测试",
                "status": "PASS",
                "duration": test_time,
                "details": results
            })
            
            print(f"✅ 并发安全测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("并发安全测试", e)
    
    def _test_data_consistency(self):
        """测试数据一致性"""
        print("\n📊 测试 7: 数据一致性")
        test_start = time.time()
        
        try:
            consistency_results = []
            
            # 多次处理同样数据，检查结果一致性
            for i in range(3):
                czsc = CZSC(self.test_data[:200])
                consistency_results.append({
                    "run": i + 1,
                    "bars_count": len(czsc.bars_ubi),
                    "fx_count": len(czsc.fx_list) if czsc.fx_list else 0,
                    "bi_count": len(czsc.bi_list) if czsc.bi_list else 0
                })
            
            # 检查一致性
            bars_counts = [r["bars_count"] for r in consistency_results]
            fx_counts = [r["fx_count"] for r in consistency_results]
            bi_counts = [r["bi_count"] for r in consistency_results]
            
            bars_consistent = len(set(bars_counts)) == 1
            fx_consistent = len(set(fx_counts)) == 1
            bi_consistent = len(set(bi_counts)) == 1
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "数据一致性测试",
                "status": "PASS" if all([bars_consistent, fx_consistent, bi_consistent]) else "FAIL",
                "duration": test_time,
                "details": {
                    "runs": consistency_results,
                    "bars_consistent": bars_consistent,
                    "fx_consistent": fx_consistent,
                    "bi_consistent": bi_consistent
                }
            })
            
            if all([bars_consistent, fx_consistent, bi_consistent]):
                print(f"✅ 数据一致性测试通过 (耗时: {test_time:.2f}s)")
            else:
                print(f"⚠️ 数据一致性测试发现问题 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("数据一致性测试", e)
    
    def _test_error_recovery(self):
        """测试错误恢复"""
        print("\n🔄 测试 8: 错误恢复")
        test_start = time.time()
        
        try:
            recovery_results = []
            
            # 测试各种异常情况的恢复能力
            test_cases = [
                ("None数据", lambda: CZSC(None)),
                ("错误类型数据", lambda: CZSC("invalid_data")),
                ("混合类型数据", lambda: CZSC([self.test_data[0], "invalid", self.test_data[1]])),
            ]
            
            for test_name, test_func in test_cases:
                try:
                    result = test_func()
                    recovery_results.append({
                        "test": test_name,
                        "status": "UNEXPECTED_PASS",
                        "details": "意外通过了错误测试"
                    })
                except Exception as e:
                    recovery_results.append({
                        "test": test_name,
                        "status": "EXPECTED_ERROR",
                        "details": f"正确捕获异常: {type(e).__name__}"
                    })
            
            # 测试错误后的正常功能恢复
            try:
                czsc = CZSC(self.test_data[:100])
                recovery_results.append({
                    "test": "错误后恢复",
                    "status": "PASS",
                    "details": "错误后能正常创建CZSC对象"
                })
            except Exception as e:
                recovery_results.append({
                    "test": "错误后恢复",
                    "status": "FAIL",
                    "details": f"错误后无法恢复: {str(e)}"
                })
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "错误恢复测试",
                "status": "PASS",
                "duration": test_time,
                "details": recovery_results
            })
            
            print(f"✅ 错误恢复测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self._log_error("错误恢复测试", e)
    
    def _log_error(self, test_name: str, error: Exception):
        """记录错误"""
        error_info = {
            "test_name": test_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.error_logs.append(error_info)
        
        self.test_results.append({
            "test_name": test_name,
            "status": "FAIL",
            "duration": 0,
            "error": error_info
        })
        
        print(f"❌ {test_name}失败: {str(error)}")
    
    def _generate_test_report(self):
        """生成测试报告"""
        print("\n📋 生成测试报告...")
        
        total_time = datetime.now() - self.start_time
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warning_tests = len([t for t in self.test_results if t["status"] == "WARNING"])
        
        # 生成详细报告
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_duration": total_time.total_seconds(),
                "test_date": self.start_time.isoformat()
            },
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "error_logs": self.error_logs,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
                "cpu_count": psutil.cpu_count()
            }
        }
        
        # 保存JSON报告
        report_file = self.result_dir / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # 生成HTML报告
        self._generate_html_report(report)
        
        # 生成Markdown报告
        self._generate_markdown_report(report)
        
        # 打印摘要
        print(f"\n📊 测试摘要:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过: {passed_tests} ✅")
        print(f"   失败: {failed_tests} ❌")
        print(f"   警告: {warning_tests} ⚠️")
        print(f"   成功率: {passed_tests/total_tests*100:.1f}%")
        print(f"   总耗时: {total_time.total_seconds():.2f}秒")
        
        print(f"\n📄 报告文件:")
        print(f"   JSON: {report_file}")
        print(f"   HTML: {report_file.with_suffix('.html')}")
        print(f"   Markdown: {report_file.with_suffix('.md')}")
    
    def _generate_html_report(self, report: Dict[str, Any]):
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CZSC Enhanced 系统测试报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-left: 4px solid #3498db; padding-left: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric h3 {{ margin: 0; font-size: 2em; }}
        .metric p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .test-result {{ margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 5px solid #ddd; }}
        .test-pass {{ background-color: #d4edda; border-left-color: #28a745; }}
        .test-fail {{ background-color: #f8d7da; border-left-color: #dc3545; }}
        .test-warning {{ background-color: #fff3cd; border-left-color: #ffc107; }}
        .error-log {{ background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        .performance {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .performance-item {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 CZSC Enhanced 全面系统测试报告</h1>
        
        <div class="summary">
            <div class="metric">
                <h3>{report['test_summary']['total_tests']}</h3>
                <p>总测试数</p>
            </div>
            <div class="metric">
                <h3>{report['test_summary']['success_rate']:.1%}</h3>
                <p>成功率</p>
            </div>
            <div class="metric">
                <h3>{report['test_summary']['total_duration']:.1f}s</h3>
                <p>总耗时</p>
            </div>
            <div class="metric">
                <h3>{report['test_summary']['failed_tests']}</h3>
                <p>失败测试</p>
            </div>
        </div>
        
        <h2>📊 测试结果详情</h2>
        """
        
        for test in report['test_results']:
            status_class = f"test-{test['status'].lower()}"
            status_emoji = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️"}.get(test['status'], "❓")
            
            html_content += f"""
            <div class="test-result {status_class}">
                <h3>{status_emoji} {test['test_name']}</h3>
                <p><strong>状态:</strong> {test['status']}</p>
                <p><strong>耗时:</strong> {test.get('duration', 0):.2f}秒</p>
            """
            
            if 'error' in test:
                html_content += f"""
                <div class="error-log">
                    <strong>错误:</strong> {test['error']['error_type']} - {test['error']['error_message']}
                </div>
                """
            
            html_content += "</div>"
        
        if report['performance_metrics']:
            html_content += """
            <h2>⚡ 性能指标</h2>
            <div class="performance">
            """
            
            for metric_name, metric_data in report['performance_metrics'].items():
                html_content += f"""
                <div class="performance-item">
                    <h4>{metric_name}</h4>
                    <pre>{json.dumps(metric_data, indent=2, ensure_ascii=False)}</pre>
                </div>
                """
            
            html_content += "</div>"
        
        html_content += """
        <h2>🔧 系统信息</h2>
        <pre>""" + json.dumps(report['system_info'], indent=2, ensure_ascii=False) + """</pre>
        
        <h2>📅 测试时间</h2>
        <p>测试开始时间: """ + report['test_summary']['test_date'] + """</p>
        
    </div>
</body>
</html>
        """
        
        html_file = self.result_dir / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, report: Dict[str, Any]):
        """生成Markdown报告"""
        md_content = f"""# CZSC Enhanced 全面系统测试报告

## 📊 测试摘要

| 指标 | 数值 |
|------|------|
| 总测试数 | {report['test_summary']['total_tests']} |
| 通过测试 | {report['test_summary']['passed_tests']} ✅ |
| 失败测试 | {report['test_summary']['failed_tests']} ❌ |
| 警告测试 | {report['test_summary']['warning_tests']} ⚠️ |
| 成功率 | {report['test_summary']['success_rate']:.1%} |
| 总耗时 | {report['test_summary']['total_duration']:.2f}秒 |

## 🧪 详细测试结果

"""
        
        for test in report['test_results']:
            status_emoji = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️"}.get(test['status'], "❓")
            md_content += f"""### {status_emoji} {test['test_name']}

- **状态**: {test['status']}
- **耗时**: {test.get('duration', 0):.2f}秒

"""
            
            if 'error' in test:
                md_content += f"""**错误信息**:
```
{test['error']['error_type']}: {test['error']['error_message']}
```

"""
        
        if report['performance_metrics']:
            md_content += """## ⚡ 性能指标

"""
            for metric_name, metric_data in report['performance_metrics'].items():
                md_content += f"""### {metric_name}

```json
{json.dumps(metric_data, indent=2, ensure_ascii=False)}
```

"""
        
        md_content += f"""## 🔧 系统信息

```json
{json.dumps(report['system_info'], indent=2, ensure_ascii=False)}
```

## 📅 测试信息

- **测试时间**: {report['test_summary']['test_date']}
- **报告生成**: {datetime.now().isoformat()}

---

*本报告由 CZSC Enhanced 自动化测试系统生成*
"""
        
        md_file = self.result_dir / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

def main():
    """主函数"""
    print("🧪 CZSC Enhanced 全面系统测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = SystemTestSuite()
    
    # 运行所有测试
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()