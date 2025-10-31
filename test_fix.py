#!/usr/bin/env python3
"""
AI Test Agent - 测试修复客户端

使用异步 API 提交测试修复任务，自动修复语法错误。

功能：
- 自动修复语法错误
- 清理 markdown 标记残留
- 修复括号不匹配
- 异步并发处理
- 实时进度显示

使用方式：
    python test_fix.py
"""
import requests
import time
import sys
from typing import Optional


class AsyncTestFixClient:
    """异步测试修复客户端"""
    
    def __init__(self, api_base: str = "http://localhost:8000/api"):
        self.api_base = api_base
    
    def submit_fix_task(
        self,
        workspace_path: str,
        test_directory: str,
        language: str = "golang",
        test_framework: str = "ginkgo",
        max_fix_attempts: int = 5,
        auto_git_commit: bool = False,
        git_username: str = "ut-agent",
        git_branch_name: Optional[str] = None,
        git_commit_message: Optional[str] = None
    ) -> Optional[str]:
        """
        提交测试修复任务
        
        Returns:
            任务ID，如果提交失败返回 None
        """
        url = f"{self.api_base}/tasks/fix-tests"
        
        payload = {
            "workspace_path": workspace_path,
            "test_directory": test_directory,
            "language": language,
            "test_framework": test_framework,
            "max_fix_attempts": max_fix_attempts,
            "auto_git_commit": auto_git_commit,
            "git_username": git_username
        }
        
        if git_branch_name:
            payload["git_branch_name"] = git_branch_name
        if git_commit_message:
            payload["git_commit_message"] = git_commit_message
        
        print("\n" + "="*70)
        print("🚀 提交测试修复任务")
        print("="*70)
        print(f"工作空间: {workspace_path}")
        print(f"测试目录: {test_directory}")
        print(f"语言: {language}")
        print(f"框架: {test_framework}")
        print(f"最大修复次数: {max_fix_attempts}")
        print(f"自动提交: {auto_git_commit}")
        print()
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data['id']
            
            print(f"✅ 任务已提交成功!")
            print(f"   任务ID: {task_id}")
            print(f"   状态: {task_data['status']}")
            print(f"   进度: {task_data['progress']}%")
            print()
            
            return task_id
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 提交任务失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   错误详情: {error_detail}")
                except:
                    print(f"   响应内容: {e.response.text}")
            return None
    
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        查询任务状态
        
        Returns:
            任务信息字典，如果查询失败返回 None
        """
        url = f"{self.api_base}/tasks/{task_id}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 查询任务状态失败: {e}")
            return None
    
    def get_task_logs(self, task_id: str) -> list:
        """
        获取任务日志
        
        Returns:
            日志列表
        """
        url = f"{self.api_base}/tasks/{task_id}/logs"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取任务日志失败: {e}")
            return []
    
    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 5,
        show_logs: bool = True
    ) -> bool:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            show_logs: 是否显示日志
        
        Returns:
            任务是否成功完成
        """
        print("="*70)
        print("⏳ 等待任务完成...")
        print("="*70)
        print(f"任务ID: {task_id}")
        print(f"轮询间隔: {poll_interval}秒")
        print()
        
        last_progress = -1
        last_log_count = 0
        
        while True:
            # 查询任务状态
            task_info = self.get_task_status(task_id)
            if not task_info:
                print("❌ 无法获取任务状态")
                return False
            
            status = task_info['status']
            progress = task_info['progress']
            
            # 显示进度（仅当有变化时）
            if progress != last_progress:
                print(f"📊 进度: {progress}% | 状态: {status}")
                last_progress = progress
            
            # 显示新日志
            if show_logs:
                logs = self.get_task_logs(task_id)
                new_logs = logs[last_log_count:]
                for log in new_logs:
                    timestamp = log['created_at'].split('T')[1].split('.')[0]
                    print(f"   [{timestamp}] {log['message']}")
                last_log_count = len(logs)
            
            # 检查任务是否完成
            if status == 'completed':
                print()
                print("="*70)
                print("✅ 任务完成!")
                print("="*70)
                self._print_task_results(task_info)
                return True
            
            elif status == 'failed':
                print()
                print("="*70)
                print("❌ 任务失败!")
                print("="*70)
                error_msg = task_info.get('error_message', '未知错误')
                print(f"错误信息: {error_msg}")
                return False
            
            elif status == 'cancelled':
                print()
                print("="*70)
                print("⚠️ 任务已取消")
                print("="*70)
                return False
            
            # 等待下一次轮询
            time.sleep(poll_interval)
    
    def _print_task_results(self, task_info: dict):
        """打印任务结果"""
        print()
        print("📊 修复统计:")
        print(f"   总文件数: {task_info.get('total_tests', 0)}")
        print(f"   已修复: {task_info.get('passed_tests', 0)}")
        print(f"   失败: {task_info.get('failed_tests', 0)}")
        
        # 显示详细结果
        coverage_data = task_info.get('coverage_data')
        if coverage_data and 'fix_results' in coverage_data:
            fix_results = coverage_data['fix_results']
            print()
            print(f"   跳过: {fix_results.get('skipped_files', 0)}")
            print(f"   成功率: {fix_results.get('success', False)}")
            
            if fix_results.get('git_result'):
                git_result = fix_results['git_result']
                print()
                print("📝 Git 操作:")
                print(f"   分支: {git_result.get('branch', 'N/A')}")
                print(f"   已提交: {git_result.get('committed', False)}")
                print(f"   已推送: {git_result.get('pushed', False)}")
        
        print()


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🤖 AI Test Agent - 异步测试修复")
    print("="*70)
    print()
    
    # 配置参数（可以根据需要修改）
    workspace_path = input("请输入工作空间路径 [例: /app/workspace/a5db9f32-xxx]: ").strip()
    if not workspace_path:
        print("❌ 工作空间路径不能为空")
        return 1
    
    test_directory = input("请输入测试目录 [例: internal/biz]: ").strip()
    if not test_directory:
        print("❌ 测试目录不能为空")
        return 1
    
    language = input("请输入编程语言 [golang]: ").strip() or "golang"
    test_framework = input("请输入测试框架 [ginkgo]: ").strip() or "ginkgo"
    
    auto_git_commit_input = input("是否自动 Git 提交? [y/N]: ").strip().lower()
    auto_git_commit = auto_git_commit_input == 'y'
    
    api_base = input("请输入 API 地址 [http://localhost:8000/api]: ").strip() or "http://localhost:8000/api"
    
    # 创建客户端
    client = AsyncTestFixClient(api_base=api_base)
    
    # 提交任务
    task_id = client.submit_fix_task(
        workspace_path=workspace_path,
        test_directory=test_directory,
        language=language,
        test_framework=test_framework,
        max_fix_attempts=5,
        auto_git_commit=auto_git_commit
    )
    
    if not task_id:
        return 1
    
    # 询问是否等待完成
    wait_input = input("是否等待任务完成? [Y/n]: ").strip().lower()
    if wait_input == 'n':
        print()
        print("💡 提示:")
        print(f"   可以通过以下命令查询任务状态:")
        print(f"   curl {api_base}/tasks/{task_id}")
        print()
        print(f"   或访问: {api_base}/tasks/{task_id}")
        return 0
    
    # 等待任务完成
    success = client.wait_for_completion(task_id, poll_interval=5, show_logs=True)
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

