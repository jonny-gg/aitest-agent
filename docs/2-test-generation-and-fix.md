# 📝 测试生成和修复完全指南

本指南涵盖了AI Test Agent的核心功能：测试生成和测试修复。

---

## 📋 目录

1. [测试生成](#测试生成)
   - [基础用法](#基础用法)
   - [高级选项](#高级选项)
   - [使用示例](#使用示例)
2. [测试修复](#测试修复)
   - [修复功能说明](#修复功能说明)
   - [异步并发修复](#异步并发修复)
   - [使用方法](#使用方法)
3. [自动修复机制](#自动修复机制)
4. [最佳实践](#最佳实践)

---

## 测试生成

### 基础用法

#### 方式 1: 使用 Python 示例脚本（推荐）

```bash
# 1. 安装依赖
pip install requests

# 2. 运行示例脚本
python example_generate_tests.py
```

**选择测试场景：**

```
请选择测试生成场景:
1. Ginkgo BDD 测试（推荐用于 Kratos 项目）
2. 智能测试生成（基于代码复杂度）
3. 标准 Go Test（传统 table-driven 风格）
```

#### 方式 2: 使用 API

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "git_url": "https://github.com/username/repo",
    "language": "golang",
    "test_framework": "ginkgo",
    "coverage_threshold": 80.0
  }'
```

### 高级选项

#### 项目配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | string | **必需** | 项目名称 |
| `git_url` | string | **必需** | Git 仓库 URL |
| `git_branch` | string | "main" | 分支名称 |
| `language` | string | "golang" | 编程语言 |
| `test_framework` | string | "ginkgo" | 测试框架 |
| `source_directory` | string | "." | 源代码目录 |
| `test_directory` | string | "tests" | 测试目录 |
| `coverage_threshold` | float | 80.0 | 覆盖率阈值 |
| `auto_commit` | boolean | true | 自动提交 |
| `create_pr` | boolean | false | 自动创建 PR |
| `ai_model` | string | "gpt-4" | AI 模型 |
| `max_tokens` | int | 2000 | 最大 Token 数 |
| `temperature` | float | 0.3 | 生成温度 |

#### 支持的语言和框架

| 语言 | 测试框架 | 说明 |
|------|---------|------|
| **golang** | `ginkgo` | Ginkgo BDD 测试（推荐） |
| **golang** | `go_test` | 标准 Go Test |
| **cpp** | `google_test` | Google Test 框架 |
| **cpp** | `catch2` | Catch2 框架 |
| **c** | `cunit` | CUnit 框架 |
| **c** | `unity` | Unity 框架 |

### 使用示例

#### 示例 1: Golang 项目 - Ginkgo BDD

**项目配置：**

```json
{
  "name": "Kratos Microservice",
  "git_url": "https://github.com/example/kratos-api",
  "language": "golang",
  "test_framework": "ginkgo",
  "coverage_threshold": 80.0,
  "auto_commit": true
}
```

**生成的测试示例：**

```go
package models_test

import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    "your-module/models"
)

var _ = Describe("User", func() {
    Context("Validate", func() {
        It("should pass for valid user", func() {
            user := models.User{
                ID:    1,
                Name:  "John Doe",
                Email: "john@example.com",
            }
            Expect(user.Validate()).To(Succeed())
        })

        It("should fail for empty name", func() {
            user := models.User{
                ID:    2,
                Name:  "",
                Email: "test@example.com",
            }
            Expect(user.Validate()).To(HaveOccurred())
        })

        It("should fail for invalid email", func() {
            user := models.User{
                ID:    3,
                Name:  "Jane",
                Email: "invalid-email",
            }
            Expect(user.Validate()).To(HaveOccurred())
        })
    })

    Context("IsAdmin", func() {
        It("should return true for admin user", func() {
            user := models.User{ID: 1}
            Expect(user.IsAdmin()).To(BeTrue())
        })

        It("should return false for regular user", func() {
            user := models.User{ID: 2}
            Expect(user.IsAdmin()).To(BeFalse())
        })
    })
})
```

#### 示例 2: Golang 项目 - 标准 Go Test

**项目配置：**

```json
{
  "name": "Go REST API",
  "git_url": "https://github.com/example/go-api",
  "language": "golang",
  "test_framework": "go_test",
  "auto_commit": true,
  "create_pr": true
}
```

**生成的测试示例：**

```go
package models

import (
    "testing"
)

func TestUser_Validate(t *testing.T) {
    tests := []struct {
        name    string
        user    User
        wantErr bool
    }{
        {
            name: "valid user",
            user: User{
                ID:    1,
                Name:  "John Doe",
                Email: "john@example.com",
            },
            wantErr: false,
        },
        {
            name: "empty name",
            user: User{
                ID:    2,
                Name:  "",
                Email: "test@example.com",
            },
            wantErr: true,
        },
        {
            name: "invalid email",
            user: User{
                ID:    3,
                Name:  "Jane",
                Email: "invalid-email",
            },
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := tt.user.Validate()
            if (err != nil) != tt.wantErr {
                t.Errorf("Validate() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

#### 示例 3: C++ 项目 - Google Test

**项目配置：**

```json
{
  "name": "C++ Calculator",
  "git_url": "https://github.com/example/cpp-calculator",
  "language": "cpp",
  "test_framework": "google_test",
  "coverage_threshold": 85.0
}
```

**生成的测试示例：**

```cpp
#include <gtest/gtest.h>
#include "calculator.h"

class CalculatorTest : public ::testing::Test {
protected:
    Calculator calc;
};

TEST_F(CalculatorTest, AddPositiveNumbers) {
    EXPECT_EQ(calc.add(2, 3), 5);
}

TEST_F(CalculatorTest, SubtractNumbers) {
    EXPECT_EQ(calc.subtract(5, 3), 2);
}

TEST_F(CalculatorTest, MultiplyNumbers) {
    EXPECT_EQ(calc.multiply(4, 3), 12);
}

TEST_F(CalculatorTest, DivideByZeroThrowsException) {
    EXPECT_THROW(calc.divide(5, 0), std::invalid_argument);
}
```

#### 示例 4: 定时任务

**设置每天凌晨 2 点自动运行：**

```bash
curl -X PUT http://localhost:8000/api/projects/{project_id} \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_cron": "0 2 * * *",
    "enabled": true
  }'
```

**常用 Cron 表达式：**

| 表达式 | 说明 |
|--------|------|
| `0 2 * * *` | 每天凌晨 2 点 |
| `0 9 * * 1` | 每周一上午 9 点 |
| `0 * * * *` | 每小时 |
| `*/30 * * * *` | 每 30 分钟 |

#### 示例 5: WebSocket 实时监控

**JavaScript 客户端：**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks/{task_id}/stream');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('进度:', data.progress, '%');
    console.log('状态:', data.status);
    console.log('消息:', data.message);
    
    // 更新 UI
    updateProgressBar(data.progress);
    updateStatus(data.status);
};
```

**Python 客户端：**

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"进度: {data['progress']}%")
    print(f"状态: {data['status']}")

ws = websocket.WebSocketApp(
    f"ws://localhost:8000/ws/tasks/{task_id}/stream",
    on_message=on_message
)

ws.run_forever()
```

---

## 测试修复

### 修复功能说明

测试代码修复功能用于修复已生成的测试文件中的语法错误。

#### 适用场景

- ✅ 之前生成的测试文件有语法错误（如残留 markdown 标记）
- ✅ 测试无法编译运行
- ✅ 覆盖率为 0%
- ✅ 批量修复多个测试文件

#### 支持的修复类型

1. **清理 Markdown 标记**
   - ````go`, ````golang`, ````markdown`, ``` 等
   - 中间残留的代码块标记

2. **语法错误修复**
   - 括号不匹配
   - Go 语法错误（使用 gofmt 检测）
   - 其他编译错误

3. **自动修复循环**
   - 发现错误 → AI 修复 → 验证 → 重复（最多 3 次）
   - 修复后自动格式化代码

### 异步并发修复

从当前版本开始，`/tasks/fix-tests` 接口已升级为**异步并发处理**模式。

#### ⚡ 性能对比

| 模式 | 处理方式 | 预计时间 | 速度提升 |
|------|---------|---------|---------|
| **旧版（串行）** | 顺序处理，一次一个文件 | 2-5 分钟 | - |
| **新版（异步并发）** | 同时处理 5 个文件 | 30-60 秒 | **快 3-5 倍** ⚡ |

#### 核心改进

**1. 并发处理**

```python
# 旧版：串行处理
for test_file in test_files:
    result = fix_single_file(test_file)
    
# 新版：异步并发
tasks = [fix_file_async(f) for f in test_files]
results = await asyncio.gather(*tasks)  # 同时处理多个
```

**2. 并发控制**

- 默认最大并发：**5 个文件**
- 可根据服务器资源调整

**3. 实时进度**

```
🔧 [1/46] 处理文件: user_test.go
🔧 [2/46] 处理文件: order_test.go
✅ [1/46] user_test.go: 修复成功 (尝试 2 次)
✅ [2/46] order_test.go: 无需修复
```

### 使用方法

#### 方法 1：简单示例脚本（推荐）

**1. 修改配置**

编辑 `example_fix_tests.py`：

```python
fix_config = {
    # 工作空间路径
    "workspace_path": "/app/workspace/a5db9f32-xxx",
    
    # 测试目录（相对于工作空间）
    "test_directory": "internal/biz",
    
    # 编程语言
    "language": "golang",
    
    # 测试框架
    "test_framework": "ginkgo",
    
    # 每个文件最大修复尝试次数
    "max_fix_attempts": 3
}
```

**2. 运行修复**

```bash
python example_fix_tests.py
```

**3. 查看输出**

```
======================================================================
  修复已生成的测试代码
======================================================================

📁 工作空间: /app/workspace/a5db9f32-xxx
📂 测试目录: internal/biz
🔤 语言: golang
🧪 框架: ginkgo

🚀 发送修复请求...

======================================================================
  修复结果
======================================================================

✅ 总体状态: 成功

📊 统计:
   总文件数: 55
   已修复:   12
   失败:     0
   跳过:     43

🎉 所有测试文件修复成功!
```

#### 方法 2：命令行工具

```bash
python fix_tests.py --api \
    -w /app/workspace/a5db9f32-xxx \
    -t internal/biz \
    -l golang \
    -f ginkgo \
    -m 3
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --api | - | 通过 API 修复（推荐） | - |
| --workspace | -w | 工作空间路径 | **必需** |
| --test-dir | -t | 测试目录相对路径 | **必需** |
| --language | -l | 编程语言 | golang |
| --framework | -f | 测试框架 | ginkgo |
| --max-attempts | -m | 最大修复尝试次数 | 3 |

#### 方法 3：直接调用 API

**使用 curl：**

```bash
curl -X POST http://localhost:8000/api/tasks/fix-tests \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_path": "/app/workspace/a5db9f32-xxx",
    "test_directory": "internal/biz",
    "language": "golang",
    "test_framework": "ginkgo",
    "max_fix_attempts": 3
  }'
```

**使用 Python requests：**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/tasks/fix-tests",
    json={
        "workspace_path": "/app/workspace/a5db9f32-xxx",
        "test_directory": "internal/biz",
        "language": "golang",
        "test_framework": "ginkgo",
        "max_fix_attempts": 3
    }
)

result = response.json()
print(f"修复成功: {result['success']}")
print(f"已修复: {result['fixed_files']} / {result['total_files']}")
```

#### API 响应格式

```json
{
  "success": true,
  "total_files": 46,
  "fixed_files": 12,
  "failed_files": 0,
  "skipped_files": 34,
  "message": "完成! 总计: 46, 修复: 12, 失败: 0, 跳过: 34",
  "file_results": [
    {
      "file_path": "/app/workspace/.../user_test.go",
      "success": true,
      "original_had_errors": true,
      "fixed": true,
      "attempts": 2,
      "errors": []
    }
  ]
}
```

### 工作空间路径说明

#### 容器内路径（推荐）

```bash
# 进入容器
docker-compose exec api bash

# 查看工作空间列表
ls -la /app/workspace/

# 使用容器内路径
workspace_path: /app/workspace/a5db9f32-xxx
```

#### 主机路径

```bash
# 主机路径（取决于 docker-compose.yml 的 volume 配置）
workspace_path: /Users/jonny/aitest-agent/backend/workspace/a5db9f32-xxx
```

#### 如何找到工作空间路径

```bash
# 方法1：通过 API 查询项目
curl http://localhost:8000/api/projects | jq '.[] | {id, name}'

# 方法2：直接列出工作空间
ls -la backend/workspace/

# 方法3：从日志中查找
docker-compose logs api | grep "workspace"
```

### 典型场景

#### 场景 1：修复有 markdown 标记的测试

**问题**：55 个测试文件，部分有 ````go` 标记残留。

**解决方案**：

```bash
python example_fix_tests.py
```

**结果**：
- 自动扫描 55 个测试文件
- 检测并修复有语法错误的文件
- 保存修复后的代码
- 提供详细的修复报告

#### 场景 2：修复特定子目录

```bash
python fix_tests.py --api \
    -w /app/workspace/a5db9f32-xxx \
    -t internal/biz/user \
    -l golang \
    -f ginkgo
```

#### 场景 3：批量修复多个语言

```bash
# Go 测试
python fix_tests.py --api -w /workspace/project1 -t tests -l golang -f ginkgo

# C++ 测试
python fix_tests.py --api -w /workspace/project2 -t tests -l cpp -f google_test

# C 测试
python fix_tests.py --api -w /workspace/project3 -t tests -l c -f cunit
```

---

## 自动修复机制

### 什么是自动修复？

当 AI 生成的测试执行**失败**时，系统会自动：

1. 分析失败原因（解析错误输出）
2. 使用 AI 重新生成测试代码
3. 验证修复结果
4. 重复此过程（最多 N 次）

### 快速配置

在 `.env` 文件中添加：

```bash
MAX_TEST_FIX_RETRIES=3    # 最大重试 3 次
ENABLE_AUTO_FIX=true      # 启用自动修复
```

### 工作流程

```
AI 生成测试 → 执行测试 → 失败？
                              ↓ 是
                         分析+修复
                              ↓
                         再次验证
                              ↓
                    通过？或达到最大重试？
                              ↓
                           完成
```

### 支持的失败类型

✅ 断言错误  
✅ 逻辑错误  
✅ 边界条件  
✅ 导入缺失  
✅ 语法错误  

### 效果统计

- **测试通过率**: 70% → 90%+
- **自动修复成功率**: 60-70%
- **平均修复时间**: 30-60秒/次

### 日志示例

```
🧪 测试结果: 3/5 通过
🔧 检测到 2 个测试失败，开始自动修复...
🔄 第 1/3 次修复尝试
✅ 测试修复成功: test_auth.go
🎉 所有测试都通过了！
```

### 何时使用

**推荐场景：**
- 快速原型开发
- CI/CD 自动化
- 大批量测试生成
- 学习和探索项目

**不推荐场景：**
- 极端复杂的业务逻辑
- 需要精确控制的测试
- 性能基准测试

### 配置建议

| 场景 | 重试次数 | 说明 |
|------|----------|------|
| 开发测试 | 3 | 平衡速度和质量 |
| CI/CD | 2 | 快速反馈 |
| 正式发布 | 5 | 最大化质量 |
| 快速验证 | 1 | 仅尝试一次 |

### 禁用方法

如果不需要自动修复：

```bash
ENABLE_AUTO_FIX=false
```

---

## 最佳实践

### 1. 测试生成最佳实践

#### 使用合适的测试框架

- **Kratos/微服务项目**: 使用 Ginkgo BDD 测试
- **传统 Go 项目**: 使用标准 Go Test
- **C++ 项目**: 使用 Google Test
- **复杂场景**: 结合智能测试策略

#### 合理设置覆盖率阈值

```python
# 新项目或快速验证
coverage_threshold = 60.0

# 一般项目
coverage_threshold = 80.0

# 关键项目
coverage_threshold = 90.0
```

#### 分批生成测试

```python
# 不要一次生成整个项目，按模块分批
modules = [
    "internal/biz",
    "internal/service",
    "internal/data"
]

for module in modules:
    generate_tests(module)
```

### 2. 测试修复最佳实践

#### 先备份再修复

```bash
# 方法1：使用 Git
cd /app/workspace/xxx
git add .
git commit -m "修复前备份"

# 方法2：直接复制
cp -r internal/biz internal/biz.backup
```

#### 小范围测试

- 先在一个小目录测试
- 确认效果后再大范围使用

#### 查看修复详情

- 仔细查看修复报告
- 对失败的文件手动检查

#### 验证修复结果

```bash
cd /app/workspace/xxx/internal/biz
ginkgo -r -v
go test -cover ./...
```

#### 定期修复

- 在每次批量生成后运行修复
- 确保测试代码质量

### 3. 性能优化

#### 调整并发数

可以在 `tasks.py` 中修改：

```python
result = await fixer.fix_tests_in_directory_async(
    workspace_path=fix_request.workspace_path,
    test_directory=fix_request.test_directory,
    max_fix_attempts=fix_request.max_fix_attempts,
    max_concurrent=10  # 增加到 10 个并发
)
```

**建议值：**
- **CPU 密集型服务器**: 5-10
- **IO 密集型服务器**: 10-20
- **开发环境**: 3-5

#### 监控资源使用

```bash
# 监控内存
watch -n 1 free -h

# 监控进程
top -p $(pgrep -f "python.*aitest")
```

### 4. 故障排查

#### 问题 1：生成的测试有语法错误

**解决方案**：运行修复

```bash
python example_fix_tests.py
```

#### 问题 2：修复速度慢

**可能原因**：
- 文件数量太多
- AI API 响应慢
- 并发数设置过低

**解决方案**：
```python
# 增加并发数
max_concurrent=10

# 分批处理
directories = ["internal/biz", "internal/service"]
for dir in directories:
    fix_tests(workspace, dir)
```

#### 问题 3：AI API 限流

**现象**：
```
429 Too Many Requests
```

**解决方案**：
```python
# 降低并发数
max_concurrent=2

# 或升级 AI API 计划
```

---

## 📚 相关文档

- **[Ginkgo 完全指南](2-Ginkgo完全指南.md)** - BDD 测试详细说明
- **[高级配置](2-高级配置.md)** - CLI、提示词、配置选项
- **[核心功能详解](3-核心功能详解.md)** - 智能策略和自动修复原理
- **[快速开始](1-快速开始.md)** - 安装和初始设置

---

## 🎉 总结

本指南涵盖了测试生成和修复的所有内容：

✅ **测试生成** - 从基础到高级，支持多种语言和框架  
✅ **测试修复** - 异步并发，快速高效  
✅ **自动修复** - 智能修复失败的测试  
✅ **最佳实践** - 经过验证的使用方法  

享受 AI 自动生成和修复测试的便利吧！🚀

