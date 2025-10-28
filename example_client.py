#!/usr/bin/env python3
"""
AI Test Agent 客户端示例
使用此脚本来触发和监控测试生成任务
"""

import requests
import time
import sys
from typing import Optional


class AITestAgentClient:
    """AI Test Agent 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
    
    def create_project(
        self,
        name: str,
        git_url: str,
        language: str,
        test_framework: str,
        git_branch: str = "main",
        coverage_threshold: float = 80.0,
        auto_commit: bool = True
    ) -> dict:
        """
        创建项目
        
        Args:
            name: 项目名称
            git_url: Git仓库URL
            language: 编程语言 (golang, cpp, c)
            test_framework: 测试框架 (go_test, google_test, cunit)
            git_branch: 分支名称
            coverage_threshold: 覆盖率阈值
            auto_commit: 是否自动提交
        
        Returns:
            项目信息字典
        """
        data = {
            "name": name,
            "git_url": git_url,
            "git_branch": git_branch,
            "language": language,
            "test_framework": test_framework,
            "coverage_threshold": coverage_threshold,
            "auto_commit": auto_commit,
            "create_pr": True
        }
        
        response = requests.post(f"{self.base_url}/projects", json=data)
        response.raise_for_status()
        
        project = response.json()
        print(f"✅ 项目创建成功: {project['name']} (ID: {project['id']})")
        return project
    
    def list_projects(self) -> list:
        """获取项目列表"""
        response = requests.get(f"{self.base_url}/projects")
        response.raise_for_status()
        return response.json()
    
    def get_project(self, project_id: str) -> dict:
        """获取项目详情"""
        response = requests.get(f"{self.base_url}/projects/{project_id}")
        response.raise_for_status()
        return response.json()
    
    def create_task(self, project_id: str) -> dict:
        """
        为项目创建测试生成任务
        
        Args:
            project_id: 项目ID
        
        Returns:
            任务信息字典
        """
        response = requests.post(f"{self.base_url}/projects/{project_id}/tasks")
        response.raise_for_status()
        
        task = response.json()
        print(f"🚀 任务已创建: {task['id']}")
        return task
    
    def get_task(self, task_id: str) -> dict:
        """获取任务详情"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def get_coverage(self, task_id: str) -> dict:
        """获取覆盖率报告"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}/coverage")
        response.raise_for_status()
        return response.json()
    
    def wait_for_task(self, task_id: str, interval: int = 5, timeout: int = 3600) -> dict:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            interval: 轮询间隔（秒）
            timeout: 超时时间（秒）
        
        Returns:
            最终任务状态
        """
        start_time = time.time()
        
        while True:
            # 检查超时
            if time.time() - start_time > timeout:
                print("❌ 任务执行超时")
                break
            
            # 获取任务状态
            task = self.get_task(task_id)
            status = task['status']
            progress = task['progress']
            
            # 显示进度
            print(f"[{progress}%] 状态: {status}")
            
            # 检查是否完成
            if status in ['completed', 'failed', 'cancelled']:
                return task
            
            # 等待
            time.sleep(interval)
        
        return self.get_task(task_id)
    
    def run_full_workflow(
        self,
        name: str,
        git_url: str,
        language: str,
        test_framework: str,
        **kwargs
    ) -> Optional[dict]:
        """
        完整工作流：创建项目 → 创建任务 → 等待完成 → 显示结果
        
        Args:
            name: 项目名称
            git_url: Git仓库URL
            language: 编程语言
            test_framework: 测试框架
            **kwargs: 其他项目参数
        
        Returns:
            任务结果，如果失败则返回None
        """
        try:
            # 1. 创建项目
            print("\n" + "="*60)
            print("步骤 1/4: 创建项目")
            print("="*60)
            project = self.create_project(
                name=name,
                git_url=git_url,
                language=language,
                test_framework=test_framework,
                **kwargs
            )
            project_id = project['id']
            
            # 2. 创建任务
            print("\n" + "="*60)
            print("步骤 2/4: 创建测试任务")
            print("="*60)
            task = self.create_task(project_id)
            task_id = task['id']
            
            # 3. 等待完成
            print("\n" + "="*60)
            print("步骤 3/4: 执行测试生成（这可能需要几分钟）")
            print("="*60)
            final_task = self.wait_for_task(task_id)
            
            # 4. 显示结果
            print("\n" + "="*60)
            print("步骤 4/4: 结果总结")
            print("="*60)
            
            if final_task['status'] == 'completed':
                print("✅ 任务完成!")
                print(f"\n📊 统计信息:")
                print(f"  - 生成测试文件: {len(final_task.get('generated_tests', []))} 个")
                print(f"  - 测试用例总数: {final_task.get('total_tests', 0)}")
                print(f"  - 通过测试: {final_task.get('passed_tests', 0)}")
                print(f"  - 失败测试: {final_task.get('failed_tests', 0)}")
                print(f"  - 行覆盖率: {final_task.get('line_coverage', 0):.2f}%")
                print(f"  - 分支覆盖率: {final_task.get('branch_coverage', 0):.2f}%")
                
                # 获取详细覆盖率
                try:
                    coverage = self.get_coverage(task_id)
                    print(f"\n📈 文件级覆盖率:")
                    for file_path, cov in coverage.get('files_coverage', {}).items():
                        print(f"  - {file_path}: {cov}%")
                except:
                    pass
                
                return final_task
            else:
                print(f"❌ 任务失败: {final_task.get('error_message', '未知错误')}")
                return None
        
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            return None


def main():
    """主函数 - 使用示例"""
    
    # 创建客户端
    client = AITestAgentClient(base_url="http://localhost:8000/api")
    
    # 示例1: Golang项目
    print("\n" + "="*60)
    print("示例: 为Golang项目生成测试")
    print("="*60)
    
    result = client.run_full_workflow(
        name="My Go API",
        git_url="https://github.com/username/go-api",  # 替换为你的仓库
        language="golang",
        test_framework="go_test",
        git_branch="main",
        coverage_threshold=80.0,
        auto_commit=True
    )
    
    if result:
        print("\n🎉 全部完成!")
    else:
        print("\n😞 任务未成功完成")


if __name__ == "__main__":
    # 如果需要自定义，可以修改这里
    if len(sys.argv) > 1:
        print("用法示例:")
        print("  python example_client.py")
        print("\n在代码中修改参数来自定义你的项目")
    else:
        main()

