"""测试代码修复服务"""
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from app.services.test_generator import get_test_generator
from app.services.git_helper import GitHelper
from app.config import get_settings


class TestFixer:
    """测试代码修复器 - 对已生成的测试文件进行语法验证和修复"""
    
    def __init__(
        self,
        language: str = "golang",
        test_framework: str = "ginkgo",
        ai_provider: str = "openai"
    ):
        """
        初始化测试修复器
        
        Args:
            language: 编程语言
            test_framework: 测试框架
            ai_provider: AI提供商
        """
        self.language = language
        self.test_framework = test_framework
        self.ai_provider = ai_provider
        self.settings = get_settings()
        
        # 获取对应语言的测试生成器（用于验证和修复）
        self.generator = get_test_generator(
            language=language,
            ai_provider=ai_provider,
            repo_path=None
        )
        
        logger.info(f"✅ 测试修复器初始化完成: {language} / {test_framework}")
    
    def fix_tests_in_directory(
        self,
        workspace_path: str,
        test_directory: str,
        max_fix_attempts: int = 5
    ) -> Dict:
        """
        修复指定目录下的所有测试文件
        
        Args:
            workspace_path: 工作空间路径，如 /app/workspace/a5db9f32-xxx
            test_directory: 测试目录相对路径，如 internal/biz
            max_fix_attempts: 每个文件最大修复尝试次数
            
        Returns:
            修复结果字典
        """
        workspace = Path(workspace_path)
        test_dir = workspace / test_directory
        
        if not workspace.exists():
            error_msg = f"工作空间不存在: {workspace_path}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'total_files': 0,
                'fixed_files': 0,
                'failed_files': 0,
                'skipped_files': 0,
                'file_results': [],
                'message': error_msg
            }
        
        if not test_dir.exists():
            error_msg = f"测试目录不存在: {test_dir}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'total_files': 0,
                'fixed_files': 0,
                'failed_files': 0,
                'skipped_files': 0,
                'file_results': [],
                'message': error_msg
            }
        
        logger.info(f"🔍 开始扫描测试目录: {test_dir}")
        
        # 查找所有测试文件
        test_files = self._find_test_files(test_dir)
        
        if not test_files:
            message = f"未找到测试文件: {test_dir}"
            logger.warning(f"⚠️ {message}")
            return {
                'success': True,
                'total_files': 0,
                'fixed_files': 0,
                'failed_files': 0,
                'skipped_files': 0,
                'file_results': [],
                'message': message
            }
        
        logger.info(f"📝 找到 {len(test_files)} 个测试文件")
        
        # 修复每个测试文件
        results = []
        fixed_count = 0
        failed_count = 0
        skipped_count = 0
        
        for test_file in test_files:
            result = self._fix_single_test_file(
                test_file,
                max_fix_attempts=max_fix_attempts
            )
            results.append(result)
            
            if result['success']:
                if result['fixed']:
                    fixed_count += 1
                else:
                    skipped_count += 1  # 原本就没错误
            else:
                failed_count += 1
        
        success = failed_count == 0
        message = f"完成! 总计: {len(test_files)}, 修复: {fixed_count}, 失败: {failed_count}, 跳过: {skipped_count}"
        
        logger.info(f"{'✅' if success else '⚠️'} {message}")
        
        return {
            'success': success,
            'total_files': len(test_files),
            'fixed_files': fixed_count,
            'failed_files': failed_count,
            'skipped_files': skipped_count,
            'file_results': results,
            'message': message
        }
    
    async def fix_tests_in_directory_async(
        self,
        workspace_path: str,
        test_directory: str,
        max_fix_attempts: int = 5,
        max_concurrent: int = 5,
        auto_git_commit: bool = False,
        git_username: str = "ut-agent",
        git_branch_name: Optional[str] = None,
        git_commit_message: Optional[str] = None
    ) -> Dict:
        """
        异步并发修复指定目录下的所有测试文件
        
        Args:
            workspace_path: 工作空间路径，如 /app/workspace/a5db9f32-xxx
            test_directory: 测试目录相对路径，如 internal/biz
            max_fix_attempts: 每个文件最大修复尝试次数
            max_concurrent: 最大并发数
            auto_git_commit: 是否自动执行 Git 提交和推送
            git_username: Git 用户名
            git_branch_name: Git 分支名称（可选，默认自动生成）
            git_commit_message: Git 提交信息（可选，默认自动生成）
            
        Returns:
            修复结果字典
        """
        workspace = Path(workspace_path)
        test_dir = workspace / test_directory
        
        if not workspace.exists():
            error_msg = f"工作空间不存在: {workspace_path}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'total_files': 0,
                'fixed_files': 0,
                'failed_files': 0,
                'skipped_files': 0,
                'file_results': [],
                'message': error_msg
            }
        
        if not test_dir.exists():
            error_msg = f"测试目录不存在: {test_dir}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'total_files': 0,
                'fixed_files': 0,
                'failed_files': 0,
                'skipped_files': 0,
                'file_results': [],
                'message': error_msg
            }
        
        logger.info(f"🔍 开始扫描测试目录: {test_dir}")
        
        # 查找所有测试文件
        test_files = self._find_test_files(test_dir)
        
        if not test_files:
            message = f"未找到测试文件: {test_dir}"
            logger.warning(f"⚠️ {message}")
            return {
                'success': True,
                'total_files': 0,
                'fixed_files': 0,
                'failed_files': 0,
                'skipped_files': 0,
                'file_results': [],
                'message': message
            }
        
        logger.info(f"📝 找到 {len(test_files)} 个测试文件")
        logger.info(f"🚀 使用异步并发处理 (最大并发: {max_concurrent})")
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # 异步并发修复所有测试文件
        tasks = [
            self._fix_single_test_file_async(
                test_file,
                max_fix_attempts,
                semaphore,
                idx + 1,
                len(test_files)
            )
            for idx, test_file in enumerate(test_files)
        ]
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        fixed_count = 0
        failed_count = 0
        skipped_count = 0
        final_results = []
        
        for result in results:
            # 处理异常情况
            if isinstance(result, Exception):
                logger.error(f"❌ 任务异常: {result}")
                failed_count += 1
                final_results.append({
                    'success': False,
                    'file_path': 'unknown',
                    'fixed': False,
                    'errors': [str(result)]
                })
                continue
            
            final_results.append(result)
            
            if result['success']:
                if result['fixed']:
                    fixed_count += 1
                else:
                    skipped_count += 1  # 原本就没错误
            else:
                failed_count += 1
        
        success = failed_count == 0
        message = f"完成! 总计: {len(test_files)}, 修复: {fixed_count}, 失败: {failed_count}, 跳过: {skipped_count}"
        
        logger.info(f"{'✅' if success else '⚠️'} {message}")
        
        # Git 操作结果
        git_result = None
        
        # 如果启用自动 Git 提交
        if auto_git_commit and (fixed_count > 0 or failed_count > 0):
            logger.info("🔄 开始 Git 操作...")
            try:
                git_helper = GitHelper(workspace_path, git_username)
                
                # 在线程池中执行 Git 操作（避免阻塞）
                loop = asyncio.get_event_loop()
                git_result = await loop.run_in_executor(
                    None,
                    git_helper.create_commit_and_push,
                    git_branch_name,
                    git_commit_message
                )
                
                if git_result['success']:
                    logger.info(f"✅ Git 操作成功: {git_result['message']}")
                else:
                    logger.error(f"❌ Git 操作失败: {git_result['message']}")
                    
            except Exception as e:
                logger.error(f"❌ Git 操作异常: {e}")
                git_result = {
                    'success': False,
                    'error': str(e),
                    'message': f'Git 操作异常: {str(e)}'
                }
        
        return {
            'success': success,
            'total_files': len(test_files),
            'fixed_files': fixed_count,
            'failed_files': failed_count,
            'skipped_files': skipped_count,
            'file_results': final_results,
            'message': message,
            'git_result': git_result
        }
    
    def _find_test_files(self, directory: Path) -> List[Path]:
        """
        查找目录下的所有测试文件
        
        Args:
            directory: 搜索目录
            
        Returns:
            测试文件路径列表
        """
        test_files = []
        
        # 根据语言确定测试文件模式
        if self.language == 'golang':
            pattern = "*_test.go"
        elif self.language == 'cpp':
            pattern = "*_test.cpp"
        elif self.language == 'c':
            pattern = "*_test.c"
        else:
            pattern = "*_test.*"
        
        # 递归查找
        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                test_files.append(file_path)
        
        return sorted(test_files)
    
    def _fix_single_test_file(
        self,
        test_file: Path,
        max_fix_attempts: int = 5
    ) -> Dict:
        """
        修复单个测试文件
        
        Args:
            test_file: 测试文件路径
            max_fix_attempts: 最大修复尝试次数
            
        Returns:
            修复结果
        """
        file_name = test_file.name
        logger.info(f"🔧 处理文件: {file_name}")
        
        try:
            # 读取测试代码
            with open(test_file, 'r', encoding='utf-8') as f:
                test_code = f.read()
            
            # 验证语法并自动修复
            original_code = test_code
            had_errors = False
            fixed = False
            
            for attempt in range(1, max_fix_attempts + 1):
                logger.debug(f"  第 {attempt} 次验证...")
                
                # 验证语法
                validation_result = self.generator.validate_syntax(test_code)
                
                if validation_result['valid']:
                    # 语法正确
                    final_code = validation_result.get('formatted_code', test_code)
                    
                    # 如果代码有变化，保存
                    if final_code != original_code:
                        with open(test_file, 'w', encoding='utf-8') as f:
                            f.write(final_code)
                        fixed = True
                        logger.info(f"  ✅ {file_name}: 修复成功 (尝试 {attempt} 次)")
                    else:
                        logger.debug(f"  ✅ {file_name}: 无需修复")
                    
                    return {
                        'file_path': str(test_file),
                        'success': True,
                        'original_had_errors': had_errors,
                        'fixed': fixed,
                        'attempts': attempt,
                        'errors': []
                    }
                
                # 发现语法错误
                had_errors = True
                errors = validation_result.get('errors', [])
                logger.warning(f"  ⚠️ 发现语法错误 (第 {attempt} 次): {errors}")
                
                # 如果是最后一次尝试，不再修复，删除文件
                if attempt >= max_fix_attempts:
                    logger.error(f"  ❌ {file_name}: 达到最大修复次数 ({max_fix_attempts} 次)，删除文件")
                    try:
                        test_file.unlink()  # 删除文件
                        logger.warning(f"  🗑️  已删除失败的测试文件: {file_name}")
                    except Exception as delete_error:
                        logger.error(f"  ❌ 删除文件失败: {delete_error}")
                    
                    return {
                        'file_path': str(test_file),
                        'success': False,
                        'original_had_errors': True,
                        'fixed': False,
                        'attempts': attempt,
                        'errors': errors,
                        'deleted': True
                    }
                
                # 调用AI修复
                logger.debug(f"  🔧 调用 AI 修复...")
                
                # 构造一个简单的 file_analysis
                file_analysis = {
                    'file_path': str(test_file),
                    'functions': []  # 对于修复不需要函数信息
                }
                
                test_code = self.generator._fix_syntax_errors(
                    test_code,
                    errors,
                    file_analysis,
                    self.language,
                    self.test_framework
                )
                
                logger.debug(f"  ✅ AI 修复完成")
            
            # 不应该到达这里
            return {
                'file_path': str(test_file),
                'success': False,
                'original_had_errors': True,
                'fixed': False,
                'attempts': max_fix_attempts,
                'errors': ['未知错误']
            }
            
        except Exception as e:
            error_msg = f"处理文件异常: {str(e)}"
            logger.error(f"  ❌ {file_name}: {error_msg}")
            return {
                'file_path': str(test_file),
                'success': False,
                'original_had_errors': False,
                'fixed': False,
                'attempts': 0,
                'errors': [error_msg]
            }
    
    async def _fix_single_test_file_async(
        self,
        test_file: Path,
        max_fix_attempts: int,
        semaphore: asyncio.Semaphore,
        file_idx: int,
        total_files: int
    ) -> Dict:
        """
        异步修复单个测试文件
        
        Args:
            test_file: 测试文件路径
            max_fix_attempts: 最大修复尝试次数
            semaphore: 信号量（控制并发数）
            file_idx: 当前文件索引
            total_files: 文件总数
            
        Returns:
            修复结果
        """
        async with semaphore:
            file_name = test_file.name
            logger.info(f"🔧 [{file_idx}/{total_files}] 处理文件: {file_name}")
            
            try:
                # 异步读取测试代码
                loop = asyncio.get_event_loop()
                test_code = await loop.run_in_executor(
                    None,
                    lambda: test_file.read_text(encoding='utf-8')
                )
                
                # 验证语法并自动修复
                original_code = test_code
                had_errors = False
                fixed = False
                
                for attempt in range(1, max_fix_attempts + 1):
                    logger.debug(f"  [{file_idx}/{total_files}] {file_name}: 第 {attempt} 次验证...")
                    
                    # 验证语法（在线程池中执行，避免阻塞）
                    validation_result = await loop.run_in_executor(
                        None,
                        self.generator.validate_syntax,
                        test_code
                    )
                    
                    if validation_result['valid']:
                        # 语法正确
                        final_code = validation_result.get('formatted_code', test_code)
                        
                        # 如果代码有变化，异步保存
                        if final_code != original_code:
                            await loop.run_in_executor(
                                None,
                                lambda: test_file.write_text(final_code, encoding='utf-8')
                            )
                            fixed = True
                            logger.info(f"  ✅ [{file_idx}/{total_files}] {file_name}: 修复成功 (尝试 {attempt} 次)")
                        else:
                            logger.debug(f"  ✅ [{file_idx}/{total_files}] {file_name}: 无需修复")
                        
                        return {
                            'file_path': str(test_file),
                            'success': True,
                            'original_had_errors': had_errors,
                            'fixed': fixed,
                            'attempts': attempt,
                            'errors': []
                        }
                    
                    # 发现语法错误
                    had_errors = True
                    errors = validation_result.get('errors', [])
                    logger.warning(f"  ⚠️ [{file_idx}/{total_files}] {file_name}: 发现语法错误 (第 {attempt} 次)")
                    
                    # 如果是最后一次尝试，不再修复，删除文件
                    if attempt >= max_fix_attempts:
                        logger.error(f"  ❌ [{file_idx}/{total_files}] {file_name}: 达到最大修复次数 ({max_fix_attempts} 次)，删除文件")
                        try:
                            await loop.run_in_executor(
                                None,
                                test_file.unlink
                            )
                            logger.warning(f"  🗑️  [{file_idx}/{total_files}] 已删除失败的测试文件: {file_name}")
                        except Exception as delete_error:
                            logger.error(f"  ❌ [{file_idx}/{total_files}] 删除文件失败: {delete_error}")
                        
                        return {
                            'file_path': str(test_file),
                            'success': False,
                            'original_had_errors': True,
                            'fixed': False,
                            'attempts': attempt,
                            'errors': errors,
                            'deleted': True
                        }
                    
                    # 调用AI修复（在线程池中执行）
                    logger.debug(f"  🔧 [{file_idx}/{total_files}] {file_name}: 调用 AI 修复...")
                    
                    # 构造一个简单的 file_analysis
                    file_analysis = {
                        'file_path': str(test_file),
                        'functions': []  # 对于修复不需要函数信息
                    }
                    
                    test_code = await loop.run_in_executor(
                        None,
                        self.generator._fix_syntax_errors,
                        test_code,
                        errors,
                        file_analysis,
                        self.language,
                        self.test_framework
                    )
                    
                    logger.debug(f"  ✅ [{file_idx}/{total_files}] {file_name}: AI 修复完成")
                
                # 不应该到达这里
                return {
                    'file_path': str(test_file),
                    'success': False,
                    'original_had_errors': True,
                    'fixed': False,
                    'attempts': max_fix_attempts,
                    'errors': ['未知错误']
                }
                
            except Exception as e:
                error_msg = f"处理文件异常: {str(e)}"
                logger.error(f"  ❌ [{file_idx}/{total_files}] {file_name}: {error_msg}")
                return {
                    'file_path': str(test_file),
                    'success': False,
                    'original_had_errors': False,
                    'fixed': False,
                    'attempts': 0,
                    'errors': [error_msg]
                }


def fix_tests_cli(
    workspace_path: str,
    test_directory: str,
    language: str = "golang",
    test_framework: str = "ginkgo",
    max_fix_attempts: int = 5
) -> Dict:
    """
    命令行工具入口 - 修复测试代码
    
    Args:
        workspace_path: 工作空间路径
        test_directory: 测试目录相对路径
        language: 编程语言
        test_framework: 测试框架
        max_fix_attempts: 最大修复尝试次数
        
    Returns:
        修复结果
    """
    fixer = TestFixer(
        language=language,
        test_framework=test_framework
    )
    
    return fixer.fix_tests_in_directory(
        workspace_path=workspace_path,
        test_directory=test_directory,
        max_fix_attempts=max_fix_attempts
    )

