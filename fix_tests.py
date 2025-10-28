#!/usr/bin/env python3
"""
测试代码修复工具

用于修复已生成的测试文件中的语法错误，支持：
- 清理 markdown 标记残留
- 修复括号不匹配
- 修复其他语法错误

使用方法：
    # 方法1: 通过 API
    python fix_tests.py --api \
        --workspace /app/workspace/a5db9f32-xxx \
        --test-dir internal/biz \
        --language golang \
        --framework ginkgo
    
    # 方法2: 直接调用
    python fix_tests.py --direct \
        --workspace /app/workspace/a5db9f32-xxx \
        --test-dir internal/biz \
        --language golang \
        --framework ginkgo
"""

import sys
import argparse
import requests
from pathlib import Path


def fix_via_api(
    workspace_path: str,
    test_directory: str,
    language: str = "golang",
    test_framework: str = "ginkgo",
    max_attempts: int = 3,
    api_base: str = "http://localhost:8000/api"
):
    """通过 API 修复测试"""
    print("=" * 70)
    print("  测试代码修复工具 (API 模式)")
    print("=" * 70)
    print()
    print(f"📁 工作空间: {workspace_path}")
    print(f"📂 测试目录: {test_directory}")
    print(f"🔤 语言: {language}")
    print(f"🧪 框架: {test_framework}")
    print(f"🔄 最大尝试次数: {max_attempts}")
    print()
    
    try:
        print("🚀 发送修复请求...")
        response = requests.post(
            f"{api_base}/tasks/fix-tests",
            json={
                "workspace_path": workspace_path,
                "test_directory": test_directory,
                "language": language,
                "test_framework": test_framework,
                "max_fix_attempts": max_attempts
            }
        )
        response.raise_for_status()
        result = response.json()
        
        print()
        print("=" * 70)
        print("  修复结果")
        print("=" * 70)
        print()
        print(f"✅ 成功: {result['success']}")
        print(f"📝 总文件数: {result['total_files']}")
        print(f"🔧 已修复: {result['fixed_files']}")
        print(f"❌ 失败: {result['failed_files']}")
        print(f"⏭️  跳过: {result['skipped_files']}")
        print()
        print(f"💬 消息: {result['message']}")
        print()
        
        # 显示详细结果
        if result['file_results']:
            print("📋 详细结果:")
            print()
            for file_result in result['file_results']:
                status = "✅" if file_result['success'] else "❌"
                file_path = Path(file_result['file_path']).name
                
                if file_result['fixed']:
                    print(f"  {status} {file_path} - 已修复 (尝试 {file_result['attempts']} 次)")
                elif file_result['success'] and not file_result['original_had_errors']:
                    print(f"  ⏭️  {file_path} - 无需修复")
                else:
                    errors_text = ", ".join(file_result['errors'][:2])
                    print(f"  {status} {file_path} - 失败: {errors_text}")
        
        print()
        print("=" * 70)
        
        return result['success']
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败! 请确保 API 服务正在运行:")
        print("   docker-compose up -d")
        return False
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ API 错误: {e}")
        if e.response is not None:
            print(f"   详情: {e.response.text}")
        return False
    
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def fix_directly(
    workspace_path: str,
    test_directory: str,
    language: str = "golang",
    test_framework: str = "ginkgo",
    max_attempts: int = 3
):
    """直接调用修复服务"""
    print("=" * 70)
    print("  测试代码修复工具 (直接模式)")
    print("=" * 70)
    print()
    print(f"📁 工作空间: {workspace_path}")
    print(f"📂 测试目录: {test_directory}")
    print(f"🔤 语言: {language}")
    print(f"🧪 框架: {test_framework}")
    print(f"🔄 最大尝试次数: {max_attempts}")
    print()
    
    try:
        # 导入修复服务
        sys.path.insert(0, str(Path(__file__).parent / "backend"))
        from app.services.test_fixer import TestFixer
        
        print("🔧 初始化修复器...")
        fixer = TestFixer(
            language=language,
            test_framework=test_framework
        )
        
        print("🚀 开始修复...")
        print()
        
        result = fixer.fix_tests_in_directory(
            workspace_path=workspace_path,
            test_directory=test_directory,
            max_fix_attempts=max_attempts
        )
        
        print()
        print("=" * 70)
        print("  修复结果")
        print("=" * 70)
        print()
        print(f"✅ 成功: {result['success']}")
        print(f"📝 总文件数: {result['total_files']}")
        print(f"🔧 已修复: {result['fixed_files']}")
        print(f"❌ 失败: {result['failed_files']}")
        print(f"⏭️  跳过: {result['skipped_files']}")
        print()
        print(f"💬 消息: {result['message']}")
        print()
        
        # 显示详细结果
        if result['file_results']:
            print("📋 详细结果:")
            print()
            for file_result in result['file_results']:
                status = "✅" if file_result['success'] else "❌"
                file_path = Path(file_result['file_path']).name
                
                if file_result['fixed']:
                    print(f"  {status} {file_path} - 已修复 (尝试 {file_result['attempts']} 次)")
                elif file_result['success'] and not file_result['original_had_errors']:
                    print(f"  ⏭️  {file_path} - 无需修复")
                else:
                    errors_text = ", ".join(file_result['errors'][:2])
                    print(f"  {status} {file_path} - 失败: {errors_text}")
        
        print()
        print("=" * 70)
        
        return result['success']
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("   提示: 请确保在正确的目录运行，或使用 --api 模式")
        return False
    
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="测试代码修复工具 - 修复已生成的测试文件中的语法错误",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 通过 API 修复 (推荐)
  python fix_tests.py --api -w /app/workspace/a5db9f32-xxx -t internal/biz
  
  # 直接调用修复
  python fix_tests.py --direct -w /app/workspace/a5db9f32-xxx -t internal/biz
  
  # 指定语言和框架
  python fix_tests.py --api -w /path/to/workspace -t test/dir -l cpp -f google_test
        """
    )
    
    # 模式选择
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--api",
        action="store_true",
        help="通过 API 修复 (推荐)"
    )
    mode_group.add_argument(
        "--direct",
        action="store_true",
        help="直接调用修复服务"
    )
    
    # 必需参数
    parser.add_argument(
        "-w", "--workspace",
        required=True,
        help="工作空间路径，如 /app/workspace/a5db9f32-xxx"
    )
    parser.add_argument(
        "-t", "--test-dir",
        required=True,
        help="测试目录相对路径，如 internal/biz"
    )
    
    # 可选参数
    parser.add_argument(
        "-l", "--language",
        default="golang",
        choices=["golang", "cpp", "c"],
        help="编程语言 (默认: golang)"
    )
    parser.add_argument(
        "-f", "--framework",
        default="ginkgo",
        choices=["go_test", "ginkgo", "google_test", "catch2", "cunit"],
        help="测试框架 (默认: ginkgo)"
    )
    parser.add_argument(
        "-m", "--max-attempts",
        type=int,
        default=3,
        help="每个文件最大修复尝试次数 (默认: 3)"
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000/api",
        help="API 基础URL (默认: http://localhost:8000/api)"
    )
    
    args = parser.parse_args()
    
    # 执行修复
    if args.api:
        success = fix_via_api(
            workspace_path=args.workspace,
            test_directory=args.test_dir,
            language=args.language,
            test_framework=args.framework,
            max_attempts=args.max_attempts,
            api_base=args.api_base
        )
    else:  # --direct
        success = fix_directly(
            workspace_path=args.workspace,
            test_directory=args.test_dir,
            language=args.language,
            test_framework=args.framework,
            max_attempts=args.max_attempts
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

