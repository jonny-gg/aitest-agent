"""Git 操作辅助工具"""
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger
from datetime import datetime


class GitHelper:
    """Git 操作辅助类"""
    
    def __init__(self, repo_path: str, username: str = "ut-agent"):
        """
        初始化 Git 辅助工具
        
        Args:
            repo_path: Git 仓库路径
            username: Git 用户名
        """
        self.repo_path = Path(repo_path)
        self.username = username
        
        if not self.repo_path.exists():
            raise ValueError(f"仓库路径不存在: {repo_path}")
    
    def _run_git_command(self, command: list, check: bool = True) -> subprocess.CompletedProcess:
        """
        执行 git 命令
        
        Args:
            command: git 命令列表
            check: 是否检查返回码
            
        Returns:
            命令执行结果
        """
        full_command = ['git', '-C', str(self.repo_path)] + command
        logger.debug(f"执行命令: {' '.join(full_command)}")
        
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=False
        )
        
        if check and result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"Git 命令执行失败: {error_msg}")
            raise RuntimeError(f"Git 命令失败: {error_msg}")
        
        return result
    
    def configure_user(self, email: Optional[str] = None):
        """
        配置 Git 用户信息
        
        Args:
            email: 用户邮箱，默认为 {username}@example.com
        """
        if email is None:
            email = f"{self.username}@example.com"
        
        logger.info(f"📝 配置 Git 用户: {self.username} <{email}>")
        
        self._run_git_command(['config', 'user.name', self.username])
        self._run_git_command(['config', 'user.email', email])
    
    def get_current_branch(self) -> str:
        """获取当前分支名"""
        result = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        return result.stdout.strip()
    
    def create_branch(self, branch_name: Optional[str] = None) -> str:
        """
        创建新分支
        
        Args:
            branch_name: 分支名称，默认自动生成
            
        Returns:
            创建的分支名称
        """
        if branch_name is None:
            # 自动生成分支名: feat/fix-tests-ut-agent-20251017-123456
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            branch_name = f"feat/fix-tests-{self.username}-{timestamp}"
        
        logger.info(f"🌿 创建新分支: {branch_name}")
        
        # 创建并切换到新分支
        self._run_git_command(['checkout', '-b', branch_name])
        
        return branch_name
    
    def add_all_changes(self):
        """添加所有更改到暂存区"""
        logger.info("📦 添加所有更改到暂存区...")
        self._run_git_command(['add', '.'])
    
    def commit(self, message: Optional[str] = None) -> bool:
        """
        提交更改
        
        Args:
            message: 提交信息，默认自动生成
            
        Returns:
            是否有内容被提交
        """
        if message is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"fix: 自动修复测试代码语法错误 ({self.username} @ {timestamp})"
        
        logger.info(f"💾 提交更改: {message}")
        
        # 检查是否有内容需要提交
        status_result = self._run_git_command(['status', '--porcelain'])
        if not status_result.stdout.strip():
            logger.warning("⚠️ 没有需要提交的更改")
            return False
        
        self._run_git_command(['commit', '-m', message])
        return True
    
    def push(self, branch_name: Optional[str] = None, set_upstream: bool = True):
        """
        推送到远程仓库
        
        Args:
            branch_name: 分支名称，默认使用当前分支
            set_upstream: 是否设置上游分支
        """
        if branch_name is None:
            branch_name = self.get_current_branch()
        
        logger.info(f"🚀 推送到远程分支: {branch_name}")
        
        if set_upstream:
            self._run_git_command(['push', '-u', 'origin', branch_name])
        else:
            self._run_git_command(['push', 'origin', branch_name])
    
    def create_commit_and_push(
        self,
        branch_name: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> dict:
        """
        一键操作：创建分支、提交并推送
        
        Args:
            branch_name: 分支名称，默认自动生成
            commit_message: 提交信息，默认自动生成
            
        Returns:
            操作结果
        """
        try:
            # 配置用户信息
            self.configure_user()
            
            # 获取当前分支（在创建新分支之前）
            original_branch = self.get_current_branch()
            logger.info(f"📍 当前分支: {original_branch}")
            
            # 创建新分支
            new_branch = self.create_branch(branch_name)
            
            # 添加所有更改
            self.add_all_changes()
            
            # 提交
            committed = self.commit(commit_message)
            
            if not committed:
                logger.warning("⚠️ 没有更改需要提交，跳过推送")
                return {
                    'success': True,
                    'branch': new_branch,
                    'committed': False,
                    'pushed': False,
                    'message': '没有更改需要提交'
                }
            
            # 推送
            self.push(new_branch)
            
            logger.info(f"✅ Git 操作完成！分支: {new_branch}")
            
            return {
                'success': True,
                'branch': new_branch,
                'committed': True,
                'pushed': True,
                'message': f'成功创建分支 {new_branch} 并推送到远程'
            }
            
        except Exception as e:
            error_msg = f"Git 操作失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'branch': None,
                'committed': False,
                'pushed': False,
                'message': error_msg,
                'error': str(e)
            }
    
    def get_status(self) -> str:
        """获取 Git 状态"""
        result = self._run_git_command(['status'])
        return result.stdout

