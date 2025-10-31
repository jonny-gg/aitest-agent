"""Celery Worker配置"""
from celery import Celery
from loguru import logger
import asyncio
from datetime import datetime

from app.config import get_settings
from app.database import AsyncSessionLocal, Task, TaskLog, CoverageReport, Project, TaskStatus
from app.agent.test_agent import TestGenerationAgent
from uuid import uuid4


settings = get_settings()

# 创建Celery应用
celery_app = Celery(
    "aitest_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.celery_task_time_limit,  # 从环境变量读取超时时间
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    worker_concurrency=settings.celery_worker_concurrency,  # 从环境变量读取并发数
)


@celery_app.task(bind=True, name="run_test_generation_task")
def run_test_generation_task(self, task_id: str):
    """
    执行测试生成任务
    
    Args:
        task_id: 任务ID
    """
    logger.info(f"🚀 开始执行任务: {task_id}")
    
    # 在事件循环中运行异步任务
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_execute_task(task_id, self))
    
    return result


async def _execute_task(task_id: str, celery_task):
    """执行任务的异步函数"""
    async with AsyncSessionLocal() as db:
        try:
            # 获取任务信息
            from sqlalchemy import select
            
            result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return {"error": "Task not found"}
            
            # 获取项目配置
            result = await db.execute(
                select(Project).where(Project.id == task.project_id)
            )
            project = result.scalar_one_or_none()
            
            if not project:
                logger.error(f"项目不存在: {task.project_id}")
                return {"error": "Project not found"}
            
            # 更新任务状态
            task.status = TaskStatus.CLONING
            task.started_at = datetime.utcnow()
            await db.commit()
            
            # 创建进度回调
            async def progress_callback(progress: int, status: str, message: str):
                # 更新任务进度
                task.progress = progress
                task.status = TaskStatus[status] if status in TaskStatus.__members__ else task.status
                
                # 添加日志
                log = TaskLog(
                    id=str(uuid4()),
                    task_id=task_id,
                    level="INFO",
                    message=message
                )
                db.add(log)
                await db.commit()
                
                # 更新Celery任务状态
                celery_task.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'status': status, 'message': message}
                )
            
            # 执行测试生成
            agent = TestGenerationAgent()
            
            project_config = {
                'git_url': project.git_url,
                'git_branch': project.git_branch,
                'language': project.language.value,
                'test_framework': project.test_framework.value,
                'source_directory': project.source_directory,
                'test_directory': project.test_directory,
                'auto_commit': project.auto_commit,
                'create_pr': project.create_pr,
                'ai_provider': settings.ai_provider,
                'max_test_fix_retries': settings.max_test_fix_retries,
                'enable_auto_fix': settings.enable_auto_fix,
                'max_concurrent_generations': settings.max_concurrent_generations,
                'skip_existing_tests': settings.skip_existing_tests
            }
            
            result = await agent.execute(
                task.project_id,
                project_config,
                task_id,
                progress_callback
            )
            
            # 更新任务结果
            if result['success']:
                task.status = TaskStatus.COMPLETED
                task.commit_hash = result['commit_hash']
                task.generated_tests = result['test_files']
                task.total_tests = result['test_results'].get('total', 0)
                task.passed_tests = result['test_results'].get('passed_count', 0)
                task.failed_tests = result['test_results'].get('failed_count', 0)
                task.line_coverage = result['coverage'].get('line_coverage')
                task.branch_coverage = result['coverage'].get('branch_coverage')
                task.function_coverage = result['coverage'].get('function_coverage')
                task.coverage_data = result['coverage']
                task.completed_at = datetime.utcnow()
                
                # 保存覆盖率报告
                if result['coverage']:
                    coverage_report = CoverageReport(
                        id=str(uuid4()),
                        task_id=task_id,
                        project_id=task.project_id,
                        total_lines=0,  # 需要从coverage_data中提取
                        covered_lines=0,
                        line_coverage=result['coverage'].get('line_coverage', 0.0),
                        total_branches=0,
                        covered_branches=0,
                        branch_coverage=result['coverage'].get('branch_coverage', 0.0),
                        total_functions=0,
                        covered_functions=0,
                        function_coverage=result['coverage'].get('function_coverage', 0.0),
                        files_coverage=result['coverage'].get('files_coverage', {})
                    )
                    db.add(coverage_report)
                
                logger.info(f"✅ 任务完成: {task_id}")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = result.get('error')
                task.completed_at = datetime.utcnow()
                
                logger.error(f"❌ 任务失败: {task_id}")
            
            await db.commit()
            
            return {
                'task_id': task_id,
                'success': result['success'],
                'test_files': result['test_files'],
                'coverage': result['coverage']
            }
        
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            
            # 更新任务为失败状态
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await db.commit()
            
            return {"error": str(e)}


