#!/usr/bin/env python3
"""
AI Test Agent - 测试修复（非交互式并发模式）

自动使用并发模式修复测试文件，支持命令行参数。
"""

import requests
import time
import sys
import subprocess
import argparse


def rerun_tests_and_show_pass_rate(workspace_path, test_framework="ginkgo"):
    """修复后重新运行测试并显示通过率"""
    print()
    print("=" * 70)
    print("  🔄 重新执行测试以验证修复效果")
    print("=" * 70)
    print()
    
    try:
        if test_framework == "ginkgo":
            # 在容器内执行 Ginkgo 测试
            cmd = [
                "docker", "exec", "aitest-celery-worker",
                "bash", "-c",
                f"cd {workspace_path} && go mod tidy && ginkgo -r -v -mod=mod 2>&1"
            ]
        else:
            # 标准 go test
            cmd = [
                "docker", "exec", "aitest-celery-worker",
                "bash", "-c",
                f"cd {workspace_path} && go mod tidy && go test -v ./... 2>&1"
            ]
        
        print("⏳ 正在执行测试...")
        print()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout + result.stderr
        
        # 显示部分输出用于调试
        print("💬 测试执行输出（最后20行）:")
        output_lines = output.strip().split('\n')
        for line in output_lines[-20:]:
            if line.strip():
                print(f"   {line}")
        print()
        
        # 解析 Ginkgo 输出
        if test_framework == "ginkgo":
            import re
            
            # 查找 "Ran X of Y Specs"
            ran_match = re.search(r'Ran (\d+) of (\d+) Specs', output)
            
            # 计数通过和失败
            passed_count = output.count("• [PASSED]") + output.count("✓")
            failed_count = output.count("• [FAILED]") + output.count("✗")
            
            # 也尝试匹配其他格式
            passed_match = re.search(r'(\d+) Passed', output)
            failed_match = re.search(r'(\d+) Failed', output)
            
            if passed_match:
                passed_count = max(passed_count, int(passed_match.group(1)))
            if failed_match:
                failed_count = max(failed_count, int(failed_match.group(1)))
            
            if ran_match:
                ran_specs = int(ran_match.group(1))
                total_specs = int(ran_match.group(2))
                total_count = passed_count + failed_count
                
                print("📊 测试执行结果:")
                print(f"   测试套件总数: {total_specs}")
                print(f"   执行的测试: {ran_specs}")
                print(f"   ✅ 通过: {passed_count}")
                print(f"   ❌ 失败: {failed_count}")
                print()
                
                if total_count > 0:
                    pass_rate = (passed_count / total_count) * 100
                    
                    # 彩色显示通过率
                    if pass_rate >= 80:
                        status_icon = "🎉"
                        status_text = "优秀"
                    elif pass_rate >= 60:
                        status_icon = "👍"
                        status_text = "良好"
                    elif pass_rate >= 40:
                        status_icon = "⚠️"
                        status_text = "需要改进"
                    else:
                        status_icon = "❌"
                        status_text = "较差"
                    
                    print(f"{status_icon} 测试通过率: {pass_rate:.1f}% ({status_text})")
                    print()
                    
                    # 对比修复前后
                    if failed_count > 0:
                        print("💡 仍有失败的测试:")
                        print(f"   - 建议再次运行修复脚本")
                        print(f"   - 或手动检查失败的测试用例")
                    else:
                        print("✨ 所有测试都通过了！")
                    print()
                else:
                    print("⚠️  没有找到测试结果")
                    print()
            else:
                # 没有找到 Ran X of Y，尝试其他解析方式
                total_count = passed_count + failed_count
                
                if total_count > 0:
                    # 至少找到了一些测试结果
                    print("📊 测试执行结果:")
                    print(f"   ✅ 通过: {passed_count}")
                    print(f"   ❌ 失败: {failed_count}")
                    print()
                    
                    pass_rate = (passed_count / total_count) * 100
                    
                    if pass_rate >= 80:
                        status_icon = "🎉"
                        status_text = "优秀"
                    elif pass_rate >= 60:
                        status_icon = "👍"
                        status_text = "良好"
                    elif pass_rate >= 40:
                        status_icon = "⚠️"
                        status_text = "需要改进"
                    else:
                        status_icon = "❌"
                        status_text = "较差"
                    
                    print(f"{status_icon} 测试通过率: {pass_rate:.1f}% ({status_text})")
                    print()
                
                elif "FAIL" in output or "Failed to compile" in output:
                    print("❌ 测试执行失败")
                    print()
                    print("可能的原因:")
                    if "cannot find module" in output:
                        print("   - 缺少依赖包")
                        print("   - 运行: go mod tidy")
                    elif "syntax error" in output:
                        print("   - 代码语法错误")
                        print("   - 检查修复后的代码")
                    elif "no test files" in output.lower() or "found no test" in output.lower():
                        print("   - 测试目录中没有测试文件")
                        print("   - 检查 test_directory 配置是否正确")
                    else:
                        print("   - 查看上面的输出确定问题")
                    print()
                else:
                    print("⚠️  无法解析测试结果")
                    print("   可能的原因:")
                    print("   - 测试目录路径不正确")
                    print("   - 测试文件格式不符合 Ginkgo 规范")
                    print("   - 查看上面的输出获取更多信息")
                    print()
        
        print("=" * 70)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ 测试执行超时（超过5分钟）")
        print()
        return False
        
    except Exception as e:
        print(f"❌ 执行测试失败: {e}")
        print()
        return False


