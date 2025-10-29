"""测试执行服务"""
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
from app.config import get_settings

settings = get_settings()


class TestExecutor:
    """测试执行器基类"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
    
    def execute_tests(self, test_files: List[str]) -> Dict:
        """执行测试"""
        raise NotImplementedError
    
    def _run_command(self, cmd: List[str], cwd: Optional[str] = None, use_bash: bool = False) -> subprocess.CompletedProcess:
        """
        执行命令
        
        Args:
            cmd: 命令列表
            cwd: 工作目录
            use_bash: 是否使用 bash -c 执行（用于支持 GVM）
        """
        try:
            if use_bash:
                # 使用 bash 执行，支持 GVM 环境
                cmd_str = ' '.join(cmd)
                bash_cmd = f"source /root/.gvm/scripts/gvm 2>/dev/null || true; {cmd_str}"
                result = subprocess.run(
                    ["bash", "-c", bash_cmd],
                    cwd=cwd or self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=settings.test_execution_timeout  # 从环境变量读取
                )
            else:
                result = subprocess.run(
                    cmd,
                    cwd=cwd or self.workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=settings.test_execution_timeout  # 从环境变量读取
                )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"命令执行超时: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            raise


class GolangTestExecutor(TestExecutor):
    """Golang测试执行器"""
    
    def __init__(self, workspace_path: str, test_framework: str = "go_test"):
        super().__init__(workspace_path)
        self.test_framework = test_framework
        self.go_version = None  # 存储项目所需的Go版本
    
    def _detect_go_version_from_mod(self) -> Optional[str]:
        """
        从go.mod文件中检测项目所需的Go版本
        
        Returns:
            Go版本字符串，如 "1.20", "1.21" 等；如果未找到则返回None
        """
        go_mod_path = self.workspace_path / "go.mod"
        if not go_mod_path.exists():
            logger.warning(f"go.mod 不存在: {go_mod_path}")
            return None
        
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 匹配 "go 1.20" 或 "go 1.20.1" 格式
                    if line.startswith('go '):
                        version_str = line.split('go ')[-1].strip()
                        # 提取主版本号 (1.20 或 1.20.1)
                        import re
                        match = re.match(r'(\d+\.\d+)(?:\.\d+)?', version_str)
                        if match:
                            version = match.group(1)
                            logger.info(f"✅ 检测到项目Go版本: {version}")
                            return version
        except Exception as e:
            logger.warning(f"读取 go.mod 失败: {e}")
        
        return None
    
    def _check_gvm_available(self) -> bool:
        """检查 GVM 是否可用"""
        try:
            # 检查 GVM 脚本是否存在
            gvm_script = Path("/root/.gvm/scripts/gvm")
            if gvm_script.exists():
                logger.info("✅ GVM 可用")
                return True
            else:
                logger.info("⚠️  GVM 不可用，将使用备用方案")
                return False
        except Exception as e:
            logger.warning(f"检查 GVM 失败: {e}")
            return False
    
    def _install_go_version_with_gvm(self, version: str) -> bool:
        """
        使用 GVM 安装指定的 Go 版本
        
        Args:
            version: Go版本，如 "1.20", "1.21"
            
        Returns:
            是否成功安装
        """
        try:
            # 构建完整版本号（需要查询可用的补丁版本）
            # 例如：1.20 -> 1.20.14
            logger.info(f"检查 GVM 中是否已安装 Go {version}...")
            
            # 使用 bash 执行 gvm 命令
            check_cmd = f"source /root/.gvm/scripts/gvm && gvm list"
            result = subprocess.run(
                ["bash", "-c", check_cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            installed_versions = result.stdout
            logger.info(f"已安装的版本:\n{installed_versions}")
            
            # 检查是否已安装匹配的版本
            import re
            pattern = re.compile(rf'go{version}(?:\.\d+)?')
            if pattern.search(installed_versions):
                logger.info(f"✅ Go {version} 已安装")
                return True
            
            # 需要安装
            logger.info(f"📦 安装 Go {version}...")
            
            # 尝试安装多个可能的补丁版本
            patch_versions = ["14", "13", "12", "11", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "0"]
            
            for patch in patch_versions:
                full_version = f"go{version}.{patch}"
                install_cmd = f"source /root/.gvm/scripts/gvm && gvm install {full_version} -B"
                logger.info(f"尝试安装 {full_version}...")
                
                result = subprocess.run(
                    ["bash", "-c", install_cmd],
                    capture_output=True,
                    text=True,
                    timeout=settings.ginkgo_install_timeout  # 从环境变量读取
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ 成功安装 {full_version}")
                    return True
                else:
                    logger.debug(f"安装 {full_version} 失败: {result.stderr}")
            
            logger.warning(f"⚠️  无法找到可安装的 Go {version} 版本")
            return False
            
        except Exception as e:
            logger.warning(f"使用 GVM 安装 Go 版本失败: {e}")
            return False
    
    def _setup_go_version(self, required_version: str) -> bool:
        """
        设置指定的Go版本（使用 GVM 或备用方案）
        
        Args:
            required_version: 所需的Go版本，如 "1.20", "1.21"
            
        Returns:
            是否成功设置
        """
        try:
            # 检查当前Go版本
            result = subprocess.run(
                ["go", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            current_version_output = result.stdout
            logger.info(f"当前Go版本: {current_version_output.strip()}")
            
            # 提取当前版本号
            import re
            match = re.search(r'go(\d+\.\d+)(?:\.\d+)?', current_version_output)
            if match:
                current_version = match.group(1)
                logger.info(f"当前Go版本号: {current_version}, 需要版本: {required_version}")
                
                # 如果版本匹配，无需切换
                if current_version == required_version:
                    logger.info(f"✅ 当前Go版本 {current_version} 符合要求")
                    return True
                
                # 版本不匹配，尝试使用 GVM 切换
                logger.info(f"⚠️  当前Go版本 {current_version} 与项目要求 {required_version} 不匹配")
                
                # 方案1：使用 GVM 切换版本
                if self._check_gvm_available():
                    logger.info(f"使用 GVM 切换到 Go {required_version}...")
                    
                    # 首先确保版本已安装
                    self._install_go_version_with_gvm(required_version)
                    
                    # 切换版本
                    switch_cmd = f"source /root/.gvm/scripts/gvm && gvm use go{required_version}"
                    result = subprocess.run(
                        ["bash", "-c", switch_cmd],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        logger.info(f"✅ 已通过 GVM 切换到 Go {required_version}")
                        
                        # 验证切换是否成功
                        verify_cmd = f"source /root/.gvm/scripts/gvm && go version"
                        verify_result = subprocess.run(
                            ["bash", "-c", verify_cmd],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        logger.info(f"验证版本: {verify_result.stdout.strip()}")
                        return True
                    else:
                        logger.warning(f"GVM 切换失败: {result.stderr}")
                        # 继续尝试备用方案
                
                # 方案2：使用 GOTOOLCHAIN（Go 1.21+ 特性）
                logger.info(f"尝试使用 GOTOOLCHAIN 环境变量...")
                import os
                os.environ['GOTOOLCHAIN'] = f'go{required_version}'
                logger.info(f"✅ 已设置 GOTOOLCHAIN=go{required_version}")
                
                # 验证是否成功
                verify_result = subprocess.run(
                    ["go", "version"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=os.environ.copy()
                )
                logger.info(f"使用 GOTOOLCHAIN 后的版本: {verify_result.stdout.strip()}")
                return True
                
        except Exception as e:
            logger.warning(f"设置Go版本失败: {e}")
            logger.info("将使用系统默认Go版本继续执行")
            return False
        
        return True
    
    def execute_tests(self, test_files: List[str]) -> Dict:
        """
        执行Go测试
        
        Returns:
            {
                'passed': bool,
                'total': int,
                'passed_count': int,
                'failed_count': int,
                'output': str,
                'coverage_file': str
            }
        """
        logger.info(f"执行Go测试: {len(test_files)} 个文件 (框架: {self.test_framework})")
        
        # 检测并设置Go版本
        required_version = self._detect_go_version_from_mod()
        if required_version:
            self.go_version = required_version
            self._setup_go_version(required_version)
        else:
            logger.info("未检测到Go版本要求，使用系统默认版本")
        
        # 根据测试框架选择执行命令
        if self.test_framework == "ginkgo":
            return self._execute_ginkgo_tests(test_files)
        else:
            return self._execute_standard_tests(test_files)
    
    def _execute_standard_tests(self, test_files: List[str]) -> Dict:
        """执行标准go test"""
        coverage_file = self.workspace_path / "coverage.out"
        
        cmd = [
            "go", "test",
            "-v",
            f"-coverprofile={coverage_file}",
            "./..."
        ]
        
        try:
            # 使用 bash 执行以支持 GVM
            result = self._run_command(cmd, use_bash=True)
            output = result.stdout + result.stderr
            
            # 解析测试结果
            passed_count = output.count("PASS:")
            failed_count = output.count("FAIL:")
            total_count = passed_count + failed_count
            
            logger.info(f"测试完成: {passed_count}/{total_count} 通过")
            
            return {
                'passed': result.returncode == 0,
                'total': total_count,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'output': output,
                'coverage_file': str(coverage_file) if coverage_file.exists() else None
            }
        
        except Exception as e:
            logger.error(f"执行Go测试失败: {e}")
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'output': str(e),
                'coverage_file': None
            }
    
    def _execute_ginkgo_tests(self, test_files: List[str]) -> Dict:
        """执行Ginkgo BDD测试"""
        coverage_file = self.workspace_path / "coverage.out"
        
        # 首先确保安装了ginkgo
        try:
            install_cmd = ["go", "install", "github.com/onsi/ginkgo/v2/ginkgo@latest"]
            self._run_command(install_cmd, use_bash=True)
            logger.info("✅ Ginkgo已安装")
        except Exception as e:
            logger.warning(f"安装Ginkgo失败: {e}")
        
        # 安装 Gomega 依赖
        try:
            gomega_cmd = ["go", "get", "github.com/onsi/gomega"]
            self._run_command(gomega_cmd, use_bash=True)
            logger.info("✅ Gomega依赖已安装")
        except Exception as e:
            logger.warning(f"安装Gomega失败: {e}")
        
        # 更新依赖（确保所有导入的包都可用）
        try:
            logger.info("更新 Go 模块依赖...")
            mod_tidy_cmd = ["go", "mod", "tidy"]
            self._run_command(mod_tidy_cmd, use_bash=True)
            logger.info("✅ Go 模块依赖已更新")
        except Exception as e:
            logger.warning(f"更新依赖失败: {e}")
        
        # 执行Ginkgo测试
        # 注意：Ginkgo v2 的 --coverprofile 只接受文件名，不接受路径
        # 需要使用 --output-dir 指定输出目录
        cmd = [
            "ginkgo",
            "-r",  # 递归运行
            "-v",  # 详细输出
            "--cover",  # 生成覆盖率
            "--coverprofile=coverage.out",  # 只传文件名
            f"--output-dir={self.workspace_path}",  # 指定输出目录
            "--randomize-all",  # 随机化测试顺序
            "--fail-on-pending",  # 待定测试视为失败
            "-mod=mod",  # 使用 go.mod 而不是 vendor 目录
        ]
        
        try:
            logger.info(f"执行命令: {' '.join(cmd)}")
            logger.info(f"工作目录: {self.workspace_path}")
            
            # 使用 bash 执行以支持 GVM
            result = self._run_command(cmd, use_bash=True)
            output = result.stdout + result.stderr
            
            # 记录完整输出用于调试
            logger.info("=" * 80)
            logger.info("Ginkgo 执行输出:")
            logger.info(output)
            logger.info("=" * 80)
            logger.info(f"返回码: {result.returncode}")
            
            # 检查编译错误
            if "Failed to compile" in output or "cannot find module" in output:
                logger.error("⚠️  测试编译失败，可能是依赖问题")
                logger.error("请检查 go.mod 和 vendor 目录")
            
            # 解析Ginkgo输出
            # Ginkgo输出格式示例：
            # • [PASSED] in 0.123 seconds
            # Ran 15 of 15 Specs in 1.234 seconds
            passed_count = output.count("• [PASSED]") + output.count("✓")
            failed_count = output.count("• [FAILED]") + output.count("✗")
            total_count = passed_count + failed_count
            
            # 从输出中提取总数
            import re
            ran_match = re.search(r'Ran (\d+) of (\d+) Specs', output)
            if ran_match:
                total_count = int(ran_match.group(2))
                logger.info(f"从输出中提取到: Ran {ran_match.group(1)} of {ran_match.group(2)} Specs")
            
            logger.info(f"Ginkgo测试完成: {passed_count}/{total_count} 通过")
            
            return {
                'passed': result.returncode == 0,
                'total': total_count,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'output': output,
                'coverage_file': str(coverage_file) if coverage_file.exists() else None
            }
        
        except Exception as e:
            logger.error(f"执行Ginkgo测试失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'output': str(e),
                'coverage_file': None
            }
    
    def collect_coverage(self, coverage_file: str) -> Dict:
        """
        收集Go覆盖率数据
        
        Returns:
            覆盖率统计字典
        """
        try:
            # 使用go tool cover分析覆盖率
            cmd = ["go", "tool", "cover", "-func", coverage_file]
            result = self._run_command(cmd, use_bash=True)
            
            if result.returncode != 0:
                logger.error("解析覆盖率失败")
                return {}
            
            # 解析输出
            lines = result.stdout.strip().split('\n')
            total_line = lines[-1]  # 最后一行是总覆盖率
            
            # 提取总覆盖率百分比
            if 'total:' in total_line:
                coverage_str = total_line.split('\t')[-1].replace('%', '')
                total_coverage = float(coverage_str)
            else:
                total_coverage = 0.0
            
            # 解析文件级覆盖率
            files_coverage = {}
            for line in lines[:-1]:
                parts = line.split('\t')
                if len(parts) >= 2:
                    func_name = parts[0]
                    coverage = float(parts[-1].replace('%', ''))
                    files_coverage[func_name] = coverage
            
            logger.info(f"✅ 覆盖率: {total_coverage}%")
            
            return {
                'line_coverage': total_coverage,
                'files_coverage': files_coverage
            }
        
        except Exception as e:
            logger.error(f"收集覆盖率失败: {e}")
            return {}


class CppTestExecutor(TestExecutor):
    """C++测试执行器（Google Test）"""
    
    def execute_tests(self, test_files: List[str]) -> Dict:
        """执行C++测试"""
        logger.info(f"执行C++测试: {len(test_files)} 个文件")
        
        # 编译测试
        compiled = self._compile_tests(test_files)
        if not compiled:
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'output': "编译失败",
                'coverage_file': None
            }
        
        # 运行测试
        test_binary = self.workspace_path / "test_runner"
        
        try:
            result = self._run_command([str(test_binary)])
            output = result.stdout + result.stderr
            
            # 解析Google Test输出
            passed_count = output.count("[  PASSED  ]")
            failed_count = output.count("[  FAILED  ]")
            total_count = passed_count + failed_count
            
            logger.info(f"测试完成: {passed_count}/{total_count} 通过")
            
            # 收集覆盖率
            self._generate_coverage()
            
            return {
                'passed': result.returncode == 0,
                'total': total_count,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'output': output,
                'coverage_file': str(self.workspace_path / "coverage.info")
            }
        
        except Exception as e:
            logger.error(f"执行C++测试失败: {e}")
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'output': str(e),
                'coverage_file': None
            }
    
    def _compile_tests(self, test_files: List[str]) -> bool:
        """编译测试文件"""
        try:
            cmd = [
                "g++",
                "-std=c++17",
                "-coverage",  # 启用覆盖率
                "-o", str(self.workspace_path / "test_runner"),
                *test_files,
                "-lgtest",
                "-lgtest_main",
                "-pthread"
            ]
            
            result = self._run_command(cmd)
            
            if result.returncode != 0:
                logger.error(f"编译失败: {result.stderr}")
                return False
            
            logger.info("✅ 编译成功")
            return True
        
        except Exception as e:
            logger.error(f"编译异常: {e}")
            return False
    
    def _generate_coverage(self):
        """生成覆盖率报告"""
        try:
            # 运行gcov
            self._run_command(["gcov", "*.gcda"])
            
            # 生成lcov报告
            self._run_command([
                "lcov",
                "--capture",
                "--directory", ".",
                "--output-file", "coverage.info"
            ])
            
            logger.info("✅ 覆盖率报告生成成功")
        
        except Exception as e:
            logger.error(f"生成覆盖率失败: {e}")
    
    def collect_coverage(self, coverage_file: str) -> Dict:
        """收集C++覆盖率数据"""
        try:
            # 使用lcov解析
            cmd = ["lcov", "--summary", coverage_file]
            result = self._run_command(cmd)
            
            # 解析输出
            output = result.stdout
            
            # 提取覆盖率数据
            line_coverage = 0.0
            function_coverage = 0.0
            
            for line in output.split('\n'):
                if 'lines......:' in line:
                    coverage_str = line.split(':')[-1].strip().split('%')[0]
                    line_coverage = float(coverage_str)
                elif 'functions..:' in line:
                    coverage_str = line.split(':')[-1].strip().split('%')[0]
                    function_coverage = float(coverage_str)
            
            return {
                'line_coverage': line_coverage,
                'function_coverage': function_coverage,
                'files_coverage': {}
            }
        
        except Exception as e:
            logger.error(f"收集覆盖率失败: {e}")
            return {}


class CTestExecutor(TestExecutor):
    """C测试执行器（CUnit）"""
    
    def execute_tests(self, test_files: List[str]) -> Dict:
        """执行C测试"""
        logger.info(f"执行C测试: {len(test_files)} 个文件")
        
        # 编译测试
        compiled = self._compile_tests(test_files)
        if not compiled:
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'output': "编译失败",
                'coverage_file': None
            }
        
        # 运行测试
        test_binary = self.workspace_path / "test_runner"
        
        try:
            result = self._run_command([str(test_binary)])
            output = result.stdout + result.stderr
            
            # 解析测试结果（简化版）
            passed_count = output.count("PASSED")
            failed_count = output.count("FAILED")
            total_count = passed_count + failed_count
            
            logger.info(f"测试完成: {passed_count}/{total_count} 通过")
            
            # 生成覆盖率
            self._generate_coverage()
            
            return {
                'passed': result.returncode == 0,
                'total': total_count,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'output': output,
                'coverage_file': str(self.workspace_path / "coverage.info")
            }
        
        except Exception as e:
            logger.error(f"执行C测试失败: {e}")
            return {
                'passed': False,
                'total': 0,
                'passed_count': 0,
                'failed_count': 0,
                'output': str(e),
                'coverage_file': None
            }
    
    def _compile_tests(self, test_files: List[str]) -> bool:
        """编译测试文件"""
        try:
            cmd = [
                "gcc",
                "-coverage",
                "-o", str(self.workspace_path / "test_runner"),
                *test_files,
                "-lcunit"
            ]
            
            result = self._run_command(cmd)
            
            if result.returncode != 0:
                logger.error(f"编译失败: {result.stderr}")
                return False
            
            logger.info("✅ 编译成功")
            return True
        
        except Exception as e:
            logger.error(f"编译异常: {e}")
            return False
    
    def _generate_coverage(self):
        """生成覆盖率报告"""
        try:
            self._run_command(["gcov", "*.gcda"])
            
            self._run_command([
                "lcov",
                "--capture",
                "--directory", ".",
                "--output-file", "coverage.info"
            ])
            
            logger.info("✅ 覆盖率报告生成成功")
        
        except Exception as e:
            logger.error(f"生成覆盖率失败: {e}")
    
    def collect_coverage(self, coverage_file: str) -> Dict:
        """收集C覆盖率数据"""
        # 与C++相同的方式
        cpp_executor = CppTestExecutor(str(self.workspace_path))
        return cpp_executor.collect_coverage(coverage_file)


def get_test_executor(language: str, workspace_path: str, test_framework: str = None) -> TestExecutor:
    """工厂函数：获取对应语言的测试执行器"""
    executors = {
        'golang': GolangTestExecutor,
        'cpp': CppTestExecutor,
        'c': CTestExecutor
    }
    
    executor_class = executors.get(language)
    if not executor_class:
        raise ValueError(f"不支持的语言: {language}")
    
    # 如果是Golang且指定了test_framework，传递参数
    if language == 'golang' and test_framework:
        return executor_class(workspace_path, test_framework)
    
    return executor_class(workspace_path)

