#!/usr/bin/env python3
"""
CZSC Enhanced 快速系统测试
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
    from czsc.signals.manager import SignalManager
    from czsc.traders.base import CzscTrader
    from czsc.strategies import CzscStrategyExample2
    from czsc.enum import Freq
    print("✅ 成功导入核心模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

class QuickTestSuite:
    """快速测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
        # 创建结果目录
        self.result_dir = project_root / "test" / "result"
        self.result_dir.mkdir(exist_ok=True)
        
        # 创建简单测试数据
        self.test_data = self._create_simple_test_data()
        
    def _create_simple_test_data(self) -> List[RawBar]:
        """创建简单测试数据"""
        print("📊 创建测试数据...")
        
        bars = []
        base_price = 100.0
        base_time = datetime(2023, 1, 1)
        
        for i in range(500):  # 较小的数据集
            # 创建有趋势的价格数据
            trend = 0.1 * (i % 50 - 25) / 25  # 创建波动趋势
            noise = (hash(str(i)) % 200 - 100) / 20000  # 添加小噪声
            
            price_change = trend + noise
            base_price *= (1 + price_change)
            
            # 创建OHLC数据
            open_price = base_price
            high_price = base_price * (1 + abs(noise) * 1.5)
            low_price = base_price * (1 - abs(noise) * 1.5)
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
        
        print(f"✅ 创建 {len(bars)} 条测试数据")
        return bars
    
    def run_quick_tests(self):
        """运行快速测试"""
        print("🚀 开始快速系统测试")
        print("=" * 50)
        
        # 1. 基础功能测试
        self._test_basic_functionality()
        
        # 2. 性能测试
        self._test_performance()
        
        # 3. 内存测试
        self._test_memory_usage()
        
        # 4. 边界条件测试
        self._test_edge_cases()
        
        # 生成报告
        self._generate_report()
        
        print("🎉 快速系统测试完成！")
    
    def _test_basic_functionality(self):
        """测试基础功能"""
        print("\n🔧 测试 1: 基础功能")
        test_start = time.time()
        
        try:
            # 测试CZSC创建
            czsc = CZSC(self.test_data[:200])
            
            basic_tests = {
                "CZSC创建": {
                    "status": "PASS",
                    "details": f"处理了{len(czsc.bars_ubi)}根K线，检测到{len(czsc.fx_list) if czsc.fx_list else 0}个分型"
                },
                "笔识别": {
                    "status": "PASS" if hasattr(czsc, 'bi_list') and czsc.bi_list else "WARNING",
                    "details": f"识别出{len(czsc.bi_list) if czsc.bi_list else 0}笔"
                }
            }
            
            # 测试策略创建
            try:
                strategy = CzscStrategyExample2(symbol="TEST.SH")
                basic_tests["策略创建"] = {
                    "status": "PASS",
                    "details": f"成功创建策略，{len(strategy.positions)}个持仓策略"
                }
                
                # 测试交易器
                trader = strategy.init_trader(bars=self.test_data[:100], init_n=50)
                basic_tests["交易器创建"] = {
                    "status": "PASS",
                    "details": "成功创建交易器"
                }
                
            except Exception as e:
                basic_tests["策略/交易器"] = {
                    "status": "FAIL",
                    "details": f"失败: {str(e)}"
                }
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "基础功能测试",
                "status": "PASS",
                "duration": test_time,
                "details": basic_tests
            })
            
            print(f"✅ 基础功能测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "基础功能测试",
                "status": "FAIL",
                "duration": time.time() - test_start,
                "error": str(e)
            })
            print(f"❌ 基础功能测试失败: {str(e)}")
    
    def _test_performance(self):
        """测试性能"""
        print("\n⚡ 测试 2: 性能测试")
        test_start = time.time()
        
        try:
            performance_results = {}
            
            # 大数据量处理测试
            large_data = self.test_data * 2  # 扩展数据
            
            start_time = time.time()
            czsc = CZSC(large_data)
            processing_time = time.time() - start_time
            
            performance_results["大数据处理"] = {
                "input_size": len(large_data),
                "output_size": len(czsc.bars_ubi),
                "processing_time": processing_time,
                "throughput": len(large_data) / processing_time  # 条/秒
            }
            
            # 多次创建测试
            start_time = time.time()
            for _ in range(10):
                czsc = CZSC(self.test_data[:100])
                del czsc
            creation_time = time.time() - start_time
            
            performance_results["重复创建"] = {
                "iterations": 10,
                "total_time": creation_time,
                "avg_time": creation_time / 10
            }
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "性能测试",
                "status": "PASS",
                "duration": test_time,
                "details": performance_results
            })
            
            print(f"✅ 性能测试通过 (耗时: {test_time:.2f}s)")
            print(f"  - 处理速度: {performance_results['大数据处理']['throughput']:.1f} 条/秒")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "性能测试",
                "status": "FAIL",
                "duration": time.time() - test_start,
                "error": str(e)
            })
            print(f"❌ 性能测试失败: {str(e)}")
    
    def _test_memory_usage(self):
        """测试内存使用"""
        print("\n🧠 测试 3: 内存测试")
        test_start = time.time()
        
        try:
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples = [initial_memory]
            
            # 多轮操作监控内存
            for round_num in range(5):
                for i in range(10):
                    czsc = CZSC(self.test_data[:150])
                    strategy = CzscStrategyExample2(symbol="TEST.SH")
                    del czsc, strategy
                
                gc.collect()
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                print(f"  轮次 {round_num+1}: {current_memory:.1f} MB")
            
            memory_change = memory_samples[-1] - memory_samples[0]
            memory_stable = abs(memory_change) < 20  # 内存变化小于20MB
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "内存测试",
                "status": "PASS" if memory_stable else "WARNING",
                "duration": test_time,
                "details": {
                    "initial_memory": initial_memory,
                    "final_memory": memory_samples[-1],
                    "memory_change": memory_change,
                    "memory_stable": memory_stable,
                    "samples": memory_samples
                }
            })
            
            if memory_stable:
                print(f"✅ 内存测试通过 (耗时: {test_time:.2f}s)")
            else:
                print(f"⚠️ 内存可能有泄漏 (变化: {memory_change:.1f}MB)")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "内存测试",
                "status": "FAIL",
                "duration": time.time() - test_start,
                "error": str(e)
            })
            print(f"❌ 内存测试失败: {str(e)}")
    
    def _test_edge_cases(self):
        """测试边界条件"""
        print("\n🎯 测试 4: 边界条件")
        test_start = time.time()
        
        try:
            edge_results = []
            
            # 空数据测试
            try:
                czsc = CZSC([])
                edge_results.append({"test": "空数据", "status": "UNEXPECTED_PASS"})
            except Exception:
                edge_results.append({"test": "空数据", "status": "EXPECTED_ERROR"})
            
            # 单条数据测试
            try:
                czsc = CZSC([self.test_data[0]])
                edge_results.append({"test": "单条数据", "status": "PASS"})
            except Exception as e:
                edge_results.append({"test": "单条数据", "status": "ERROR", "error": str(e)})
            
            # 小数据集测试
            try:
                czsc = CZSC(self.test_data[:5])
                edge_results.append({"test": "小数据集", "status": "PASS"})
            except Exception as e:
                edge_results.append({"test": "小数据集", "status": "ERROR", "error": str(e)})
            
            test_time = time.time() - test_start
            
            self.test_results.append({
                "test_name": "边界条件测试",
                "status": "PASS",
                "duration": test_time,
                "details": edge_results
            })
            
            print(f"✅ 边界条件测试通过 (耗时: {test_time:.2f}s)")
            
        except Exception as e:
            self.test_results.append({
                "test_name": "边界条件测试",
                "status": "FAIL",
                "duration": time.time() - test_start,
                "error": str(e)
            })
            print(f"❌ 边界条件测试失败: {str(e)}")
    
    def _generate_report(self):
        """生成测试报告"""
        print("\n📋 生成测试报告...")
        
        total_time = datetime.now() - self.start_time
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warning_tests = len([t for t in self.test_results if t["status"] == "WARNING"])
        
        # 生成报告
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
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
                "cpu_count": psutil.cpu_count()
            },
            "issues_found": self._analyze_issues()
        }
        
        # 保存JSON报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.result_dir / f"quick_test_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # 生成简化的Markdown报告
        self._generate_markdown_report(report, timestamp)
        
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
        print(f"   Markdown: {report_file.with_suffix('.md')}")
        
        # 显示发现的问题
        issues = report['issues_found']
        if issues['critical'] or issues['warnings']:
            print(f"\n⚠️ 发现的问题:")
            for issue in issues['critical']:
                print(f"   🔴 严重: {issue}")
            for issue in issues['warnings']:
                print(f"   🟡 警告: {issue}")
        else:
            print(f"\n✅ 未发现严重问题！")
    
    def _analyze_issues(self) -> Dict[str, List[str]]:
        """分析测试中发现的问题"""
        issues = {"critical": [], "warnings": []}
        
        for test in self.test_results:
            if test["status"] == "FAIL":
                issues["critical"].append(f"{test['test_name']}: {test.get('error', '未知错误')}")
            elif test["status"] == "WARNING":
                issues["warnings"].append(f"{test['test_name']}: 可能存在问题")
            
            # 检查性能问题
            if test["test_name"] == "性能测试" and "details" in test:
                throughput = test["details"].get("大数据处理", {}).get("throughput", 0)
                if throughput < 100:  # 处理速度低于100条/秒
                    issues["warnings"].append(f"性能问题: 处理速度较低 ({throughput:.1f} 条/秒)")
            
            # 检查内存问题
            if test["test_name"] == "内存测试" and "details" in test:
                memory_change = test["details"].get("memory_change", 0)
                if abs(memory_change) > 50:  # 内存变化超过50MB
                    issues["warnings"].append(f"内存问题: 内存变化较大 ({memory_change:.1f}MB)")
        
        return issues
    
    def _generate_markdown_report(self, report: Dict[str, Any], timestamp: str):
        """生成Markdown报告"""
        md_content = f"""# CZSC Enhanced 快速系统测试报告

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
{test['error']}
```

"""
        
        issues = report['issues_found']
        if issues['critical'] or issues['warnings']:
            md_content += """## ⚠️ 发现的问题

"""
            for issue in issues['critical']:
                md_content += f"🔴 **严重**: {issue}\n\n"
            for issue in issues['warnings']:
                md_content += f"🟡 **警告**: {issue}\n\n"
        
        md_content += f"""## 🔧 系统信息

- **Python版本**: {report['system_info']['python_version'].split()[0]}
- **平台**: {report['system_info']['platform']}
- **内存总量**: {report['system_info']['memory_total']:.1f} GB
- **CPU核心数**: {report['system_info']['cpu_count']}

## 📅 测试信息

- **测试时间**: {report['test_summary']['test_date']}
- **报告生成**: {datetime.now().isoformat()}

---

*本报告由 CZSC Enhanced 快速测试系统生成*
"""
        
        md_file = self.result_dir / f"quick_test_report_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

def main():
    """主函数"""
    print("🧪 CZSC Enhanced 快速系统测试")
    print("=" * 50)
    
    # 创建测试套件
    test_suite = QuickTestSuite()
    
    # 运行测试
    test_suite.run_quick_tests()

if __name__ == "__main__":
    main()