#!/usr/bin/env python3
"""
AI Test Agent - 测试生成示例集合

包含多种测试生成场景：
1. 基础测试生成（Ginkgo框架）
2. 智能测试生成（基于代码复杂度）
3. 标准测试生成（go test框架）
"""

import requests
import time
import sys


def show_menu():
    """显示菜单"""
    print()
    print("=" * 70)
    print("  🚀 AI Test Agent - 测试生成示例")
    print("=" * 70)
    print()
    print("请选择测试生成场景:")
    print()
    print("  1. Ginkgo BDD 测试生成（Kratos微服务项目）")
    print("  2. 智能测试生成（基于代码复杂度，新功能）")
    print("  3. 标准 Go Test 生成")
    print("  4. 查看 Ginkgo 测试示例代码")
    print("  0. 退出")
    print()
    
    choice = input("请输入选项 (0-4): ").strip()
    return choice


def create_project_and_generate(project_config, show_details=True):
    """
    创建项目并生成测试的通用流程
    
    Args:
        project_config: 项目配置字典
        show_details: 是否显示详细的代码分析信息
    """
    API_BASE = "http://localhost:8000/api"
    
    # 1. 创建项目
    print("\n步骤 1/4: 创建项目...")
    try:
        response = requests.post(f"{API_BASE}/projects", json=project_config)
        response.raise_for_status()
        project = response.json()
        project_id = project['id']
        
        print(f"✅ 项目创建成功: {project_id}")
        print(f"   项目名: {project['name']}")
        print(f"   测试框架: {project_config['test_framework']}")
        print()
        
    except Exception as e:
        print(f"❌ 创建项目失败: {e}")
        return False
    
    # 2. 触发测试生成任务
    print("步骤 2/4: 触发测试生成任务...")
    try:
        response = requests.post(f"{API_BASE}/projects/{project_id}/tasks")
        response.raise_for_status()
        task = response.json()
        task_id = task['id']
        
        print(f"✅ 任务已创建: {task_id}")
        print()
        
    except Exception as e:
        print(f"❌ 创建任务失败: {e}")
        return False
    
    # 3. 监控任务执行
    print("步骤 3/4: 等待任务完成...")
    if show_details:
        print("💡 系统正在分析代码并生成测试，请稍候...")
    print()
    
    last_message = ""
    code_analysis_shown = False
    
    while True:
        try:
            response = requests.get(f"{API_BASE}/tasks/{task_id}")
            response.raise_for_status()
            task = response.json()
            
            status = task['status']
            progress = task['progress']
            
            # 显示代码分析结果（智能模式）
            if show_details and not code_analysis_shown and progress >= 30:
                try:
                    logs_response = requests.get(f"{API_BASE}/tasks/{task_id}/logs")
                    if logs_response.status_code == 200:
                        logs = logs_response.json()
                        
                        # 查找包含测试用例策略的日志
                        analysis_logs = []
                        for log in logs:
                            message = log.get('message', '')
                            if '建议生成' in message and '个测试用例' in message:
                                analysis_logs.append(message)
                        
                        if analysis_logs:
                            print("📊 智能代码分析结果:")
                            for msg in analysis_logs[:5]:  # 只显示前5条
                                print(f"   {msg}")
                            print()
                            code_analysis_shown = True
                except:
                    pass
            
            # 获取最新消息
            try:
                logs_response = requests.get(f"{API_BASE}/tasks/{task_id}/logs")
                if logs_response.status_code == 200:
                    logs = logs_response.json()
                    if logs and len(logs) > 0:
                        latest_log = logs[-1]
                        current_message = latest_log.get('message', status)
                        if current_message != last_message:
                            last_message = current_message
            except:
                current_message = status
            
            # 显示进度条
            progress_bar = '█' * (progress // 5) + '░' * (20 - progress // 5)
            print(f"\r[{progress_bar}] {progress:3d}% | {last_message[:50]:<50}", end='', flush=True)
            
            # 检查是否完成
            if status in ['completed', 'failed', 'cancelled']:
                print()
                break
            
            time.sleep(3)
            
        except Exception as e:
            print(f"\n❌ 查询任务状态失败: {e}")
            return False
    
    # 4. 显示结果
    print()
    print("步骤 4/4: 测试生成结果")
    print("=" * 70)
    
    if task['status'] == 'completed':
        print("✅ 任务完成!")
        print()
        
        # 测试统计
        print("📊 测试统计:")
        generated_count = len(task.get('generated_tests', []))
        total_tests = task.get('total_tests', 0)
        passed_tests = task.get('passed_tests', 0)
        failed_tests = task.get('failed_tests', 0)
        
        print(f"   生成测试文件: {generated_count} 个")
        print(f"   测试用例总数: {total_tests} 个")
        print(f"   通过测试: {passed_tests} 个")
        print(f"   失败测试: {failed_tests} 个")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"   成功率: {success_rate:.1f}%")
        print()
        
        # 覆盖率
        print("📈 代码覆盖率:")
        line_cov = task.get('line_coverage') or 0
        print(f"   行覆盖率: {line_cov:.2f}%")
        
        if task.get('branch_coverage'):
            branch_cov = task.get('branch_coverage') or 0
            print(f"   分支覆盖率: {branch_cov:.2f}%")
        
        if task.get('function_coverage'):
            func_cov = task.get('function_coverage') or 0
            print(f"   函数覆盖率: {func_cov:.2f}%")
        print()
        
        # 生成的测试文件
        if task.get('generated_tests'):
            print("📝 生成的测试文件（前5个）:")
            for test_file in task['generated_tests'][:5]:
                print(f"   - {test_file}")
            if len(task['generated_tests']) > 5:
                print(f"   ... 还有 {len(task['generated_tests']) - 5} 个文件")
        print()
        
        return True
        
    else:
        print(f"❌ 任务失败: {task.get('error_message', '未知错误')}")
        print()
        print("💡 故障排查:")
        print("   1. 检查Git仓库是否可访问")
        print("   2. 确认OpenAI API密钥正确")
        print("   3. 查看日志: docker-compose logs celery-worker")
        print()
        return False


