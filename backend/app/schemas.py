"""Pydantic模型定义"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# 枚举类型
class Language(str, Enum):
    GOLANG = "golang"
    CPP = "cpp"
    C = "c"


class TaskStatus(str, Enum):
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


class TestFramework(str, Enum):
    GO_TEST = "go_test"
    GINKGO = "ginkgo"  # BDD测试框架
    GOOGLE_TEST = "google_test"
    CATCH2 = "catch2"
    CUNIT = "cunit"
    UNITY = "unity"


# 项目相关Schema
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    git_url: str
    git_branch: str = "main"
    language: Language
    test_framework: TestFramework
    source_directory: str = "."
    test_directory: str = "tests"
    coverage_threshold: float = 80.0
    auto_commit: bool = True
    create_pr: bool = True
    schedule_cron: Optional[str] = None
    ai_model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.3


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    git_branch: Optional[str] = None
    test_framework: Optional[TestFramework] = None
    source_directory: Optional[str] = None
    test_directory: Optional[str] = None
    coverage_threshold: Optional[float] = None
    auto_commit: Optional[bool] = None
    create_pr: Optional[bool] = None
    schedule_cron: Optional[str] = None
    enabled: Optional[bool] = None
    ai_model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    git_url: str
    git_branch: str
    language: Language
    test_framework: TestFramework
    source_directory: str
    test_directory: str
    coverage_threshold: float
    auto_commit: bool
    create_pr: bool
    schedule_cron: Optional[str]
    enabled: bool
    ai_model: str
    max_tokens: int
    temperature: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 任务相关Schema
class TaskResponse(BaseModel):
    id: str
    project_id: str
    status: TaskStatus
    progress: int
    commit_hash: Optional[str]
    branch: Optional[str]
    target_files: Optional[List[str]]
    generated_tests: Optional[List[str]]
    total_tests: int
    passed_tests: int
    failed_tests: int
    coverage_data: Optional[dict]
    line_coverage: Optional[float]
    branch_coverage: Optional[float]
    function_coverage: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TaskLogResponse(BaseModel):
    id: str
    task_id: str
    level: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CoverageReportResponse(BaseModel):
    id: str
    task_id: str
    project_id: str
    total_lines: int
    covered_lines: int
    line_coverage: float
    total_branches: int
    covered_branches: int
    branch_coverage: float
    total_functions: int
    covered_functions: int
    function_coverage: float
    files_coverage: dict
    html_report_path: Optional[str]
    json_report_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# 测试修复相关Schema
class TestFixRequest(BaseModel):
    """测试修复请求"""
    workspace_path: str = Field(..., description="项目工作空间路径，如 /app/workspace/a5db9f32-xxx")
    test_directory: str = Field(..., description="测试目录相对路径，如 internal/biz")
    language: Language = Field(Language.GOLANG, description="编程语言")
    test_framework: TestFramework = Field(TestFramework.GINKGO, description="测试框架")
    max_fix_attempts: int = Field(5, description="每个文件最大修复尝试次数，5次后仍失败则删除文件")
    auto_git_commit: bool = Field(False, description="是否自动执行 Git 提交和推送")
    git_username: str = Field("ut-agent", description="Git 用户名")
    git_branch_name: Optional[str] = Field(None, description="Git 分支名称（可选，默认自动生成）")
    git_commit_message: Optional[str] = Field(None, description="Git 提交信息（可选，默认自动生成）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workspace_path": "/app/workspace/a5db9f32-2f88-485e-9dd3-4232667918e3",
                "test_directory": "internal/biz",
                "language": "golang",
                "test_framework": "ginkgo",
                "max_fix_attempts": 5,
                "auto_git_commit": True,
                "git_username": "ut-agent",
                "git_branch_name": "feat/fix-tests-ut-agent",
                "git_commit_message": "fix: 自动修复测试代码语法错误"
            }
        }


class TestFixFileResult(BaseModel):
    """单个测试文件修复结果"""
    file_path: str
    success: bool
    original_had_errors: bool
    fixed: bool
    attempts: int
    errors: List[str] = []


class GitOperationResult(BaseModel):
    """Git 操作结果"""
    success: bool
    branch: Optional[str] = None
    committed: bool = False
    pushed: bool = False
    message: str
    error: Optional[str] = None


class TestFixResponse(BaseModel):
    """测试修复响应"""
    success: bool
    total_files: int
    fixed_files: int
    failed_files: int
    skipped_files: int
    file_results: List[TestFixFileResult]
    message: str
    git_result: Optional[GitOperationResult] = None

