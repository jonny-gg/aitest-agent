# 🏗️ 系统架构和 API 参考

本指南介绍 AI Test Agent 的系统架构设计和 API 接口。

---

## 📋 目录

1. [系统架构](#系统架构)
2. [核心组件](#核心组件)
3. [API 参考](#api-参考)
4. [技术栈](#技术栈)

---

## 系统架构

### 整体架构

AI Test Agent 采用微服务架构，主要由以下组件构成：

```
┌─────────────────────────────────────────────────────────┐
│                      用户层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ CLI 客户端│  │ API 客户端│  │ Swagger UI│              │
│  └──────────┘  └──────────┘  └──────────┘              │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/WebSocket
┌──────────────────┴──────────────────────────────────────┐
│                  API 网关层                               │
│  ┌─────────────────────────────────────────────┐        │
│  │      FastAPI (8000)                          │        │
│  │  - REST API 端点                              │        │
│  │  - WebSocket 实时通信                         │        │
│  │  - Swagger 文档                               │        │
│  └─────────────────────────────────────────────┘        │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│                  业务逻辑层                               │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │ Test Agent   │  │ Test Fixer   │                    │
│  │ 测试生成引擎  │  │ 修复引擎      │                    │
│  └──────────────┘  └──────────────┘                    │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │ Code Analyzer│  │ Test Runner  │                    │
│  │ 代码分析器    │  │ 测试执行器    │                    │
│  └──────────────┘  └──────────────┘                    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│                  任务队列层                               │
│  ┌─────────────────────────────────────────────┐        │
│  │      Celery + Redis                          │        │
│  │  - 异步任务队列                               │        │
│  │  - 定时任务                                   │        │
│  │  - 任务调度                                   │        │
│  └─────────────────────────────────────────────┘        │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│                  数据存储层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │PostgreSQL│  │  Redis   │  │File System│              │
│  │项目/任务  │  │  缓存    │  │ 工作空间  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────┐
│                  外部服务层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ OpenAI   │  │  GitHub  │  │  GitLab  │              │
│  │   API    │  │   API    │  │   API    │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
1. 用户创建项目 → API 层 → 存储到 PostgreSQL
2. 触发测试任务 → Celery 异步任务
3. Clone Git 仓库 → 本地工作空间
4. 分析代码 → 提取函数信息
5. 调用 OpenAI API → 生成测试代码
6. 保存测试文件 → 本地文件系统
7. 执行测试 → 收集结果
8. 提交代码 → Git Push
9. 更新任务状态 → PostgreSQL
10. WebSocket 推送 → 实时通知用户
```

---

## 核心组件

### 1. FastAPI 服务 (aitest-api)

**功能**：
- RESTful API 端点
- WebSocket 实时通信
- Swagger 文档
- 请求验证和错误处理

**主要模块**：
- `app/api/` - API 路由和端点
- `app/models/` - 数据模型
- `app/schemas/` - Pydantic 模式
- `app/db/` - 数据库连接

### 2. Celery Worker (aitest-celery-worker)

**功能**：
- 异步任务执行
- 长时间运行的任务
- 并发处理
- 任务重试机制

**主要任务**：
- `generate_tests_task` - 生成测试
- `run_tests_task` - 执行测试
- `collect_coverage_task` - 收集覆盖率
- `fix_tests_task` - 修复测试

### 3. Test Generator (测试生成器)

**文件**：`backend/app/services/test_generator.py`

**功能**：
- 代码分析
- 测试用例生成
- 导入路径处理
- 包名推断
- 自动修复

**核心方法**：
- `generate_tests_for_file()` - 为单个文件生成测试
- `_build_prompt()` - 构建 AI 提示词
- `_auto_fix_test_code()` - 自动修复生成的代码
- `_clean_internal_imports()` - 清理内部导入

### 4. Test Fixer (测试修复器)

**文件**：`backend/app/services/test_fixer.py`

**功能**：
- 语法错误检测
- AI 驱动修复
- 异步并发修复
- 修复结果验证

**核心方法**：
- `fix_tests_in_directory_async()` - 异步批量修复
- `_fix_single_test_file_async()` - 修复单个文件
- `_validate_test_file()` - 验证测试文件

### 5. Code Analyzer (代码分析器)

**文件**：`backend/app/services/code_analyzer.py`

**功能**：
- 代码解析
- 函数提取
- 复杂度计算
- 可执行行数统计

**核心功能**：
- 提取函数信息（名称、参数、返回值）
- 计算圈复杂度
- 统计可执行代码行数
- 识别函数类型

### 6. Prompt Templates (提示词模板)

**文件**：`backend/app/services/prompt_templates.py`

**功能**：
- 集中管理 AI 提示词
- 多语言支持
- 多框架支持
- 版本控制

**模板类型**：
- Golang 标准测试
- Golang Ginkgo BDD 测试
- C++ Google Test
- C Unit Test

---

## API 参考

### 健康检查

```http
GET /health
```

**响应**：
```json
{
  "status": "healthy"
}
```

### 项目管理

#### 创建项目

```http
POST /api/projects
Content-Type: application/json

{
  "name": "My Project",
  "git_url": "https://github.com/username/repo",
  "git_branch": "main",
  "language": "golang",
  "test_framework": "ginkgo",
  "coverage_threshold": 80.0,
  "auto_commit": true
}
```

**响应**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Project",
  "language": "golang",
  "test_framework": "ginkgo",
  "enabled": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 获取项目列表

```http
GET /api/projects
```

#### 获取项目详情

```http
GET /api/projects/{project_id}
```

#### 更新项目

```http
PUT /api/projects/{project_id}
Content-Type: application/json

{
  "coverage_threshold": 85.0,
  "auto_commit": false
}
```

#### 删除项目

```http
DELETE /api/projects/{project_id}
```

### 任务管理

#### 创建测试任务

```http
POST /api/projects/{project_id}/tasks
```

**响应**：
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "created_at": "2024-01-15T10:35:00Z"
}
```

#### 获取任务状态

```http
GET /api/tasks/{task_id}
```

**响应**：
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "commit_hash": "abc123def456",
  "generated_tests": [
    "/workspace/project/tests/user_test.go",
    "/workspace/project/tests/auth_test.go"
  ],
  "total_tests": 15,
  "passed_tests": 15,
  "failed_tests": 0,
  "line_coverage": 87.5,
  "branch_coverage": 82.3,
  "completed_at": "2024-01-15T10:45:00Z"
}
```

#### 获取任务日志

```http
GET /api/tasks/{task_id}/logs
```

#### 获取覆盖率报告

```http
GET /api/tasks/{task_id}/coverage
```

**响应**：
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "task_id": "660e8400-e29b-41d4-a716-446655440001",
  "total_lines": 1200,
  "covered_lines": 1050,
  "line_coverage": 87.5,
  "total_branches": 150,
  "covered_branches": 123,
  "branch_coverage": 82.0,
  "files_coverage": {
    "user.go": 95.2,
    "auth.go": 88.7,
    "handler.go": 82.3
  }
}
```

### 测试修复

#### 修复测试文件

```http
POST /api/tasks/fix-tests
Content-Type: application/json

{
  "workspace_path": "/app/workspace/a5db9f32-xxx",
  "test_directory": "internal/biz",
  "language": "golang",
  "test_framework": "ginkgo",
  "max_fix_attempts": 3
}
```

**响应**：
```json
{
  "success": true,
  "total_files": 46,
  "fixed_files": 12,
  "failed_files": 0,
  "skipped_files": 34,
  "message": "完成! 总计: 46, 修复: 12, 失败: 0, 跳过: 34"
}
```

### WebSocket

#### 实时任务状态

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks/{task_id}/stream');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log({
        progress: data.progress,
        status: data.status,
        message: data.message
    });
};
```

---

## 技术栈

### 后端

- **Python 3.9+** - 主要编程语言
- **FastAPI** - Web 框架
- **Celery** - 异步任务队列
- **PostgreSQL** - 关系数据库
- **Redis** - 缓存和消息队列
- **SQLAlchemy** - ORM
- **Pydantic** - 数据验证

### 测试工具

- **Ginkgo/Gomega** - Go BDD 测试框架
- **gofmt** - Go 代码格式化
- **go test** - Go 测试运行器
- **Google Test** - C++ 测试框架

### AI 集成

- **OpenAI API** - GPT-4 模型
- **Anthropic Claude** - 可选的 AI 模型

### 部署

- **Docker** - 容器化
- **Docker Compose** - 多容器编排
- **Nginx** - 反向代理（可选）

### 监控

- **Flower** - Celery 监控
- **Swagger UI** - API 文档
- **Loguru** - 日志系统

---

## 📚 相关文档

- **[快速开始](1-快速开始.md)** - 安装和初始设置
- **[开发和贡献](4-开发和贡献.md)** - 开发环境和贡献指南
- **[高级配置](2-高级配置.md)** - 命令行和配置选项

---

## 🎉 总结

AI Test Agent 采用现代化的微服务架构：

✅ **模块化设计** - 各组件职责清晰，易于维护  
✅ **异步处理** - Celery 队列支持高并发  
✅ **RESTful API** - 标准化的 API 接口  
✅ **实时通信** - WebSocket 推送任务状态  
✅ **可扩展性** - 易于添加新功能和集成  

通过了解系统架构，您可以更好地使用和扩展 AI Test Agent！🚀