def scenario_1_ginkgo_kratos():
    """场景1: Kratos项目使用Ginkgo BDD测试框架"""
    
    print()
    print("=" * 70)
    print("  场景 1: Kratos 项目 + Ginkgo BDD 测试")
    print("=" * 70)
    print()
    print("📖 适用场景:")
    print("   - 使用 Kratos 框架的微服务项目")
    print("   - 需要 BDD 风格测试（行为驱动开发）")
    print("   - 包含依赖注入的项目")
    print()
    
    project_data = {
        "name": "Kratos User Service",
        "description": "使用Ginkgo BDD测试的Kratos微服务",
        "git_url": "ssh://git@bt.baishancloud.com:7999/baishanone/cloud-ecs-api.git",
        "git_branch": "master",
        "language": "golang",
        "test_framework": "ginkgo",
        "source_directory": "internal/biz",
        "test_directory": "internal/biz",
        "coverage_threshold": 80.0,
        "auto_commit": True,
        "create_pr": True
    }
    
    success = create_project_and_generate(project_data, show_details=False)
    
    if success:
        print()
        print("=" * 70)
        print("🎉 Ginkgo BDD 测试生成完成!")
        print()
        print("📚 Ginkgo测试特点:")
        print("   ✓ BDD风格，可读性强")
        print("   ✓ Describe/Context/It结构清晰")
        print("   ✓ 支持BeforeEach/AfterEach依赖管理")
        print("   ✓ 完美适配Kratos依赖注入")
        print("   ✓ Gomega流畅断言API")
        print()
        print("💡 下一步:")
        print("   查看详细文档: cat docs/guides/ginkgo-guide.md")
        print()
    
    return success


def scenario_2_smart_generation():
    """场景2: 基于代码复杂度的智能测试生成"""
    
    print()
    print("=" * 70)
    print("  场景 2: 智能测试生成（基于代码复杂度）⚡")
    print("=" * 70)
    print()
    print("✨ 新功能亮点:")
    print("   1️⃣  自动计算可执行代码行数（排除注释、空行）")
    print("   2️⃣  基于代码复杂度智能决定测试用例数量")
    print("   3️⃣  简单函数少量测试，复杂函数详细测试")
    print("   4️⃣  自动分配正常/边界/异常场景比例 (40%/30%/30%)")
    print()
    print("📊 测试用例数量策略:")
    print("   - 简单函数 (< 10行): 生成 2-3 个测试用例")
    print("   - 中等函数 (10-30行): 生成 4-6 个测试用例")
    print("   - 复杂函数 (30-50行): 生成 7-10 个测试用例")
    print("   - 超复杂函数 (> 50行): 生成 11-15 个测试用例")
    print()
    
    project_data = {
        "name": "智能测试用例生成演示",
        "description": "展示基于代码复杂度的测试用例数量策略",
        "git_url": "ssh://git@bt.baishancloud.com:7999/baishanone/cloud-ecs-api.git",
        "git_branch": "master",
        "language": "golang",
        "test_framework": "ginkgo",
        "source_directory": "internal/biz",
        "test_directory": "internal/biz",
        "coverage_threshold": 80.0,
        "auto_commit": True,
        "create_pr": True
    }
    
    success = create_project_and_generate(project_data, show_details=True)
    
    if success:
        print()
        print("=" * 70)
        print("💡 智能测试用例生成的优势:")
        print()
        print("   🎯 精准覆盖")
        print("      - 避免过度测试简单函数")
        print("      - 充分测试关键业务逻辑")
        print()
        print("   💰 成本优化")
        print("      - 减少不必要的测试用例")
        print("      - 降低 AI token 消耗")
        print()
        print("   ⚡ 并发生成")
        print("      - 最多10个文件同时生成")
        print("      - 显著提升生成速度")
        print()
        print("📖 查看详细文档:")
        print("   cat docs/guides/CODE_BASED_TEST_GENERATION.md")
        print()
    
    return success