def show_menu():
    """显示菜单"""
    print()
    print("=" * 70)
    print("  🔧 AI Test Agent - 测试修复示例")
    print("=" * 70)
    print()
    print("请选择修复模式:")
    print()
    print("  1. 快速修复（同步模式）")
    print("  2. 异步并发修复（推荐，速度快3-5倍）")
    print("  3. 异步修复 + Git 自动提交")
    print("  4. 查看性能对比")
    print("  0. 退出")
    print()
    
    choice = input("请输入选项 (0-4): ").strip()
    return choice


def get_fix_config():
    """获取修复配置"""
    
    print()
    print("请输入修复配置（留空使用默认值）:")
    print()
    
    workspace = input("工作空间路径 [/app/workspace/...]: ").strip()
    if not workspace:
        workspace = "/app/workspace/b8670a68-fb12-46e0-85cb-854be2da80a3"
    
    test_dir = input("测试目录 [internal/biz]: ").strip()
    if not test_dir:
        test_dir = "internal/biz"
    
    language = input("编程语言 [golang]: ").strip()
    if not language:
        language = "golang"
    
    framework = input("测试框架 [ginkgo]: ").strip()
    if not framework:
        framework = "ginkgo"
    
    return {
        "workspace_path": workspace,
        "test_directory": test_dir,
        "language": language,
        "test_framework": framework,
        "max_fix_attempts": 5
    }


