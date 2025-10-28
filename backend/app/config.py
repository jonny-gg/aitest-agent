"""应用配置"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-this-in-production"
    
    # 数据库配置
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "aitest"
    postgres_user: str = "aitest"
    postgres_password: str = "aitest123"
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    # Celery配置
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # AI配置
    ai_provider: str = "openai"  # openai, anthropic, local
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_base_url: str = "https://api.openai.com/v1"
    
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-sonnet-20240229"
    
    local_model_url: str = "http://localhost:8080/v1"
    local_model_name: str = "codellama"
    
    # Git配置
    git_username: str = ""
    git_token: str = ""
    git_default_branch: str = "main"
    
    # 工作目录
    workspace_dir: str = "/app/workspace"
    reports_dir: str = "/app/reports"
    
    # 日志
    log_level: str = "INFO"
    
    # 覆盖率阈值
    default_coverage_threshold: float = 80.0
    
    # 测试修复配置
    max_test_fix_retries: int = 3  # AI自动修复测试的最大重试次数
    enable_auto_fix: bool = True  # 是否启用自动修复功能
    max_concurrent_generations: int = 10  # 并发生成测试的最大数量
    skip_existing_tests: bool = True  # 是否跳过已存在的测试文件，直接运行和修复
    
    # 并发配置
    max_concurrent_tasks: int = 5
    celery_worker_concurrency: int = 4
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

