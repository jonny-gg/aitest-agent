"""任务管理API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db, Task, TaskLog, CoverageReport
from app.schemas import (
    TaskResponse, 
    TaskLogResponse, 
    CoverageReportResponse,
    TestFixRequest,
    TestFixResponse
)


router = APIRouter()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """取消任务"""
    from app.worker import celery_app
    
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 撤销Celery任务
    celery_app.control.revoke(task_id, terminate=True)
    
    # 更新任务状态
    from app.database import TaskStatus
    task.status = TaskStatus.CANCELLED
    await db.commit()
    
    return {"message": "Task cancelled successfully"}


@router.get("/{task_id}/logs", response_model=List[TaskLogResponse])
async def get_task_logs(
    task_id: str,
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """获取任务日志"""
    result = await db.execute(
        select(TaskLog)
        .where(TaskLog.task_id == task_id)
        .offset(skip)
        .limit(limit)
        .order_by(TaskLog.created_at.asc())
    )
    logs = result.scalars().all()
    return logs


@router.get("/{task_id}/coverage", response_model=CoverageReportResponse)
async def get_task_coverage(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务覆盖率报告"""
    result = await db.execute(
        select(CoverageReport).where(CoverageReport.task_id == task_id)
    )
    coverage = result.scalar_one_or_none()
    
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage report not found")
    
    return coverage


@router.post("/fix-tests", response_model=TaskResponse)
async def fix_tests(
    fix_request: TestFixRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    提交测试修复任务（异步模式）
    
    立即返回任务ID，用户可通过 GET /api/tasks/{task_id} 查询进度。
    
    用于修复之前生成的测试文件中的语法错误，支持：
    - 清理 markdown 标记
    - 修复括号不匹配
    - 修复其他语法错误
    - 异步并发处理多个文件，大幅提升速度
    """
    from app.worker import run_test_fix_task
    from loguru import logger
    from uuid import uuid4
    
    logger.info(f"🔧 收到测试修复请求:")
    logger.info(f"   工作空间: {fix_request.workspace_path}")
    logger.info(f"   测试目录: {fix_request.test_directory}")
    logger.info(f"   语言: {fix_request.language}")
    logger.info(f"   框架: {fix_request.test_framework}")
    
    try:
        # 创建任务记录
        from app.database import TaskStatus
        
        task = Task(
            id=str(uuid4()),
            project_id="fix-task",  # 修复任务使用固定的 project_id
            status=TaskStatus.PENDING,
            progress=0
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        # 准备修复配置
        fix_config = {
            'workspace_path': fix_request.workspace_path,
            'test_directory': fix_request.test_directory,
            'language': fix_request.language.value,
            'test_framework': fix_request.test_framework.value,
            'max_fix_attempts': fix_request.max_fix_attempts,
            'auto_git_commit': fix_request.auto_git_commit,
            'git_username': fix_request.git_username,
            'git_branch_name': fix_request.git_branch_name,
            'git_commit_message': fix_request.git_commit_message
        }
        
        # 异步执行修复任务
        run_test_fix_task.delay(task.id, fix_config)
        
        logger.info(f"✅ 测试修复任务已创建: {task.id}")
        logger.info(f"   查询进度: GET /api/tasks/{task.id}")
        
        return task
        
    except Exception as e:
        logger.error(f"❌ 创建测试修复任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/fix-tests-sync", response_model=TestFixResponse)
async def fix_tests_sync(
    fix_request: TestFixRequest
):
    """
    同步修复测试代码（已废弃，建议使用异步版本）
    
    此接口会等待修复完成才返回，可能需要较长时间。
    建议使用 POST /api/tasks/fix-tests 异步接口。
    """
    from app.services.test_fixer import TestFixer
    from loguru import logger
    
    logger.warning("⚠️ 使用了同步修复接口，建议改用异步接口: POST /api/tasks/fix-tests")
    
    try:
        # 创建修复器
        fixer = TestFixer(
            language=fix_request.language,
            test_framework=fix_request.test_framework
        )
        
        # 执行异步并发修复
        result = await fixer.fix_tests_in_directory_async(
            workspace_path=fix_request.workspace_path,
            test_directory=fix_request.test_directory,
            max_fix_attempts=fix_request.max_fix_attempts,
            max_concurrent=10,  # 最大并发数：10个文件同时处理
            auto_git_commit=fix_request.auto_git_commit,
            git_username=fix_request.git_username,
            git_branch_name=fix_request.git_branch_name,
            git_commit_message=fix_request.git_commit_message
        )
        
        return TestFixResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ 测试修复失败: {e}")
        raise HTTPException(status_code=500, detail=f"修复失败: {str(e)}")

