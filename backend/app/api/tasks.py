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


@router.post("/fix-tests", response_model=TestFixResponse)
async def fix_tests(
    fix_request: TestFixRequest
):
    """
    修复已生成的测试代码（异步并发版本）
    
    用于修复之前生成的测试文件中的语法错误，支持：
    - 清理 markdown 标记
    - 修复括号不匹配
    - 修复其他语法错误
    - 异步并发处理多个文件，大幅提升速度
    """
    from app.services.test_fixer import TestFixer
    from loguru import logger
    
    logger.info(f"🔧 收到测试修复请求:")
    logger.info(f"   工作空间: {fix_request.workspace_path}")
    logger.info(f"   测试目录: {fix_request.test_directory}")
    logger.info(f"   语言: {fix_request.language}")
    logger.info(f"   框架: {fix_request.test_framework}")
    
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

