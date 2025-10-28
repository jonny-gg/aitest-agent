"""Git操作服务"""
import os
import git
from typing import Optional
from loguru import logger
from pathlib import Path

from app.config import get_settings


class GitService:
    """Git服务类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.workspace_dir = Path(self.settings.workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_repo_path(self, project_id: str) -> Path:
        """获取仓库本地路径"""
        return self.workspace_dir / project_id
    
    def _get_auth_url(self, git_url: str) -> str:
        """添加认证信息到Git URL"""
        if not self.settings.git_username or not self.settings.git_token:
            return git_url
        
        # 处理HTTPS URL
        if git_url.startswith('https://'):
            parts = git_url.replace('https://', '').split('/', 1)
            if len(parts) == 2:
                host, path = parts
                return f"https://{self.settings.git_username}:{self.settings.git_token}@{host}/{path}"
        
        return git_url
    
    async def clone_or_pull(
        self,
        project_id: str,
        git_url: str,
        branch: str = "main"
    ) -> str:
        """
        克隆或更新Git仓库
        
        Args:
            project_id: 项目ID
            git_url: Git仓库URL
            branch: 分支名称
            
        Returns:
            仓库本地路径
        """
        repo_path = self._get_repo_path(project_id)
        auth_url = self._get_auth_url(git_url)
        
        try:
            if repo_path.exists():
                logger.info(f"更新仓库: {repo_path}")
                repo = git.Repo(repo_path)
                
                # 切换到指定分支
                repo.git.checkout(branch)
                
                # 拉取最新代码
                origin = repo.remotes.origin
                origin.pull(branch)
                
                logger.info(f"✅ 仓库更新成功: {repo_path}")
            else:
                logger.info(f"克隆仓库: {git_url} -> {repo_path}")
                repo = git.Repo.clone_from(
                    auth_url,
                    repo_path,
                    branch=branch,
                    depth=1  # 浅克隆，提高速度
                )
                logger.info(f"✅ 仓库克隆成功: {repo_path}")
            
            # 获取最新commit hash
            commit_hash = repo.head.commit.hexsha
            logger.info(f"当前commit: {commit_hash}")
            
            return str(repo_path)
            
        except Exception as e:
            logger.error(f"Git操作失败: {e}")
            raise
    
    async def create_branch(
        self,
        repo_path: str,
        branch_name: str
    ) -> None:
        """
        创建新分支
        
        Args:
            repo_path: 仓库路径
            branch_name: 新分支名称
        """
        try:
            repo = git.Repo(repo_path)
            
            # 检查分支是否已存在
            if branch_name in repo.heads:
                logger.warning(f"分支已存在: {branch_name}")
                repo.git.checkout(branch_name)
            else:
                # 创建并切换到新分支
                repo.git.checkout('-b', branch_name)
                logger.info(f"✅ 创建新分支: {branch_name}")
        
        except Exception as e:
            logger.error(f"创建分支失败: {e}")
            raise
    
    async def commit_and_push(
        self,
        repo_path: str,
        files: list[str],
        commit_message: str,
        branch_name: Optional[str] = None
    ) -> str:
        """
        提交并推送代码
        
        Args:
            repo_path: 仓库路径
            files: 要提交的文件列表
            commit_message: 提交信息
            branch_name: 分支名称（可选，如果提供则创建新分支）
            
        Returns:
            commit hash
        """
        try:
            repo = git.Repo(repo_path)
            
            # 如果指定了分支名，创建新分支
            if branch_name:
                await self.create_branch(repo_path, branch_name)
            
            # 添加文件到暂存区
            for file_path in files:
                repo.index.add([file_path])
            
            logger.info(f"添加 {len(files)} 个文件到暂存区")
            
            # 检查是否有变更
            if not repo.index.diff("HEAD"):
                logger.warning("没有需要提交的变更")
                return repo.head.commit.hexsha
            
            # 提交
            commit = repo.index.commit(commit_message)
            logger.info(f"✅ 提交成功: {commit.hexsha[:8]}")
            
            # 推送到远程
            current_branch = repo.active_branch.name
            origin = repo.remotes.origin
            
            # 配置推送URL（包含认证）
            if self.settings.git_username and self.settings.git_token:
                push_url = self._get_auth_url(repo.remotes.origin.url)
                origin.set_url(push_url)
            
            origin.push(current_branch)
            logger.info(f"✅ 推送成功: {current_branch}")
            
            return commit.hexsha
            
        except Exception as e:
            logger.error(f"提交推送失败: {e}")
            raise
    
    async def get_commit_info(self, repo_path: str) -> dict:
        """
        获取当前commit信息
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            commit信息字典
        """
        try:
            repo = git.Repo(repo_path)
            commit = repo.head.commit
            
            return {
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat(),
                "branch": repo.active_branch.name
            }
        except Exception as e:
            logger.error(f"获取commit信息失败: {e}")
            raise
    
    async def create_pull_request(
        self,
        project_id: str,
        branch_name: str,
        title: str,
        description: str,
        base_branch: str = "main"
    ) -> Optional[str]:
        """
        创建Pull Request（需要GitHub/GitLab API）
        
        这里只是示例，实际需要集成GitHub/GitLab API
        """
        logger.info(f"创建PR: {branch_name} -> {base_branch}")
        logger.info(f"标题: {title}")
        logger.info(f"描述: {description}")
        
        # TODO: 实现GitHub/GitLab API集成
        # 使用 PyGithub 或 python-gitlab 库
        
        return None

