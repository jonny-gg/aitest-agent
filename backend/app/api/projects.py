"""项目管理API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import uuid4

from app.database import get_db, Project, Task
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, TaskResponse


router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新项目"""
    project = Project(
        id=str(uuid4()),
        name=project_data.name,
        description=project_data.description,
        git_url=project_data.git_url,
        git_branch=project_data.git_branch,
        language=project_data.language,
        test_framework=project_data.test_framework,
        source_directory=project_data.source_directory,
        test_directory=project_data.test_directory,
        coverage_threshold=project_data.coverage_threshold,
        auto_commit=project_data.auto_commit,
        create_pr=project_data.create_pr,
        schedule_cron=project_data.schedule_cron,
        ai_model=project_data.ai_model,
        max_tokens=project_data.max_tokens,
        temperature=project_data.temperature
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取项目列表"""
    result = await db.execute(
        select(Project)
        .offset(skip)
        .limit(limit)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取项目详情"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新项目"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 更新字段
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除项目"""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """为项目创建测试任务"""
    from app.worker import run_test_generation_task
    
    # 验证项目存在
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 创建任务
    task = Task(
        id=str(uuid4()),
        project_id=project_id,
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # 异步执行任务
    run_test_generation_task.delay(task.id)
    
    return task


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def list_project_tasks(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取项目的任务列表"""
    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return tasks

