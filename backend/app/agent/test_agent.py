"""AI测试生成Agent"""
import os
import asyncio
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from loguru import logger
from uuid import uuid4

from app.services.git_service import GitService
from app.services.code_analyzer import get_analyzer
from app.services.test_generator import get_test_generator
from app.services.test_executor import get_test_executor


class TestGenerationAgent:
    """测试生成Agent - 编排整个测试生成流程"""
    
    def __init__(self):
        self.git_service = GitService()
    
    async def execute(
        self,
        project_id: str,
        project_config: Dict,
        task_id: str,
        progress_callback=None
    ) -> Dict:
        """
        执行完整的测试生成流程
        
        Args:
            project_id: 项目ID
            project_config: 项目配置
            task_id: 任务ID
            progress_callback: 进度回调函数
            
        Returns:
            任务执行结果
        """
        logger.info(f"🚀 开始执行测试生成任务: {task_id}")
        
        result = {
            'success': False,
            'commit_hash': None,
            'test_files': [],
            'test_results': {},
            'coverage': {},
            'error': None
        }
        
        try:
            # 1. 克隆/更新代码仓库
            await self._update_progress(progress_callback, 10, "CLONING", "克隆代码仓库...")
            repo_path = await self.git_service.clone_or_pull(
                project_id,
                project_config['git_url'],
                project_config['git_branch']
            )
            
            commit_info = await self.git_service.get_commit_info(repo_path)
            result['commit_hash'] = commit_info['hash']
            
            logger.info(f"📁 代码仓库: {repo_path}")
            
            # 2. 分析代码
            await self._update_progress(progress_callback, 30, "ANALYZING", "分析代码结构...")
            analyzer = get_analyzer(project_config['language'])
            
            source_dir = Path(repo_path) / project_config.get('source_directory', '.')
            analysis_results = analyzer.analyze_directory(str(source_dir))
            
            logger.info(f"🔍 发现 {len(analysis_results)} 个文件待测试")
            
            # 3. 生成测试（智能跳过已有测试）
            await self._update_progress(progress_callback, 50, "GENERATING", "检查并生成测试代码...")
            test_generator = get_test_generator(
                project_config['language'],
                project_config.get('ai_provider', 'openai'),
                repo_path
            )
            
            generated_tests = []
            existing_tests = []
            test_dir = Path(repo_path) / project_config.get('test_directory', 'tests')
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # 为每个源文件生成测试（一个源文件一个测试文件，包含所有函数的测试）
            test_metadata = {}  # 存储测试元数据，用于后续修复
            max_concurrent = project_config.get('max_concurrent_generations', 10)  # 最大并发数
            
            # 按源文件分组准备测试任务
            test_tasks = []  # 每个任务对应一个源文件
            skipped_count = 0
            skip_existing = project_config.get('skip_existing_tests', True)
            
            for file_analysis in analysis_results:
                # 检查该源文件的测试文件是否已存在
                expected_test_file = self._get_expected_test_file_path(
                    test_dir,
                    file_analysis['file_path'],
                    project_config['language'],
                    project_config.get('test_framework')
                )
                
                if skip_existing and expected_test_file.exists():
                    # 测试文件已存在，跳过整个文件
                    if str(expected_test_file) not in existing_tests:
                        existing_tests.append(str(expected_test_file))
                    test_metadata[str(expected_test_file)] = {
                        'file_analysis': file_analysis,
                        'is_existing': True
                    }
                    skipped_count += 1
                    logger.info(f"⏭️  跳过已有测试: {expected_test_file.name}")
                else:
                    # 需要为该源文件生成新测试
                    test_tasks.append({
                        'file_analysis': file_analysis
                    })
            
            logger.info(f"📊 跳过 {skipped_count} 个已有测试，准备并发生成 {len(test_tasks)} 个新测试（并发数：{max_concurrent}）")
            
            # 并发生成新测试
            if test_tasks:
                total_files = len(test_tasks)
                
                # 更新进度：开始生成
                await self._update_progress(
                    progress_callback, 
                    50, 
                    "GENERATING", 
                    f"开始生成测试代码: 0/{total_files} 个文件"
                )
                
                generated_results = await self._generate_tests_concurrently(
                    test_tasks,
                    test_generator,
                    test_dir,
                    project_config,
                    max_concurrent,
                    progress_callback  # 传递进度回调
                )
                
                # 处理生成结果
                generated_count = 0
                for result_item in generated_results:
                    if result_item['success']:
                        test_file = result_item['test_file']
                        generated_tests.append(test_file)
                        test_metadata[test_file] = {
                            'file_analysis': result_item['file_analysis'],
                            'test_code': result_item['test_code'],
                            'is_existing': False
                        }
                        generated_count += 1
                        
                        # 更新详细进度
                        progress_percent = 50 + int((generated_count / total_files) * 15)  # 50-65%
                        await self._update_progress(
                            progress_callback,
                            progress_percent,
                            "GENERATING",
                            f"生成测试代码: {generated_count}/{total_files} 个文件"
                        )
                        
                        logger.info(f"✅ 生成测试 ({generated_count}/{total_files}): {Path(test_file).name}")
                    else:
                        source_file = Path(result_item['file_analysis']['file_path']).name
                        logger.warning(f"⚠️  为源文件 {source_file} 生成测试失败: {result_item['error']}")
            
            # 所有测试文件（新生成的 + 已存在的）
            all_test_files = generated_tests + existing_tests
            result['test_files'] = all_test_files
            logger.info(f"📝 新生成 {len(generated_tests)} 个测试，已有 {len(existing_tests)} 个测试，共 {len(all_test_files)} 个测试文件")
            
            # 4. 执行测试并自动修复失败的测试
            await self._update_progress(progress_callback, 68, "TESTING", "执行测试...")
            test_executor = get_test_executor(
                project_config['language'], 
                repo_path,
                project_config.get('test_framework')
            )
            
            # 首次执行测试
            test_results = test_executor.execute_tests(generated_tests)
            result['test_results'] = test_results
            
            logger.info(f"🧪 测试结果: {test_results['passed_count']}/{test_results['total']} 通过")
            
            # 5. 如果测试失败，尝试自动修复（如果启用）
            enable_auto_fix = project_config.get('enable_auto_fix', True)
            max_retry = project_config.get('max_test_fix_retries', 3)
            
            if enable_auto_fix and not test_results['passed'] and test_results['failed_count'] > 0:
                logger.info(f"🔧 检测到 {test_results['failed_count']} 个测试失败，开始自动修复...")
                
                fixed_tests = await self._fix_failed_tests(
                    test_executor,
                    test_generator,
                    generated_tests,
                    test_metadata,
                    test_results,
                    project_config,
                    max_retry,
                    progress_callback
                )
                
                if fixed_tests > 0:
                    logger.info(f"✅ 成功修复 {fixed_tests} 个测试")
                    # 重新执行所有测试
                    test_results = test_executor.execute_tests(generated_tests)
                    result['test_results'] = test_results
                    logger.info(f"🧪 修复后测试结果: {test_results['passed_count']}/{test_results['total']} 通过")
            elif not enable_auto_fix and test_results['failed_count'] > 0:
                logger.info(f"⚠️  自动修复功能已禁用，跳过测试修复")
            
            # 6. 收集覆盖率
            await self._update_progress(progress_callback, 85, "COLLECTING_COVERAGE", "收集覆盖率...")
            
            if test_results.get('coverage_file'):
                coverage_data = test_executor.collect_coverage(test_results['coverage_file'])
                result['coverage'] = coverage_data
                logger.info(f"📊 代码覆盖率: {coverage_data.get('line_coverage', 0)}%")
            
            # 7. 提交代码
            if project_config.get('auto_commit', True):
                await self._update_progress(progress_callback, 95, "COMMITTING", "提交测试代码...")
                
                branch_name = f"aitest/add-tests-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                commit_message = f"""Add unit tests generated by AI Test Agent

