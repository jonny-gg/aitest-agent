# 🚀 快速开始

欢迎使用 AI Test Agent！本指南将帮助你在 **5 分钟内**开始使用。

---

## 📋 目录

1. [前置要求](#前置要求)
2. [安装部署](#安装部署)
3. [第一个测试](#第一个测试)
4. [验证和监控](#验证和监控)
5. [使用示例](#使用示例)
6. [常见问题](#常见问题)

---

## 📌 前置要求

在开始之前,请确保你已经安装以下工具:

| 工具 | 版本要求 | 用途 |
|------|---------|------|
| **Docker** | 20.10+ | 容器运行环境 |
| **Docker Compose** | 2.0+ | 多容器编排 |
| **Git** | 2.0+ | 代码仓库克隆 |
| **Python** | 3.7+ | 运行客户端脚本（可选） |
| **OpenAI API Key** | - | AI 测试生成（必需） |

---

## ⚡ 安装部署

### 第 1 步：克隆项目

```bash
git clone <your-repository-url>
cd aitest-agent
```

### 第 2 步：配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件
nano .env
```

**必须配置的环境变量：**

```bash
# OpenAI API 密钥（必需）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 数据库密码（建议修改）
POSTGRES_PASSWORD=your-secure-password

# 可选：Git 认证（用于自动提交）
GIT_USERNAME=your-github-username
GIT_TOKEN=your-github-token
```

### 第 3 步：启动服务

```bash
# 启动所有后端服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**应该看到以下服务运行中：**

| 服务 | 端口 | 说明 |
|------|------|------|
| `aitest-postgres` | 5432 | PostgreSQL 数据库 |
| `aitest-redis` | 6379 | Redis 缓存 |
| `aitest-api` | 8000 | FastAPI 服务 |
| `aitest-celery-worker` | - | 异步任务执行器 |
| `aitest-celery-beat` | - | 定时任务调度器 |
| `aitest-flower` | 5555 | Celery 监控面板 |

**等待服务启动**（约 30 秒）。

### 第 4 步：验证安装

```bash
# 健康检查
curl http://localhost:8000/health
# 输出: {"status":"healthy"}

# 查看 API 文档
open http://localhost:8000/docs

# 查看 Celery 监控
open http://localhost:5555
```

✅ 如果以上命令都成功,说明安装完成！

---

## 🎯 第一个测试

### 方式 1: 使用 Python 示例脚本（推荐）

这是最简单的开始方式:

```bash
# 安装 Python 依赖
pip install requests

# 运行示例脚本
python example_generate_tests.py
```

**选择测试场景：**

```
请选择测试生成场景:
1. Ginkgo BDD 测试（推荐用于 Kratos 项目）
2. 智能测试生成（基于代码复杂度）
3. 标准 Go Test（传统 table-driven 风格）
```

输入 `1` 选择 Ginkgo BDD 测试,然后按照提示输入:
- Git 仓库 URL
- 分支名称（默认 `main`）
- 源代码目录（默认 `.`）
- 测试目录（默认 `tests`）

**示例输出：**

```
============================================================
步骤 1/4: 创建项目
============================================================
✅ 项目创建成功: My Kratos Service (ID: 550e8400-xxx)

============================================================
步骤 2/4: 创建测试任务
============================================================
🚀 任务已创建: 660e8400-xxx

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
  - 生成测试文件: 46 个
  - 测试用例总数: 215
  - 通过测试: 215
  - 失败测试: 0
  - 行覆盖率: 85.30%
  - 分支覆盖率: 78.60%

🎉 全部完成!
```

### 方式 2: 使用 curl 命令

```bash
# 1. 创建项目
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Go Project",
    "git_url": "https://github.com/username/repo",
    "git_branch": "main",
    "language": "golang",
    "test_framework": "ginkgo",
    "coverage_threshold": 80.0,
    "auto_commit": true
  }'

# 记录返回的 project_id

# 2. 创建测试任务（替换 {project_id}）
curl -X POST http://localhost:8000/api/projects/{project_id}/tasks

# 记录返回的 task_id

# 3. 查询任务状态（替换 {task_id}）
curl http://localhost:8000/api/tasks/{task_id}

# 4. 获取覆盖率报告
curl http://localhost:8000/api/tasks/{task_id}/coverage
```

### 方式 3: 使用 API 交互式文档

1. 访问 http://localhost:8000/docs
2. 找到 `POST /api/projects` 接口
3. 点击 **"Try it out"**
4. 填写项目信息
5. 点击 **"Execute"** 执行

---

## 📊 验证和监控

### 1. API 交互式文档

访问：**http://localhost:8000/docs**

功能：
- ✅ 查看所有 API 接口
- ✅ 在线测试 API
- ✅ 查看请求/响应格式
- ✅ 自动生成代码示例

### 2. Flower - Celery 任务监控

访问：**http://localhost:5555**

功能：
- ✅ 实时任务状态
- ✅ Worker 运行情况
- ✅ 任务执行历史
- ✅ 失败任务重试

### 3. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看 API 日志
docker-compose logs -f api

# 查看 Worker 日志
docker-compose logs -f celery-worker

# 查看特定任务的日志
curl http://localhost:8000/api/tasks/{task_id}/logs
```

---

## 🎯 使用示例

### 示例 1: Golang Ginkgo BDD 测试

```python
import requests

API = "http://localhost:8000/api"

# 创建 Ginkgo 项目
project = requests.post(f"{API}/projects", json={
    "name": "Kratos Microservice",
    "git_url": "https://github.com/username/kratos-api",
    "language": "golang",
    "test_framework": "ginkgo",
    "coverage_threshold": 80.0
}).json()

# 触发测试生成
task = requests.post(f"{API}/projects/{project['id']}/tasks").json()

print(f"✅ 任务ID: {task['id']}")
print(f"🔗 监控地址: http://localhost:5555")
```

### 示例 2: 标准 Go Test

```python
import requests

API = "http://localhost:8000/api"

# 创建标准 Go 测试项目
project = requests.post(f"{API}/projects", json={
    "name": "Go REST API",
    "git_url": "https://github.com/username/go-api",
    "language": "golang",
    "test_framework": "go_test",  # 标准 Go 测试
    "auto_commit": true,
    "create_pr": true
}).json()

# 触发测试生成
task = requests.post(f"{API}/projects/{project['id']}/tasks").json()
```

### 示例 3: 定时任务

```bash
# 设置每天凌晨 2 点自动运行
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

---

## ❓ 常见问题

### Q1: 服务启动失败？

**解决方案：**

```bash
# 查看详细日志
docker-compose logs

# 重启服务
docker-compose restart

# 完全重建
docker-compose down
docker-compose up -d --build
```

### Q2: OpenAI API 调用失败？

**检查清单：**

1. ✅ API 密钥是否正确？
   ```bash
   cat .env | grep OPENAI_API_KEY
   ```

2. ✅ 网络是否能访问 OpenAI？
   ```bash
   curl https://api.openai.com
   ```

3. ✅ API 配额是否充足？
   - 登录 OpenAI 控制台检查余额

4. ✅ 查看详细错误：
   ```bash
   docker-compose logs api | grep -i error
   ```

### Q3: Git 仓库无法访问？

**解决方案：**

1. **检查仓库 URL** 是否正确
2. **私有仓库**需要设置 `GIT_USERNAME` 和 `GIT_TOKEN`
3. **SSH 密钥**配置（如使用 SSH URL）
4. 查看详细错误：
   ```bash
   docker-compose logs celery-worker | grep -i git
   ```

### Q4: 数据库连接失败？

```bash
# 检查 PostgreSQL 状态
docker-compose ps postgres

# 查看 PostgreSQL 日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### Q5: Celery 任务不执行？

```bash
# 检查 Worker 状态
docker-compose ps celery-worker

# 查看 Worker 日志
docker-compose logs celery-worker

# 访问 Flower 监控
open http://localhost:5555

# 重启 Worker
docker-compose restart celery-worker
```

### Q6: 测试生成的代码有语法错误？

**自动修复功能：**

系统已内置自动修复功能,包括:
- ✅ 自动修复包名
- ✅ 自动修复导入路径
- ✅ 清理 Markdown 标记
- ✅ 语法错误修复（最多 3 次尝试）

**手动修复：**

```bash
# 使用修复脚本
python example_fix_tests.py
```

详见：[测试修复指南](2-测试生成和修复.md#测试修复)

---

## 💡 使用技巧

### 技巧 1: 使用 jq 美化 JSON 输出

```bash
# 安装 jq（macOS）
brew install jq

# 使用 jq 美化输出
curl http://localhost:8000/api/projects | jq

# 提取特定字段
curl http://localhost:8000/api/tasks/{task_id} | jq '{status, progress, line_coverage}'
```

### 技巧 2: 轮询等待任务完成

```bash
#!/bin/bash
TASK_ID="your-task-id"

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
curl http://localhost:8000/api/tasks/$TASK_ID | jq
```

### 技巧 3: 批量处理多个项目

```bash
# repos.txt - 每行一个仓库 URL
https://github.com/user/repo1
https://github.com/user/repo2
https://github.com/user/repo3

# 批处理脚本
while IFS= read -r repo; do
    echo "处理: $repo"
    
    PROJECT=$(curl -s -X POST http://localhost:8000/api/projects \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$(basename $repo)\",
            \"git_url\": \"$repo\",
            \"language\": \"golang\",
            \"test_framework\": \"ginkgo\"
        }")
    
    PROJECT_ID=$(echo $PROJECT | jq -r '.id')
    curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/tasks
    
    sleep 2
done < repos.txt
```

---

## 🔄 集成到 CI/CD

### GitHub Actions

```yaml
name: Auto Generate Tests

on:
  push:
    branches: [ main ]

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Test Generation
        run: |
          curl -X POST ${{ secrets.AGENT_URL }}/api/projects/${{ secrets.PROJECT_ID }}/tasks
```

### GitLab CI

```yaml
generate_tests:
  stage: test
  script:
    - curl -X POST ${AGENT_URL}/api/projects/${PROJECT_ID}/tasks
  only:
    - main
```

---

## 📚 下一步

现在你已经成功启动了 AI Test Agent,接下来可以:

- 📖 **[测试生成和修复指南](2-测试生成和修复.md)** - 详细的生成和修复说明
- 🎯 **[Ginkgo 完全指南](2-Ginkgo完全指南.md)** - BDD 测试最佳实践
- ⚙️ **[高级配置](2-高级配置.md)** - CLI、提示词、配置选项
- 🔧 **[核心功能详解](3-核心功能详解.md)** - 智能策略和自动修复
- 🏗️ **[系统架构和 API](4-系统架构和API.md)** - 架构设计和 API 参考
- 💻 **[开发和贡献](4-开发和贡献.md)** - 参与项目开发

---

## 🛑 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据（慎用）
docker-compose down -v

# 查看资源使用
docker-compose ps
docker system df
```

---

## 🎉 成功！

恭喜你！现在已经成功启动了 AI Test Agent 后端系统！

通过以下方式使用：
- ✅ **Python 客户端** - `python example_generate_tests.py`
- ✅ **REST API** - curl/requests/任何 HTTP 客户端
- ✅ **API 文档** - http://localhost:8000/docs
- ✅ **Celery 监控** - http://localhost:5555

享受 AI 自动生成测试的便利吧！🚀