def scenario_1_quick_fix():
    """场景1: 快速修复（同步模式）"""
    
    API_BASE = "http://localhost:8000/api"
    
    print()
    print("=" * 70)
    print("  场景 1: 快速修复测试代码（同步模式）")
    print("=" * 70)
    print()
    print("📖 适用场景:")
    print("   - 测试文件数量较少（< 20个）")
    print("   - 需要实时查看修复进度")
    print("   - 简单快速的修复需求")
    print()
    
    fix_config = get_fix_config()
    
    print()
    print(f"📁 工作空间: {fix_config['workspace_path']}")
    print(f"📂 测试目录: {fix_config['test_directory']}")
    print(f"🔤 语言: {fix_config['language']}")
    print(f"🧪 框架: {fix_config['test_framework']}")
    print()
    
    try:
        print("🚀 开始修复...")
        
        response = requests.post(
            f"{API_BASE}/tasks/fix-tests",
            json=fix_config,
            timeout=600
        )
        response.raise_for_status()
        result = response.json()
        
        print()
        print("=" * 70)
        print("  修复结果")
        print("=" * 70)
        print()
        
        # 总览
        print(f"✅ 总体状态: {'成功' if result['success'] else '部分失败'}")
        print()
        print(f"📊 统计:")
        print(f"   总文件数: {result['total_files']}")
        print(f"   已修复:   {result['fixed_files']}")
        print(f"   失败:     {result['failed_files']}")
        print(f"   跳过:     {result['skipped_files']}")
        print()
        
        # 详细结果
        if result['file_results']:
            print("📋 文件详情:")
            print()
            
            # 分类显示
            fixed_files = []
            no_error_files = []
            failed_files = []
            
            for file_result in result['file_results']:
                if file_result['fixed']:
                    fixed_files.append(file_result)
                elif file_result['success'] and not file_result['original_had_errors']:
                    no_error_files.append(file_result)
                else:
                    failed_files.append(file_result)
            
            # 显示已修复的文件
            if fixed_files:
                print(f"🔧 已修复 ({len(fixed_files)} 个):")
                for fr in fixed_files:
                    file_name = fr['file_path'].split('/')[-1]
                    print(f"   ✅ {file_name} (尝试 {fr['attempts']} 次)")
                print()
            
            # 显示无需修复的文件
            if no_error_files:
                print(f"⏭️  无需修复 ({len(no_error_files)} 个):")
                for fr in no_error_files[:5]:  # 只显示前5个
                    file_name = fr['file_path'].split('/')[-1]
                    print(f"   ✓ {file_name}")
                if len(no_error_files) > 5:
                    print(f"   ... 还有 {len(no_error_files) - 5} 个文件")
                print()
            
            # 显示失败的文件
            if failed_files:
                print(f"❌ 修复失败 ({len(failed_files)} 个):")
                for fr in failed_files:
                    file_name = fr['file_path'].split('/')[-1]
                    errors = ', '.join(fr['errors'][:2])
                    print(f"   ✗ {file_name}")
                    print(f"     错误: {errors}")
                print()
        
        print("=" * 70)
        
        if result['success'] or result['fixed_files'] > 0:
            print()
            if result['success']:
                print("🎉 所有测试文件修复成功!")
            else:
                print("⚠️ 部分文件已修复")
            print()
            
            # 询问是否重新运行测试
            rerun = input("是否重新运行测试以查看通过率？(y/n) [y]: ").strip().lower()
            if rerun == '' or rerun == 'y' or rerun == 'yes':
                rerun_tests_and_show_pass_rate(
                    fix_config['workspace_path'],
                    fix_config['test_framework']
                )
            else:
                print()
                print("💡 下一步:")
                print(f"   1. cd {fix_config['workspace_path']}")
                print(f"   2. cd {fix_config['test_directory']}")
                print("   3. ginkgo -r -v")
                print()
        else:
            print()
            print("⚠️ 部分文件修复失败，请检查上面的错误信息")
            print()
        
        return result['success']
        
    except requests.exceptions.ConnectionError:
        print()
        print("❌ 连接失败! 请确保服务正在运行:")
        print("   docker-compose up -d")
        print()
        return False
    
    except Exception as e:
        print()
        print(f"❌ 错误: {e}")
        print()
        return False


