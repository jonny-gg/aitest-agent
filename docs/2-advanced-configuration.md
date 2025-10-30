# ⚙️ 高级配置指南

本指南介绍 AI Test Agent 的高级配置和使用方法，包括命令行工具、提示词自定义、配置选项等。

---

## 📋 目录

1. [命令行工具使用](#命令行工具使用)
2. [提示词管理](#提示词管理)
3. [配置选项](#配置选项)
4. [常见问题 FAQ](#常见问题-faq)

---

## 命令行工具使用

本系统是一个**纯后端 Agent**，通过 REST API 提供服务，无需前端界面。

### 使用方式

#### 方式 1: Python 客户端（推荐）

```bash
# 编辑 example_client.py，设置你的项目信息
vim example_client.py

# 运行客户端
python example_client.py
```

**示例输出：**

```
============================================================
步骤 1/4: 创建项目
============================================================
✅ 项目创建成功: My Go API (ID: abc-123)

============================================================
步骤 2/4: 创建测试任务
============================================================
🚀 任务已创建: def-456

============================================================
步骤 3/4: 执行测试生成（这可能需要几分钟）
============================================================
[10%] 状态: cloning
[30%] 状态: analyzing
[50%] 状态: generating
[70%] 状态: testing
[85%] 状态: collecting_coverage
[95%] 状态: committing
[100%] 状态: completed

============================================================
步骤 4/4: 结果总结
============================================================
✅ 任务完成!

📊 统计信息:
  - 生成测试文件: 8 个
  - 测试用例总数: 45
  - 通过测试: 45
  - 失败测试: 0
  - 行覆盖率: 87.50%
  - 分支覆盖率: 82.30%
```

#### 方式 2: curl 命令

**创建项目：**

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Project",
    "git_url": "https://github.com/username/repo",
    "git_branch": "main",
    "language": "golang",
    "test_framework": "go_test",
    "coverage_threshold": 80.0,
    "auto_commit": true
  }'
```

**触发测试任务：**

```bash
PROJECT_ID="550e8400-e29b-41d4-a716-446655440000"
curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/tasks
```

**查询任务状态：**

```bash
TASK_ID="660e8400-e29b-41d4-a716-446655440001"
curl http://localhost:8000/api/tasks/$TASK_ID | jq
```

**轮询直到完成：**

```bash
#!/bin/bash
TASK_ID="660e8400-e29b-41d4-a716-446655440001"

while true; do
    STATUS=$(curl -s http://localhost:8000/api/tasks/$TASK_ID | jq -r '.status')
    PROGRESS=$(curl -s http://localhost:8000/api/tasks/$TASK_ID | jq -r '.progress')
    
    echo "[$PROGRESS%] 状态: $STATUS"
    
    if [[ "$STATUS" == "completed" ]] || [[ "$STATUS" == "failed" ]]; then
        break
    fi
    
    sleep 5
done

# 显示最终结果
curl -s http://localhost:8000/api/tasks/$TASK_ID | jq '{
    status,
    generated_tests,
    total_tests,
    passed_tests,
    line_coverage
}'
```

#### 方式 3: Python requests 库

```python
import requests
import time

API_BASE = "http://localhost:8000/api"

# 创建项目
project = requests.post(f"{API_BASE}/projects", json={
    "name": "My Project",
    "git_url": "https://github.com/username/repo",
    "language": "golang",
    "test_framework": "go_test"
}).json()

project_id = project['id']

# 创建任务
task = requests.post(f"{API_BASE}/projects/{project_id}/tasks").json()
task_id = task['id']

# 等待完成
while True:
    task = requests.get(f"{API_BASE}/tasks/{task_id}").json()
    print(f"[{task['progress']}%] {task['status']}")
    
    if task['status'] in ['completed', 'failed']:
        break
    
    time.sleep(5)

# 显示结果
if task['status'] == 'completed':
    print(f"✅ 完成! 覆盖率: {task['line_coverage']}%")
    
    # 获取详细覆盖率
    coverage = requests.get(f"{API_BASE}/tasks/{task_id}/coverage").json()
    print(coverage)
```

### 监控界面

虽然没有 Web 前端，但你可以使用：

#### 1. Swagger API 文档

访问：**http://localhost:8000/docs**

- 交互式 API 测试
- 完整的接口文档
- 在线调试

#### 2. Flower 监控

访问：**http://localhost:5555**

- Celery 任务队列监控
- Worker 状态
- 任务执行历史
- 失败任务重试

#### 3. 日志查看

```bash
# 实时查看所有日志
docker-compose logs -f

# 查看 API 日志
docker-compose logs -f api

# 查看 Worker 日志
docker-compose logs -f celery-worker

# 查看特定任务的日志
curl http://localhost:8000/api/tasks/$TASK_ID/logs | jq
```

### 高级用法

#### 定时任务

设置 cron 表达式，Agent 自动定时运行：

```bash
curl -X PUT http://localhost:8000/api/projects/$PROJECT_ID \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_cron": "0 2 * * *",
    "enabled": true
  }'
```

**常用 cron 表达式：**

| 表达式 | 说明 |
|--------|------|
| `0 2 * * *` | 每天凌晨 2 点 |
| `0 9 * * 1` | 每周一上午 9 点 |
| `0 */6 * * *` | 每 6 小时 |
| `*/30 * * * *` | 每 30 分钟 |

#### 批量处理

```bash
#!/bin/bash

# 项目列表
PROJECTS=(
    "https://github.com/user/repo1"
    "https://github.com/user/repo2"
    "https://github.com/user/repo3"
)

# 批量创建并运行
for REPO in "${PROJECTS[@]}"; do
    echo "处理: $REPO"
    
    # 创建项目
    PROJECT=$(curl -s -X POST http://localhost:8000/api/projects \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$(basename $REPO)\",
            \"git_url\": \"$REPO\",
            \"language\": \"golang\",
            \"test_framework\": \"go_test\"
        }")
    
    PROJECT_ID=$(echo $PROJECT | jq -r '.id')
    
    # 创建任务
    curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/tasks
    
    sleep 2
done
```

#### WebSocket 实时监控

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"[{data['progress']}%] {data['status']}: {data['message']}")

def on_error(ws, error):
    print(f"错误: {error}")

def on_close(ws):
    print("连接关闭")

task_id = "your-task-id"
ws = websocket.WebSocketApp(
    f"ws://localhost:8000/ws/tasks/{task_id}/stream",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()
```

### 集成到其他系统

#### GitHub Actions

```yaml
- name: Generate Tests
  run: |
    TASK=$(curl -X POST https://agent.example.com/api/projects/$PROJECT_ID/tasks)
    TASK_ID=$(echo $TASK | jq -r '.id')
    
    # 等待完成
    while true; do
      STATUS=$(curl -s https://agent.example.com/api/tasks/$TASK_ID | jq -r '.status')
      if [[ "$STATUS" == "completed" ]]; then
        break
      fi
      sleep 10
    done
```

#### GitLab CI

```yaml
generate_tests:
  script:
    - curl -X POST https://agent.example.com/api/projects/$PROJECT_ID/tasks
```

#### Jenkins

```groovy
pipeline {
    stages {
        stage('Generate Tests') {
            steps {
                script {
                    def response = sh(
                        script: "curl -X POST http://agent:8000/api/projects/${PROJECT_ID}/tasks",
                        returnStdout: true
                    ).trim()
                    
                    def task = readJSON text: response
                    echo "任务ID: ${task.id}"
                }
            }
        }
    }
}
```

### API 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/projects` | 创建项目 |
| GET | `/api/projects` | 项目列表 |
| GET | `/api/projects/:id` | 项目详情 |
| PUT | `/api/projects/:id` | 更新项目 |
| POST | `/api/projects/:id/tasks` | 创建任务 |
| GET | `/api/tasks/:id` | 任务详情 |
| GET | `/api/tasks/:id/logs` | 任务日志 |
| GET | `/api/tasks/:id/coverage` | 覆盖率报告 |
| GET | `/api/dashboard/stats` | 统计数据 |

---

## 提示词管理

AI Test Agent 采用**集中式提示词管理**架构，所有 AI 提示词都集中在 `backend/app/services/prompt_templates.py` 文件中管理。

### 设计理念

**为什么要集中管理提示词？**

1. **统一标准** - 确保所有测试生成使用一致的提示词策略
2. **易于维护** - 修改提示词只需要编辑一个文件
3. **版本控制** - 提示词的变更历史清晰可追踪
4. **质量保证** - 经过验证的提示词模板保证生成质量
5. **安全可控** - 避免客户端传入不安全或低质量的提示词

### 文件结构

```
backend/app/services/
├── prompt_templates.py    # 提示词模板管理
├── test_generator.py      # 测试生成器（使用提示词模板）
├── test_case_strategy.py  # 测试用例策略
└── ...
```

### 提示词模板类

所有提示词模板都通过 `PromptTemplates` 类管理：

```python
from app.services.prompt_templates import get_prompt_templates

# 获取提示词模板实例
templates = get_prompt_templates()

# 使用 Golang 标准测试提示词
prompt = templates.golang_standard_test(
    func_name="Calculate",
    func_body="return a + b",
    params=["a int", "b int"],
    return_type="int",
    receiver=""
)

# 使用 Ginkgo BDD 测试提示词
prompt = templates.golang_ginkgo_test(
    func_name="CreateUser",
    func_body="...",
    params=["ctx context.Context", "req *pb.CreateUserRequest"],
    return_type="(*pb.CreateUserReply, error)",
    receiver="*UserService",
    module_path="github.com/example/myproject",
    package_name="service",
    file_path="internal/service/user.go"
)
```

### 可用的提示词模板

#### Golang 测试

| 方法名 | 用途 | 框架 |
|--------|------|------|
| `golang_standard_test()` | Go 标准测试 | testing |
| `golang_ginkgo_test()` | Ginkgo BDD 测试 | ginkgo/gomega |
| `golang_ginkgo_file_test()` | 整个文件的 Ginkgo 测试 | ginkgo/gomega |
| `golang_fix_test()` | 修复失败的测试 | 通用 |
| `golang_syntax_fix()` | 修复语法错误 | 通用 |

#### C++ 测试

| 方法名 | 用途 | 框架 |
|--------|------|------|
| `cpp_google_test()` | Google Test | gtest |
| `cpp_fix_test()` | 修复失败的测试 | 通用 |

#### C 测试

| 方法名 | 用途 | 框架 |
|--------|------|------|
| `c_unit_test()` | C 单元测试 | CUnit/其他 |
| `c_fix_test()` | 修复失败的测试 | 通用 |

### 如何定制提示词

#### 方法 1: 修改现有模板

编辑 `backend/app/services/prompt_templates.py` 文件：

```python
@staticmethod
def golang_ginkgo_test(
    func_name: str,
    func_body: str,
    params: List[str],
    return_type: str,
    receiver: str,
    module_path: str,
    package_name: str,
    file_path: str
) -> str:
    """Ginkgo BDD 测试框架提示词"""
    return f"""请为以下Go函数生成基于Ginkgo/Gomega的BDD风格单元测试。

## 项目信息
- Go模块路径: {module_path}
- 包名: {package_name}

## 目标函数
```go
func {func_name}({', '.join(params)}) {return_type} {{
{func_body}
}}
```

## 你的定制规则
1. 使用特定的命名约定
2. 添加额外的测试场景
3. 使用特定的断言风格
...

请只返回测试代码，不要包含额外的解释。
"""
```

#### 方法 2: 添加新的模板

在 `PromptTemplates` 类中添加新方法：

```python
@staticmethod
def golang_custom_framework_test(
    func_name: str,
    func_body: str,
    custom_param: str
) -> str:
    """自定义测试框架提示词"""
    return f"""
    为 {func_name} 生成使用自定义框架的测试
    
    自定义参数: {custom_param}
    
    函数体:
    {func_body}
    """
```

### 提示词更新流程

**1. 修改提示词模板**

编辑 `prompt_templates.py` 文件，修改相应的提示词方法。

**2. 测试验证**

```bash
# 重启服务
docker-compose restart api celery-worker

# 运行测试
python example_generate_tests.py
```

**3. 版本控制**

```bash
git add backend/app/services/prompt_templates.py
git commit -m "优化: 更新 Ginkgo 测试提示词模板"
```

### 提示词设计最佳实践

#### 1. 结构清晰

```python
def your_prompt_template(...) -> str:
    return f"""
## 第一部分：上下文信息
- 项目信息
- 代码上下文

## 第二部分：目标代码
```language
{code}
```

## 第三部分：规则要求
1. 规则1
2. 规则2

## 第四部分：示例格式
```language
// 示例代码
```

## 第五部分：输出要求
请只返回代码，不要包含额外解释。
"""
```

#### 2. 参数化设计

使用参数而不是硬编码：

```python
# ✅ 好的设计
def good_prompt(module_path: str, package_name: str) -> str:
    return f"使用模块路径: {module_path}, 包名: {package_name}"

# ❌ 不好的设计
def bad_prompt() -> str:
    return "使用模块路径: github.com/example/project"
```

#### 3. 包含示例

在提示词中包含具体的代码示例：

```python
## 示例格式
```go
var _ = Describe("UserService", func() {{
    Context("when creating user", func() {{
        It("should succeed", func() {{
            Expect(err).NotTo(HaveOccurred())
        }})
    }})
}})
```
```

#### 4. 明确约束

明确说明什么能做、什么不能做：

```python
## 导入规则
**只导入这些包**:
- testing
- ginkgo/v2
- gomega

**不要导入**:
- ❌ 项目内部包
- ❌ mock 包
```

---

## 配置选项

### 环境变量配置

编辑 `.env` 文件：

```bash
# OpenAI API 密钥（必需）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 数据库配置
POSTGRES_DB=aitest
POSTGRES_USER=aitest
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Git 认证（用于自动提交）
GIT_USERNAME=your-github-username
GIT_TOKEN=your-github-token

# AI 配置
AI_MODEL=gpt-4
AI_TEMPERATURE=0.3
MAX_TEST_FIX_RETRIES=3
ENABLE_AUTO_FIX=true

# 日志级别
LOG_LEVEL=INFO
```

### 项目配置参数

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
| `schedule_cron` | string | null | 定时任务表达式 |
| `enabled` | boolean | true | 是否启用 |

### 配置管理命令

**查看所有项目：**

```bash
curl http://localhost:8000/api/projects | jq
```

**更新项目配置：**

```bash
curl -X PUT http://localhost:8000/api/projects/$PROJECT_ID \
  -H "Content-Type: application/json" \
  -d '{
    "coverage_threshold": 85.0,
    "auto_commit": false
  }'
```

**删除项目：**

```bash
curl -X DELETE http://localhost:8000/api/projects/$PROJECT_ID
```

---

## 常见问题 FAQ

### Q1: 为什么不让客户端自定义提示词？

**A:** 集中管理提示词有以下优势：
1. 保证生成质量的一致性
2. 防止不安全的提示词注入
3. 便于统一优化和维护
4. 确保符合项目规范

### Q2: 如何为特定项目定制提示词？

**A:** 有两种方式：
1. 修改 `prompt_templates.py` 文件（推荐）
2. 通过项目配置参数影响提示词内容

### Q3: 提示词修改后需要重启服务吗？

**A:** 是的，修改后需要重启 api 和 celery-worker 服务：

```bash
docker-compose restart api celery-worker
```

### Q4: 如何测试新的提示词？

**A:** 使用示例脚本测试：

```bash
python example_generate_tests.py
```

### Q5: 如何查看详细的 API 文档？

**A:** 访问 Swagger UI：

```
http://localhost:8000/docs
```

### Q6: 如何监控任务执行状态？

**A:** 访问 Flower 监控面板：

```
http://localhost:5555
```

### Q7: 如何设置定时任务？

**A:** 使用 cron 表达式：

```bash
curl -X PUT http://localhost:8000/api/projects/$PROJECT_ID \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_cron": "0 2 * * *",
    "enabled": true
  }'
```

### Q8: 如何批量处理多个项目？

**A:** 使用脚本循环处理：

```bash
for REPO in repo1 repo2 repo3; do
    # 创建项目并触发任务
    curl -X POST http://localhost:8000/api/projects ...
done
```

### Q9: 如何集成到 CI/CD？

**A:** 参考 [集成到其他系统](#集成到其他系统) 章节。

### Q10: 如何调整并发数？

**A:** 修改 `backend/app/services/test_fixer.py` 中的 `max_concurrent` 参数。

---

## 💡 最佳实践

1. **使用 Python 客户端** - 提供了完整的错误处理和进度显示
2. **设置合理的超时** - 大型项目可能需要更长时间
3. **监控 Flower** - 及时发现和处理失败的任务
4. **查看日志** - 遇到问题时第一时间查看详细日志
5. **合理设置覆盖率阈值** - 根据项目实际情况调整
6. **使用 jq 工具** - 美化 JSON 输出，提高可读性
7. **定期备份配置** - 使用 Git 管理配置文件
8. **分批处理大项目** - 避免一次性生成过多测试

---

## 📚 相关文档

- **[快速开始](1-快速开始.md)** - 安装和初始设置
- **[测试生成和修复](2-测试生成和修复.md)** - 核心功能使用
- **[Ginkgo 完全指南](2-Ginkgo完全指南.md)** - BDD 测试详解
- **[核心功能详解](3-核心功能详解.md)** - 智能策略和自动修复
- **[系统架构和 API](4-系统架构和API.md)** - 架构设计和 API 参考

---

## 🎉 总结

本指南涵盖了 AI Test Agent 的高级配置：

✅ **命令行工具** - 多种使用方式，灵活调用  
✅ **提示词管理** - 集中管理，易于定制  
✅ **配置选项** - 丰富的参数，满足不同需求  
✅ **常见问题** - 快速解决常见疑问  

掌握这些高级配置，您可以充分发挥 AI Test Agent 的强大功能！🚀