@celery_app.task(bind=True, name="run_test_fix_task")
def run_test_fix_task(self, task_id: str, fix_config: dict):
    """
    执行测试修复任务
    
    Args:
        task_id: 任务ID
        fix_config: 修复配置
    """
    logger.info(f"🔧 开始执行测试修复任务: {task_id}")
    
    # 在事件循环中运行异步任务
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_execute_fix_task(task_id, fix_config, self))
    
    return result


async def _execute_fix_task(task_id: str, fix_config: dict, celery_task):
    """执行测试修复的异步函数"""
    from app.services.test_fixer import TestFixer
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取任务信息
            from sqlalchemy import select
            
            result = await db.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return {"error": "Task not found"}
            
            # 更新任务状态
            task.status = TaskStatus.GENERATING  # 使用 GENERATING 状态表示修复中
            task.started_at = datetime.utcnow()
            await db.commit()
            
            # 创建进度回调
            async def progress_callback(progress: int, status: str, message: str):
                # 更新任务进度
                task.progress = progress
                if status in TaskStatus.__members__:
                    task.status = TaskStatus[status]
                
                # 添加日志
                log = TaskLog(
                    id=str(uuid4()),
                    task_id=task_id,
                    level="INFO",
                    message=message
                )
                db.add(log)
                await db.commit()
                
                # 更新Celery任务状态
                celery_task.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'status': status, 'message': message}
                )
            
            # 创建修复器
            fixer = TestFixer(
                language=fix_config['language'],
                test_framework=fix_config['test_framework']
            )
            
            await progress_callback(10, "GENERATING", "开始扫描测试文件...")
            
            # 执行异步并发修复
            fix_result = await fixer.fix_tests_in_directory_async(
                workspace_path=fix_config['workspace_path'],
                test_directory=fix_config['test_directory'],
                max_fix_attempts=fix_config.get('max_fix_attempts', 5),
                max_concurrent=10,
                auto_git_commit=fix_config.get('auto_git_commit', False),
                git_username=fix_config.get('git_username', 'ut-agent'),
                git_branch_name=fix_config.get('git_branch_name'),
                git_commit_message=fix_config.get('git_commit_message')
            )
            
            await progress_callback(90, "GENERATING", "修复完成，准备保存结果...")
            
            # 更新任务结果
            if fix_result['success']:
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.total_tests = fix_result['total_files']
                task.passed_tests = fix_result['fixed_files']
                task.failed_tests = fix_result['failed_files']
                
                # 保存详细结果到 coverage_data 字段
                task.coverage_data = {
                    'fix_results': fix_result,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if fix_result.get('git_result'):
                    task.branch = fix_result['git_result'].get('branch')
                    task.commit_hash = 'fixed'  # 标记为已修复
                
                task.completed_at = datetime.utcnow()
                
                logger.info(f"✅ 测试修复任务完成: {task_id}")
                logger.info(f"   总文件: {fix_result['total_files']}")
                logger.info(f"   已修复: {fix_result['fixed_files']}")
                logger.info(f"   失败: {fix_result['failed_files']}")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = fix_result.get('message', '修复失败')
                task.completed_at = datetime.utcnow()
                
                logger.error(f"❌ 测试修复任务失败: {task_id}")
            
            await db.commit()
            
            return {
                'task_id': task_id,
                'success': fix_result['success'],
                'result': fix_result
            }
        
        except Exception as e:
            logger.error(f"测试修复任务执行异常: {e}", exc_info=True)
            
            # 更新任务为失败状态
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await db.commit()
            
            return {"error": str(e)}


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks():
    """清理旧任务（定时任务）"""
    logger.info("🧹 清理旧任务...")
    # TODO: 实现清理逻辑
    return {"message": "Cleanup completed"}


# 定时任务配置
celery_app.conf.beat_schedule = {
    'cleanup-every-day': {
        'task': 'cleanup_old_tasks',
        'schedule': 86400.0,  # 每天执行一次
    },
}