def scenario_2_async_fix():
    """场景2: 异步并发修复（高性能模式）"""
    
    API_BASE = "http://localhost:8000/api"
    
    print()
    print("=" * 70)
    print("  场景 2: 异步并发修复（高性能模式）⚡")
    print("=" * 70)
    print()
    print("✨ 优势:")
    print("   1️⃣  最多10个文件同时处理")
    print("   2️⃣  速度提升 3-5 倍")
    print("   3️⃣  适合大量文件修复（20+个）")
    print("   4️⃣  自动重试和错误恢复")
    print()
    
    fix_config = get_fix_config()
    
    print()
    print(f"📁 工作空间: {fix_config['workspace_path']}")
    print(f"📂 测试目录: {fix_config['test_directory']}")
    print(f"🔤 语言: {fix_config['language']}")
    print(f"🧪 框架: {fix_config['test_framework']}")
    print()
    
    try:
        print("🚀 开始异步并发修复...")
        print()
        
        # 记录开始时间
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE}/tasks/fix-tests",
            json=fix_config,
            timeout=(60, 1800)  # 连接60秒，读取30分钟
        )
        response.raise_for_status()
        result = response.json()
        
        # 计算耗时
        duration = time.time() - start_time
        
        print()
        print("=" * 70)
        print("  修复结果")
        print("=" * 70)
        print()
        
        # 总览
        print(f"✅ 总体状态: {'成功' if result['success'] else '部分失败'}")
        print()
        print(f"⏱️  总耗时: {duration:.2f} 秒")
        print()
        print(f"📊 统计:")
        print(f"   总文件数: {result['total_files']}")
        print(f"   已修复:   {result['fixed_files']}")
        print(f"   失败:     {result['failed_files']}")
        print(f"   跳过:     {result['skipped_files']}")
        
        # 计算平均速度
        if result['total_files'] > 0:
            avg_speed = result['total_files'] / duration
            print()
            print(f"⚡ 平均速度: {avg_speed:.2f} 文件/秒")
        
        print()
        print(f"💬 消息: {result['message']}")
        print()
        
        # 详细结果（只显示有问题的文件）
        if result.get('file_results'):
            has_issues = False
            for file_result in result['file_results']:
                if not file_result['success'] or file_result.get('fixed'):
                    if not has_issues:
                        print("📋 详细结果:")
                        print()
                        has_issues = True
                    
                    file_name = file_result['file_path'].split('/')[-1]
                    status = "✅ 已修复" if file_result['success'] and file_result.get('fixed') else "❌ 失败"
                    
                    print(f"  {status}: {file_name}")
                    if file_result.get('attempts'):
                        print(f"    尝试次数: {file_result['attempts']}")
                    if file_result.get('errors'):
                        print(f"    错误: {', '.join(file_result['errors'][:2])}")
                    print()
            
            if not has_issues:
                print("✨ 所有文件都无需修复，代码质量很好！")
                print()
        
        # 性能对比
        estimated_serial_time = duration * 3
        print("=" * 70)
        print("  性能对比")
        print("=" * 70)
        print()
        print(f"🐢 串行模式预计耗时: {estimated_serial_time:.2f} 秒")
        print(f"⚡ 并发模式实际耗时: {duration:.2f} 秒")
        print(f"🚀 速度提升: {(estimated_serial_time/duration):.1f}x 倍")
        print()
        
        # 询问是否重新运行测试
        if result['success'] or result['fixed_files'] > 0:
            rerun = input("是否重新运行测试以查看通过率？(y/n) [y]: ").strip().lower()
            if rerun == '' or rerun == 'y' or rerun == 'yes':
                rerun_tests_and_show_pass_rate(
                    fix_config['workspace_path'],
                    fix_config['test_framework']
                )
        
        return result['success']
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        print("   建议: 增加 timeout 参数或减少文件数量")
        return False
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def scenario_3_async_with_git():
    """场景3: 异步修复 + Git 自动提交"""
    
    API_BASE = "http://localhost:8000/api"
    
    print()
    print("=" * 70)
    print("  场景 3: 异步修复 + Git 自动提交")
    print("=" * 70)
    print()
    print("✨ 功能:")
    print("   1️⃣  异步并发修复测试代码")
    print("   2️⃣  自动创建分支")
    print("   3️⃣  自动提交修复结果")
    print("   4️⃣  自动推送到远程仓库")
    print()
    
    fix_config = get_fix_config()
    
    # 添加Git配置
    print()
    print("Git 配置:")
    git_username = input("Git 用户名 [utest-agent]: ").strip()
    if not git_username:
        git_username = "utest-agent"
    
    git_branch = "aitest/add-tests-20251023-082555"
    
    fix_config.update({
        "auto_git_commit": True,
        "git_username": git_username,
    })
    
    if git_branch:
        fix_config["git_branch_name"] = git_branch
    
    print()
    print(f"📁 工作空间: {fix_config['workspace_path']}")
    print(f"📂 测试目录: {fix_config['test_directory']}")
    print(f"🔤 语言: {fix_config['language']}")
    print(f"🧪 框架: {fix_config['test_framework']}")
    print(f"👤 Git 用户: {git_username}")
    print()
    
    try:
        print("🚀 开始异步修复并提交...")
        print()
        
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE}/tasks/fix-tests",
            json=fix_config,
            timeout=(60, 1800)
        )
        response.raise_for_status()
        result = response.json()
        
        duration = time.time() - start_time
        
        print()
        print("=" * 70)
        print("  修复结果")
        print("=" * 70)
        print()
        
        print(f"✅ 总体状态: {'成功' if result['success'] else '部分失败'}")
        print()
        print(f"⏱️  总耗时: {duration:.2f} 秒")
        print()
        print(f"📊 统计:")
        print(f"   总文件数: {result['total_files']}")
        print(f"   已修复:   {result['fixed_files']}")
        print(f"   失败:     {result['failed_files']}")
        print(f"   跳过:     {result['skipped_files']}")
        print()
        
        # Git 操作结果
        if result.get('git_result'):
            git_result = result['git_result']
            print("=" * 70)
            print("  Git 操作结果")
            print("=" * 70)
            print()
            if git_result['success']:
                print(f"✅ Git 状态: 成功")
                if git_result.get('branch'):
                    print(f"🌿 分支: {git_result['branch']}")
                if git_result.get('committed'):
                    print(f"💾 已提交: 是")
                if git_result.get('pushed'):
                    print(f"🚀 已推送: 是")
                print(f"💬 {git_result['message']}")
            else:
                print(f"❌ Git 状态: 失败")
                print(f"💬 错误: {git_result['message']}")
            print()
        
        # 询问是否重新运行测试
        if result['success'] or result['fixed_files'] > 0:
            rerun = input("是否重新运行测试以查看通过率？(y/n) [y]: ").strip().lower()
            if rerun == '' or rerun == 'y' or rerun == 'yes':
                rerun_tests_and_show_pass_rate(
                    fix_config['workspace_path'],
                    fix_config['test_framework']
                )
        
        return result['success']
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def show_performance_comparison():
    """显示性能对比"""
    
    print()
    print("=" * 70)
    print("  性能对比测试")
    print("=" * 70)
    print()
    
    # 模拟数据
    test_scenarios = [
        {"files": 10, "serial": 30, "async": 10},
        {"files": 25, "serial": 75, "async": 25},
        {"files": 46, "serial": 180, "async": 45},
        {"files": 100, "serial": 400, "async": 90},
    ]
    
    print("📊 不同文件数量下的性能对比:\n")
    print(f"{'文件数':<10} {'同步模式':<15} {'异步模式':<15} {'速度提升':<10}")
    print("-" * 55)
    
    for scenario in test_scenarios:
        files = scenario['files']
        serial = scenario['serial']
        async_time = scenario['async']
        speedup = serial / async_time
        
        print(f"{files:<10} {serial:<15}秒 {async_time:<15}秒 {speedup:.1f}x 倍")
    
    print()
    print("💡 结论:")
    print("   - 文件越多，异步模式优势越明显")
    print("   - 建议：> 20 个文件时使用异步模式")
    print("   - 默认并发数：10（可在代码中调整）")
    print()