def scenario_3_standard_go_test():
    """场景3: 标准 Go Test 框架"""
    
    print()
    print("=" * 70)
    print("  场景 3: 标准 Go Test 框架")
    print("=" * 70)
    print()
    print("📖 适用场景:")
    print("   - 标准 Go 项目")
    print("   - 使用 testing 包")
    print("   - Table-driven test 风格")
    print()
    
    project_data = {
        "name": "Standard Go Test Project",
        "description": "使用标准 Go testing 包的项目",
        "git_url": "https://github.com/your-org/your-repo.git",
        "git_branch": "main",
        "language": "golang",
        "test_framework": "go_test",
        "source_directory": "pkg",
        "test_directory": "pkg",
        "coverage_threshold": 75.0,
        "auto_commit": True,
        "create_pr": True
    }
    
    success = create_project_and_generate(project_data, show_details=True)
    
    if success:
        print()
        print("=" * 70)
        print("🎉 标准 Go Test 生成完成!")
        print()
        print("📚 Go Test 特点:")
        print("   ✓ Go 原生测试框架")
        print("   ✓ Table-driven test 模式")
        print("   ✓ 简单直接，易于维护")
        print("   ✓ 无需额外依赖")
        print()
    
    return success


def show_ginkgo_example():
    """显示Ginkgo测试代码示例"""
    
    print()
    print("=" * 70)
    print("  Ginkgo 测试代码示例")
    print("=" * 70)
    print()
    print("""
// Kratos Service 测试示例
// 注意：实际生成的测试会根据你的项目自动使用正确的模块路径和包名
package service

import (
    "context"
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    
    // 实际生成时会自动替换为你的模块路径，例如：
    // "bt.baishancloud.com/baishanone/cloud-ecs-api/internal/service"
    "your-module-path/internal/service"
)

func TestService(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Service Suite")
}

var _ = Describe("UserService", func() {
    var (
        svc    *service.UserService
        ctx    context.Context
    )
    
    BeforeEach(func() {
        ctx = context.Background()
        svc = service.NewUserService()
    })
    
    Describe("CreateUser", func() {
        Context("when request is valid", func() {
            It("should create user successfully", func() {
                // Arrange
                req := &pb.CreateUserRequest{
                    Name:  "John Doe",
                    Email: "john@example.com",
                }
                
                // Act
                reply, err := svc.CreateUser(ctx, req)
                
                // Assert
                Expect(err).NotTo(HaveOccurred())
                Expect(reply.Id).To(BeNumerically(">", 0))
                Expect(reply.Name).To(Equal("John Doe"))
            })
        })
        
        Context("when name is empty", func() {
            It("should return validation error", func() {
                req := &pb.CreateUserRequest{
                    Name:  "",
                    Email: "john@example.com",
                }
                
                _, err := svc.CreateUser(ctx, req)
                
                Expect(err).To(HaveOccurred())
            })
        })
    })
})
""")
    print()
    print("💡 Gomega 常用断言:")
    print("   - Expect(actual).To(Equal(expected))")
    print("   - Expect(err).NotTo(HaveOccurred())")
    print("   - Expect(value).To(BeNil())")
    print("   - Expect(slice).To(ContainElement(item))")
    print("   - Expect(value).To(BeNumerically(\">\", 0))")
    print()
    print("🔧 自动修复功能:")
    print("   ✅ 从 go.mod 自动检测模块路径")
    print("   ✅ 根据文件位置智能推断包名")
    print("   ✅ 自动替换 'your-module-path' 占位符")
    print("   ✅ 检测并添加需要的标准库导入")
    print()
    print("📖 详细说明:")
    print("   1. 系统会自动从 go.mod 读取你的模块路径")
    print("   2. 根据源文件路径智能生成导入语句")
    print("      例如: internal/biz/user.go -> 'your-module/internal/biz'")
    print("   3. 包名自动匹配目录名 + _test 后缀")
    print("      例如: internal/biz/ -> package biz_test")
    print()


def main():
    """主函数"""
    
    while True:
        choice = show_menu()
        
        if choice == '0':
            print()
            print("👋 再见!")
            print()
            sys.exit(0)
        
        elif choice == '1':
            scenario_1_ginkgo_kratos()
            input("\n按 Enter 键返回菜单...")
        
        elif choice == '2':
            scenario_2_smart_generation()
            input("\n按 Enter 键返回菜单...")
        
        elif choice == '3':
            scenario_3_standard_go_test()
            input("\n按 Enter 键返回菜单...")
        
        elif choice == '4':
            show_ginkgo_example()
            input("\n按 Enter 键返回菜单...")
        
        else:
            print("\n❌ 无效选项，请重新选择")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消，退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        sys.exit(1)

