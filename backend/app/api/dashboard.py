"""仪表板API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.database import get_db, Project, Task, CoverageReport
from app.database import TaskStatus


router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取仪表板统计数据"""
    
    # 项目总数
    project_count_result = await db.execute(
        select(func.count(Project.id))
    )
    total_projects = project_count_result.scalar()
    
    # 任务总数
    task_count_result = await db.execute(
        select(func.count(Task.id))
    )
    total_tasks = task_count_result.scalar()
    
    # 进行中的任务
    active_tasks_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.status.in_([
                TaskStatus.PENDING,
                TaskStatus.CLONING,
                TaskStatus.ANALYZING,
                TaskStatus.GENERATING,
                TaskStatus.TESTING,
                TaskStatus.COLLECTING_COVERAGE,
                TaskStatus.COMMITTING
            ])
        )
    )
    active_tasks = active_tasks_result.scalar()
    
    # 今日完成的任务
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_tasks_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= today
        )
    )
    today_completed_tasks = today_tasks_result.scalar()
    
    # 平均覆盖率
    avg_coverage_result = await db.execute(
        select(func.avg(CoverageReport.line_coverage))
    )
    avg_coverage = avg_coverage_result.scalar() or 0
    
    # 最近7天的任务趋势
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_tasks_result = await db.execute(
        select(
            func.date(Task.created_at).label('date'),
            func.count(Task.id).label('count')
        )
        .where(Task.created_at >= seven_days_ago)
        .group_by(func.date(Task.created_at))
        .order_by(func.date(Task.created_at))
    )
    recent_tasks = [
        {"date": str(row.date), "count": row.count}
        for row in recent_tasks_result
    ]
    
    return {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "today_completed_tasks": today_completed_tasks,
        "average_coverage": round(avg_coverage, 2),
        "recent_tasks_trend": recent_tasks
    }


@router.get("/recent-tasks")
async def get_recent_tasks(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取最近的任务"""
    result = await db.execute(
        select(Task)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    tasks = result.scalars().all()
    
    return [
        {
            "id": task.id,
            "project_id": task.project_id,
            "status": task.status,
            "progress": task.progress,
            "line_coverage": task.line_coverage,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        }
        for task in tasks
    ]