def async_fix_tests(workspace_path, test_directory="internal/biz", 
                    language="golang", test_framework="ginkgo",
                    auto_rerun=True, git_commit=False, git_branch=None):
    """非交互式异步并发修复"""
    
    API_BASE = "http://localhost:8000/api"
    
    print()
    print("=" * 70)
    print("  🔧 AI Test Agent - 异步并发修复")
    print("=" * 70)
    print()
    
    fix_config = {
        "workspace_path": workspace_path,
        "test_directory": test_directory,
        "language": language,
        "test_framework": test_framework,
        "max_fix_attempts": 5
    }
    
    # 如果需要 Git 提交
    if git_commit:
        fix_config.update({
            "auto_git_commit": True,
            "git_username": "aitest-agent",
        })
        if git_branch:
            fix_config["git_branch_name"] = git_branch
    
    print(f"📁 工作空间: {workspace_path}")
    print(f"📂 测试目录: {test_directory}")
    print(f"🔤 语言: {language}")
    print(f"🧪 框架: {test_framework}")
    if git_commit:
        print(f"🌿 Git 分支: {git_branch or '自动生成'}")
    print()
    
    try:
        print("🚀 开始异步并发修复...")
        print()
        
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE}/tasks/fix-tests",
            json=fix_config,
            timeout=(60, 1800)
        )
        response.raise_for_status()
        result = response.json()
        
        duration = time.time() - start_time
        
        print()
        print("=" * 70)
        print("  修复结果")
        print("=" * 70)
        print()
        
        print(f"✅ 总体状态: {'成功' if result['success'] else '部分失败'}")
        print()
        print(f"⏱️  总耗时: {duration:.2f} 秒")
        print()
        print(f"📊 统计:")
        print(f"   总文件数: {result['total_files']}")
        print(f"   已修复:   {result['fixed_files']}")
        print(f"   失败:     {result['failed_files']}")
        print(f"   跳过:     {result['skipped_files']}")
        
        if result['total_files'] > 0:
            avg_speed = result['total_files'] / duration
            print()
            print(f"⚡ 平均速度: {avg_speed:.2f} 文件/秒")
        
        print()
        
        # 显示详细结果
        if result.get('file_results'):
            has_issues = False
            for file_result in result['file_results']:
                if not file_result['success'] or file_result.get('fixed'):
                    if not has_issues:
                        print("📋 详细结果:")
                        print()
                        has_issues = True
                    
                    file_name = file_result['file_path'].split('/')[-1]
                    status = "✅ 已修复" if file_result['success'] and file_result.get('fixed') else "❌ 失败"
                    
                    print(f"  {status}: {file_name}")
                    if file_result.get('attempts'):
                        print(f"    尝试次数: {file_result['attempts']}")
                    if file_result.get('errors'):
                        print(f"    错误: {', '.join(file_result['errors'][:2])}")
                    print()
        
        # Git 操作结果
        if result.get('git_result'):
            git_result = result['git_result']
            print("=" * 70)
            print("  Git 操作结果")
            print("=" * 70)
            print()
            if git_result['success']:
                print(f"✅ Git 状态: 成功")
                if git_result.get('branch'):
                    print(f"🌿 分支: {git_result['branch']}")
                if git_result.get('committed'):
                    print(f"💾 已提交: 是")
                if git_result.get('pushed'):
                    print(f"🚀 已推送: 是")
                print(f"💬 {git_result['message']}")
            else:
                print(f"❌ Git 状态: 失败")
                print(f"💬 错误: {git_result['message']}")
            print()
        
        # 自动重新运行测试
        if auto_rerun and (result['success'] or result['fixed_files'] > 0):
            print("=" * 70)
            rerun_tests_and_show_pass_rate(workspace_path, test_framework)
        
        return result['success']
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AI Test Agent - 异步并发测试修复工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 使用默认配置
  python3 example_fix_tests.py
  
  # 指定工作空间
  python3 example_fix_tests.py -w /app/workspace/xxx-xxx-xxx
  
  # 指定测试目录
  python3 example_fix_tests.py -w /app/workspace/xxx -d internal/biz
  
  # 启用 Git 提交
  python3 example_fix_tests.py -w /app/workspace/xxx --git --branch aitest/fix-tests
  
  # 不自动运行测试
  python3 example_fix_tests.py -w /app/workspace/xxx --no-rerun
        '''
    )
    
    parser.add_argument(
        '-w', '--workspace',
        default='/app/workspace/712b7838-417c-40e5-af90-f84bbd02f08b',
        help='工作空间路径 (默认: 最新生成的工作空间)'
    )
    
    parser.add_argument(
        '-d', '--directory',
        default='internal/biz',
        help='测试目录 (默认: internal/biz)'
    )
    
    parser.add_argument(
        '-l', '--language',
        default='golang',
        choices=['golang', 'python', 'java', 'cpp', 'c'],
        help='编程语言 (默认: golang)'
    )
    
    parser.add_argument(
        '-f', '--framework',
        default='ginkgo',
        choices=['ginkgo', 'go_test', 'pytest', 'junit', 'gtest'],
        help='测试框架 (默认: ginkgo)'
    )
    
    parser.add_argument(
        '--git',
        action='store_true',
        help='启用 Git 自动提交'
    )
    
    parser.add_argument(
        '--branch',
        default='aitest/add-tests-20251023-082555',
        help='Git 分支名称 (默认: aitest/add-tests-20251023-082555)'
    )
    
    parser.add_argument(
        '--no-rerun',
        action='store_true',
        help='修复后不自动重新运行测试'
    )
    
    args = parser.parse_args()
    
    print()
    print("🔧 AI Test Agent - 非交互式并发修复")
    print()
    
    success = async_fix_tests(
        workspace_path=args.workspace,
        test_directory=args.directory,
        language=args.language,
        test_framework=args.framework,
        auto_rerun=not args.no_rerun,
        git_commit=args.git,
        git_branch=args.branch if args.git else None
    )
    
    print()
    print("=" * 70)
    if success:
        print("🎉 修复完成!")
    else:
        print("⚠️  修复完成，但部分文件可能仍有问题")
    print("=" * 70)
    print()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户取消，退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
