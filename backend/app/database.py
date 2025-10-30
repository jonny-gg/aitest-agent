"""数据库配置和模型"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, JSON, Enum
from datetime import datetime
from typing import Optional, Any
import enum

from app.config import get_settings


# 创建异步引擎
engine = create_async_engine(
    get_settings().database_url,
    echo=True,
    future=True
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Base类
class Base(DeclarativeBase):
    pass


# 枚举类型
class Language(str, enum.Enum):
    GOLANG = "golang"
    CPP = "cpp"
    C = "c"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    COLLECTING_COVERAGE = "collecting_coverage"
    COMMITTING = "committing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestFramework(str, enum.Enum):
    # Golang
    GO_TEST = "go_test"
    GINKGO = "ginkgo"  # BDD测试框架，适合Kratos等有依赖注入的场景
    # C++
    GOOGLE_TEST = "google_test"
    CATCH2 = "catch2"
    # C
    CUNIT = "cunit"
    UNITY = "unity"


# 模型定义
class Project(Base):
    """项目模型"""
    __tablename__ = "projects"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Git配置
    git_url: Mapped[str] = mapped_column(String(500), nullable=False)
    git_branch: Mapped[str] = mapped_column(String(100), default="main")
    
    # 语言和框架
    language: Mapped[Language] = mapped_column(Enum(Language), nullable=False)
    test_framework: Mapped[TestFramework] = mapped_column(Enum(TestFramework), nullable=False)
    
    # 路径配置
    # source_directory 支持字符串或数组（JSON类型）
    # 字符串: "internal/biz" (单目录)
    # 数组: ["internal/biz", "pkg"] (多目录递归)
    source_directory: Mapped[Any] = mapped_column(JSON, default=".")
    test_directory: Mapped[str] = mapped_column(String(255), default="tests")
    
    # 测试配置
    coverage_threshold: Mapped[float] = mapped_column(Float, default=80.0)
    auto_commit: Mapped[bool] = mapped_column(Boolean, default=True)
    create_pr: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # 调度配置
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # AI配置
    ai_model: Mapped[str] = mapped_column(String(100), default="gpt-4")
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000)
    temperature: Mapped[float] = mapped_column(Float, default=0.3)
    
    # 元数据
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """测试任务模型"""
    __tablename__ = "tasks"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # 状态
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    
    # Git信息
    commit_hash: Mapped[Optional[str]] = mapped_column(String(40))
    branch: Mapped[Optional[str]] = mapped_column(String(100))
    
    # 任务详情
    target_files: Mapped[Optional[list]] = mapped_column(JSON)
    generated_tests: Mapped[Optional[list]] = mapped_column(JSON)
    
    # 执行结果
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0)
    
    # 覆盖率数据
    coverage_data: Mapped[Optional[dict]] = mapped_column(JSON)
    line_coverage: Mapped[Optional[float]] = mapped_column(Float)
    branch_coverage: Mapped[Optional[float]] = mapped_column(Float)
    function_coverage: Mapped[Optional[float]] = mapped_column(Float)
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class CoverageReport(Base):
    """覆盖率报告模型"""
    __tablename__ = "coverage_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # 覆盖率统计
    total_lines: Mapped[int] = mapped_column(Integer, default=0)
    covered_lines: Mapped[int] = mapped_column(Integer, default=0)
    line_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    
    total_branches: Mapped[int] = mapped_column(Integer, default=0)
    covered_branches: Mapped[int] = mapped_column(Integer, default=0)
    branch_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    
    total_functions: Mapped[int] = mapped_column(Integer, default=0)
    covered_functions: Mapped[int] = mapped_column(Integer, default=0)
    function_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # 文件级覆盖率
    files_coverage: Mapped[dict] = mapped_column(JSON)
    
    # 报告路径
    html_report_path: Mapped[Optional[str]] = mapped_column(String(500))
    json_report_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TaskLog(Base):
    """任务日志模型"""
    __tablename__ = "task_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    level: Mapped[str] = mapped_column(String(20))  # INFO, WARNING, ERROR
    message: Mapped[str] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# 数据库初始化
async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 获取数据库会话
async def get_db():
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

