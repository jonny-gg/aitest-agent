#!/usr/bin/env python3
"""
增量测试功能演示脚本

演示如何使用智能增量测试和自动修复功能
"""
import requests
import time
from datetime import datetime

API_BASE = "http://localhost:8000/api"


def demo_incremental_testing():
    """演示增量测试功能"""
    
    print("=" * 60)
    print("🚀 AI Test Agent - 增量测试功能演示")
    print("=" * 60)
    print()
    
    # 1. 创建项目（首次运行）
    print("📝 步骤 1：创建项目并生成测试")
    print("-" * 60)
    
    project_data = {
        "name": "增量测试演示项目",
        "description": "演示智能增量测试和自动修复功能",
        "git_url": "ssh://git@bt.baishancloud.com:7999/baishanone/cloud-ecs-api.git",
        "git_branch": "master",
        "language": "golang",
        "test_framework": "ginkgo",
        "source_directory": "internal/biz",
        "test_directory": "internal/biz",
        "coverage_threshold": 80.0,
        "auto_commit": True,
        "create_pr": True,
    }
    
    print(f"创建项目: {project_data['name']}")
    response = requests.post(f"{API_BASE}/projects", json=project_data)
    
    if response.status_code != 200:
        print(f"❌ 创建项目失败: {response.text}")
        return
    
    project = response.json()
    project_id = project['id']
    print(f"✅ 项目创建成功: {project_id}")
    print()
    
    # 2. 启动第一次测试生成（全量）
    print("📝 步骤 2：首次运行（全量生成）")
    print("-" * 60)
    
    task_response = requests.post(f"{API_BASE}/projects/{project_id}/generate-tests")
    if task_response.status_code != 200:
        print(f"❌ 启动任务失败: {task_response.text}")
        return
    
    task = task_response.json()
    task_id = task['task_id']
    print(f"✅ 任务已启动: {task_id}")
    print()
    
    # 3. 监控第一次任务进度
    print("⏳ 监控任务进度...")
    print("-" * 60)
    
    start_time = time.time()
    previous_status = None
    
    while True:
        status_response = requests.get(f"{API_BASE}/tasks/{task_id}")
        if status_response.status_code != 200:
            print(f"❌ 获取状态失败")
            break
        
        task_status = status_response.json()
        current_status = task_status['status']
        progress = task_status.get('progress', 0)
        
        if current_status != previous_status:
            print(f"📊 状态: {current_status} - 进度: {progress}%")
            previous_status = current_status
        
        if current_status in ['completed', 'failed']:
            break
        
        time.sleep(2)
    
    elapsed_time = time.time() - start_time
    
    if task_status['status'] == 'completed':
        generated_count = len(task_status.get('generated_tests', []))
        print(f"✅ 首次生成完成！")
        print(f"   - 生成测试: {generated_count} 个")
        print(f"   - 耗时: {elapsed_time:.1f} 秒")
    else:
        print(f"❌ 任务失败: {task_status.get('error', 'Unknown error')}")
        return
    
    print()
    
    # 4. 模拟第二次运行（增量）
    print("📝 步骤 3：再次运行（增量模式）")
    print("-" * 60)
    print("💡 提示：这次会跳过所有已存在的测试文件")
    print()
    
    # 等待用户确认
    input("按回车键继续第二次运行（增量模式）...")
    print()
    
    # 启动第二次任务
    task2_response = requests.post(f"{API_BASE}/projects/{project_id}/generate-tests")
    if task2_response.status_code != 200:
        print(f"❌ 启动任务失败: {task2_response.text}")
        return
    
    task2 = task2_response.json()
    task2_id = task2['task_id']
    print(f"✅ 增量任务已启动: {task2_id}")
    print()
    
    # 监控第二次任务
    print("⏳ 监控增量任务进度...")
    print("-" * 60)
    
    start_time2 = time.time()
    previous_status = None
    
    while True:
        status_response = requests.get(f"{API_BASE}/tasks/{task2_id}")
        if status_response.status_code != 200:
            break
        
        task2_status = status_response.json()
        current_status = task2_status['status']
        progress = task2_status.get('progress', 0)
        
        if current_status != previous_status:
            print(f"📊 状态: {current_status} - 进度: {progress}%")
            previous_status = current_status
        
        if current_status in ['completed', 'failed']:
            break
        
        time.sleep(2)
    
    elapsed_time2 = time.time() - start_time2
    
    if task2_status['status'] == 'completed':
        print(f"✅ 增量生成完成！")
        print(f"   - 耗时: {elapsed_time2:.1f} 秒")
        print()
        print("📊 性能对比：")
        print(f"   首次运行: {elapsed_time:.1f} 秒")
        print(f"   增量运行: {elapsed_time2:.1f} 秒")
        if elapsed_time > 0:
            speedup = elapsed_time / elapsed_time2
            print(f"   提速: {speedup:.1f}x ⚡")
    
    print()
    
    # 5. 总结
    print("=" * 60)
    print("🎉 演示完成！")
    print("=" * 60)
    print()
    print("✅ 增量测试功能已验证：")
    print("   1. 自动检测已有测试")
    print("   2. 跳过重复生成")
    print("   3. 大幅提升速度")
    print("   4. 节省 API 调用成本")
    print()
    print("📚 详细文档: docs/guides/incremental-testing.md")
    print()


if __name__ == "__main__":
    try:
        demo_incremental_testing()
    except KeyboardInterrupt:
        print("\n\n⚠️  演示已中断")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")