Generated {len(generated_tests)} test files
Coverage: {result['coverage'].get('line_coverage', 0):.2f}%

Task ID: {task_id}
"""
                
                try:
                    commit_hash = await self.git_service.commit_and_push(
                        repo_path,
                        generated_tests,
                        commit_message,
                        branch_name
                    )
                    
                    logger.info(f"✅ 代码已提交: {commit_hash[:8]}")
                    
                    # 创建PR（如果配置）
                    if project_config.get('create_pr', True):
                        await self.git_service.create_pull_request(
                            project_id,
                            branch_name,
                            "Add AI-generated unit tests",
                            commit_message,
                            project_config['git_branch']
                        )
                
                except Exception as e:
                    logger.warning(f"提交代码失败: {e}")
                    # 提交失败不影响整体成功
            
            # 8. 完成
            await self._update_progress(progress_callback, 100, "COMPLETED", "任务完成!")
            result['success'] = True
            
            logger.info(f"🎉 任务完成: {task_id}")
            return result
        
        except Exception as e:
            logger.error(f"❌ 任务执行失败: {e}")
            result['error'] = str(e)
            await self._update_progress(progress_callback, 0, "FAILED", f"失败: {e}")
            return result
    
    async def _generate_tests_concurrently(
        self,
        test_tasks: List[Dict],
        test_generator,
        test_dir: Path,
        project_config: Dict,
        max_concurrent: int,
        progress_callback=None
    ) -> List[Dict]:
        """
        并发生成多个测试（每个任务对应一个源文件）
        
        Args:
            test_tasks: 测试任务列表（每个任务包含一个源文件的所有函数）
            test_generator: 测试生成器
            test_dir: 测试目录
            project_config: 项目配置
            max_concurrent: 最大并发数
            progress_callback: 进度回调函数
            
        Returns:
            生成结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_test_for_file(task):
            """为一个源文件的所有函数生成测试（含语法验证和自动修复）"""
            async with semaphore:
                try:
                    file_analysis = task['file_analysis']
                    source_file = Path(file_analysis['file_path']).name
                    
                    # 使用线程池执行同步的AI调用（避免阻塞事件循环）
                    loop = asyncio.get_event_loop()
                    
                    # 生成测试代码并自动验证修复
                    def generate_and_validate_with_hybrid():
                        return test_generator.generate_and_validate(
                            file_analysis,
                            project_config['language'],
                            project_config['test_framework'],
                            test_dir=test_dir,
                            use_hybrid_mode=True,
                            max_fix_attempts=3  # 最多尝试修复3次
                        )
                    
                    result = await loop.run_in_executor(None, generate_and_validate_with_hybrid)
                    
                    # 检查生成和验证是否成功
                    if not result['success']:
                        error_msg = f"语法验证失败 (尝试 {result['attempts']} 次): {result['validation_errors']}"
                        logger.error(f"❌ {source_file}: {error_msg}")
                        return {
                            'success': False,
                            'file_analysis': file_analysis,
                            'error': error_msg,
                            'validation_errors': result['validation_errors']
                        }
                    
                    test_code = result['test_code']
                    attempts = result['attempts']
                    
                    if attempts > 1:
                        logger.info(f"✅ {source_file}: 经过 {attempts} 次修复后通过语法验证")
                    else:
                        logger.info(f"✅ {source_file}: 首次生成即通过语法验证")
                    
                    # 保存测试文件
                    test_file = self._save_test_file(
                        test_dir,
                        file_analysis['file_path'],
                        test_code,
                        project_config['language'],
                        project_config.get('test_framework')
                    )
                    
                    return {
                        'success': True,
                        'test_file': test_file,
                        'file_analysis': file_analysis,
                        'test_code': test_code,
                        'validation_attempts': attempts
                    }
                    
                except Exception as e:
                    logger.error(f"❌ 生成测试异常: {str(e)}")
                    return {
                        'success': False,
                        'file_analysis': task['file_analysis'],
                        'error': str(e)
                    }
        
        # 并发执行所有任务
        results = await asyncio.gather(*[generate_test_for_file(task) for task in test_tasks])
        return results
    
    def _get_expected_test_file_path(
        self,
        test_dir: Path,
        source_file: str,
        language: str,
        test_framework: str = None
    ) -> Path:
        """获取预期的测试文件路径（一个源文件对应一个测试文件）"""
        # 根据语言确定文件扩展名
        extensions = {
            'golang': '_test.go',
            'cpp': '_test.cpp',
            'c': '_test.c'
        }
        
        # 生成测试文件名：源文件名 + 测试后缀
        source_name = Path(source_file).stem
        test_file_name = f"{source_name}{extensions.get(language, '_test.txt')}"
        
        return test_dir / test_file_name
    
    def _save_test_file(
        self,
        test_dir: Path,
        source_file: str,
        test_code: str,
        language: str,
        test_framework: str = None
    ) -> str:
        """保存测试文件并自动修复"""
        test_file_path = self._get_expected_test_file_path(
            test_dir,
            source_file,
            language,
            test_framework
        )
        
        # 检查是否有大小写冲突的文件
        if test_file_path.exists():
            # 文件已存在，检查是否是大小写不同的重复
            existing_files = list(test_file_path.parent.glob(f"{test_file_path.stem}*{test_file_path.suffix}"))
            for existing_file in existing_files:
                if existing_file.name.lower() == test_file_path.name.lower() and existing_file != test_file_path:
                    logger.warning(f"⚠️  检测到大小写冲突的文件: {existing_file.name} vs {test_file_path.name}")
                    # 保留原文件，跳过新文件
                    return str(existing_file)
        
        # 修复包名（对于 Golang）
        if language == 'golang':
            test_code = self._fix_package_name(test_code, test_dir)
        
        # 写入测试代码
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        logger.debug(f"✅ 保存测试文件: {test_file_path.name}")
        return str(test_file_path)
    
    def _fix_package_name(self, test_code: str, test_dir: Path) -> str:
        """
        修复测试文件的包名
        
        使用同包测试策略：测试代码和源代码使用相同的 package
        不使用 _test 后缀
        """
        import re
        
        # 获取目录名作为包名（不添加 _test 后缀）
        dir_name = test_dir.name
        correct_package = dir_name  # ✅ 使用同包测试，不添加 _test
        
        # 查找并替换包名（移除 _test 后缀）
        package_match = re.search(r'^package\s+(\w+)', test_code, re.MULTILINE)
        if package_match:
            current_package = package_match.group(1)
            # 如果当前包名有 _test 后缀，移除它
            if current_package.endswith('_test'):
                test_code = re.sub(
                    r'^package\s+\w+_test',
                    f'package {correct_package}',
                    test_code,
                    count=1,
                    flags=re.MULTILINE
                )
                logger.debug(f"📝 修复包名为同包测试: {current_package} -> {correct_package}")
            elif current_package != correct_package:
                # 如果包名不匹配（但没有_test后缀），也修正
                test_code = re.sub(
                    r'^package\s+\w+',
                    f'package {correct_package}',
                    test_code,
                    count=1,
                    flags=re.MULTILINE
                )
                logger.debug(f"📝 修复包名: {current_package} -> {correct_package}")
        
        return test_code
    
    async def _fix_failed_tests(
        self,
        test_executor,
        test_generator,
        test_files: List[str],
        test_metadata: Dict,
        test_results: Dict,
        project_config: Dict,
        max_retry: int,
        progress_callback
    ) -> int:
        """
        自动修复失败的测试
        
        Args:
            test_executor: 测试执行器
            test_generator: 测试生成器
            test_files: 测试文件列表
            test_metadata: 测试元数据
            test_results: 测试结果
            project_config: 项目配置
            max_retry: 最大重试次数
            progress_callback: 进度回调
            
        Returns:
            成功修复的测试数量
        """
        fixed_count = 0
        retry_count = 0
        
        while retry_count < max_retry and test_results.get('failed_count', 0) > 0:
            retry_count += 1
            logger.info(f"🔄 第 {retry_count}/{max_retry} 次修复尝试")
            
            await self._update_progress(
                progress_callback,
                70 + retry_count * 3,
                "FIXING",
                f"修复失败的测试 (第{retry_count}次尝试)..."
            )
            
            # 逐个测试文件执行，找出失败的测试
            for test_file in test_files:
                try:
                    # 单独执行这个测试文件
                    single_result = test_executor.execute_tests([test_file])
                    
                    # 如果这个测试失败了
                    if not single_result['passed'] and single_result['failed_count'] > 0:
                        logger.info(f"🔍 分析失败测试: {test_file}")
                        
                        # 获取测试元数据
                        if test_file not in test_metadata:
                            logger.warning(f"⚠️  找不到测试元数据: {test_file}")
                            continue
                        
                        metadata = test_metadata[test_file]
                        
                        # 读取当前测试代码
                        with open(test_file, 'r', encoding='utf-8') as f:
                            current_test_code = f.read()
                        
                        # 使用AI修复测试
                        try:
                            fixed_test_code = test_generator.fix_test(
                                current_test_code,
                                single_result['output'],
                                metadata['file_analysis'],
                                project_config['language'],
                                project_config['test_framework']
                            )
                            
                            # 保存修复后的测试
                            with open(test_file, 'w', encoding='utf-8') as f:
                                f.write(fixed_test_code)
                            
                            # 更新元数据
                            metadata['test_code'] = fixed_test_code
                            
                            # 验证修复后的测试
                            verify_result = test_executor.execute_tests([test_file])
                            if verify_result['passed']:
                                logger.info(f"✅ 测试修复成功: {test_file}")
                                fixed_count += 1
                            else:
                                logger.warning(f"⚠️  测试修复后仍然失败: {test_file}")
                        
                        except Exception as e:
                            logger.error(f"❌ 修复测试失败: {test_file}, 错误: {e}")
                            continue
                
                except Exception as e:
                    logger.error(f"❌ 执行测试失败: {test_file}, 错误: {e}")
                    continue
            
            # 重新执行所有测试查看整体情况
            test_results = test_executor.execute_tests(test_files)
            logger.info(f"📊 当前测试状态: {test_results['passed_count']}/{test_results['total']} 通过")
            
            # 如果所有测试都通过了，提前退出
            if test_results['passed']:
                logger.info("🎉 所有测试都通过了！")
                break
        
        return fixed_count
    
    async def _update_progress(
        self,
        callback,
        progress: int,
        status: str,
        message: str
    ):
        """更新进度"""
        logger.info(f"[{progress}%] {status}: {message}")
        
        if callback:
            await callback(progress, status, message)

