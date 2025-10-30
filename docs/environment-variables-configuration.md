# 环境变量配置说明

## 📋 概述

AI Test Agent 的所有配置都可以通过环境变量进行修改，包括并发数、超时时间等关键参数。

## 🚀 快速开始

### 1. 创建配置文件

```bash
cp env.example .env
```

### 2. 编辑配置

根据你的需求修改 `.env` 文件中的配置项。

### 3. 重启服务

```bash
docker-compose restart api celery-worker
```

## ⚙️ 并发配置

### MAX_CONCURRENT_GENERATIONS

**说明**：同时生成多少个测试文件

**默认值**：`10`

**推荐值**：
- 小型项目（< 20 文件）：`5-10`
- 中型项目（20-100 文件）：`10-15`
- 大型项目（> 100 文件）：`15-20`

**影响**：
- ✅ 值越大，生成速度越快
- ⚠️ 值越大，消耗更多 API tokens 和内存

**示例**：
```bash
# 快速生成（适合大项目）
MAX_CONCURRENT_GENERATIONS=20

# 节省成本（适合小项目）
MAX_CONCURRENT_GENERATIONS=5
```

---

### MAX_CONCURRENT_TASKS

**说明**：系统同时处理的测试生成任务数

**默认值**：`5`

**推荐值**：
- 单用户/小团队：`3-5`
- 多用户/中团队：`5-8`
- 大团队/高负载：`8-10`

**影响**：
- ✅ 值越大，可以同时运行更多任务
- ⚠️ 需要配合服务器资源调整

**示例**：
```bash
# 单用户开发环境
MAX_CONCURRENT_TASKS=3

# 团队生产环境
MAX_CONCURRENT_TASKS=10
```

---

### CELERY_WORKER_CONCURRENCY

**说明**：每个 Worker 进程的并发执行线程数

**默认值**：`4`

**推荐值**（根据CPU核心数）：
- 2核CPU：`2-4`
- 4核CPU：`4-6`
- 8核及以上：`6-8`

**💡 建议**：设置为 CPU 核心数

**示例**：
```bash
# 查看CPU核心数
nproc

# 4核CPU
CELERY_WORKER_CONCURRENCY=4

# 8核CPU
CELERY_WORKER_CONCURRENCY=8
```

---

## ⏱️ 超时配置

### CELERY_TASK_TIME_LIMIT

**说明**：单个测试生成任务的最大执行时间（秒）

**默认值**：`7200`（2小时）

**推荐值**：
- 小型项目：`3600`（1小时）
- 中型项目：`7200`（2小时）
- 大型项目：`10800`（3小时）

**影响**：
- ⚠️ 超过此时间任务将被强制终止
- ✅ 防止任务无限运行占用资源

**示例**：
```bash
# 大型项目
CELERY_TASK_TIME_LIMIT=10800

# 快速测试
CELERY_TASK_TIME_LIMIT=1800
```

---

### TEST_EXECUTION_TIMEOUT

**说明**：单次测试执行的超时时间（秒）

**默认值**：`300`（5分钟）

**推荐值**：
- 快速单元测试：`180`（3分钟）
- 普通测试：`300`（5分钟）
- 复杂集成测试：`600`（10分钟）

**示例**：
```bash
# 快速单元测试
TEST_EXECUTION_TIMEOUT=180

# 复杂测试
TEST_EXECUTION_TIMEOUT=600
```

---

### GINKGO_INSTALL_TIMEOUT

**说明**：安装 Ginkgo 测试框架的超时时间（秒）

**默认值**：`300`（5分钟）

**推荐值**：
- 网络良好：`300`
- 网络较慢：`600`

**示例**：
```bash
# 网络慢的环境
GINKGO_INSTALL_TIMEOUT=600
```

---

## 📊 配置方案推荐

### 方案 1：开发环境（单用户）

```bash
# 并发配置
MAX_CONCURRENT_GENERATIONS=5
MAX_CONCURRENT_TASKS=3
CELERY_WORKER_CONCURRENCY=2

# 超时配置
CELERY_TASK_TIME_LIMIT=3600
TEST_EXECUTION_TIMEOUT=300
GINKGO_INSTALL_TIMEOUT=300
```

**适用场景**：
- 个人开发
- 小项目测试
- 资源有限的环境

---

### 方案 2：测试环境（小团队）

```bash
# 并发配置
MAX_CONCURRENT_GENERATIONS=10
MAX_CONCURRENT_TASKS=5
CELERY_WORKER_CONCURRENCY=4

# 超时配置
CELERY_TASK_TIME_LIMIT=7200
TEST_EXECUTION_TIMEOUT=300
GINKGO_INSTALL_TIMEOUT=300
```

**适用场景**：
- 3-10人团队
- 中小型项目
- 一般服务器配置

---

### 方案 3：生产环境（大团队）

```bash
# 并发配置
MAX_CONCURRENT_GENERATIONS=20
MAX_CONCURRENT_TASKS=10
CELERY_WORKER_CONCURRENCY=8

# 超时配置
CELERY_TASK_TIME_LIMIT=10800
TEST_EXECUTION_TIMEOUT=600
GINKGO_INSTALL_TIMEOUT=600
```

**适用场景**：
- 大型团队
- 大型项目
- 高性能服务器

---

## 🔍 监控和调优

### 查看当前配置

```bash
# 进入容器
docker exec -it aitest-api bash

# 查看环境变量
env | grep -E "MAX_CONCURRENT|CELERY|TIMEOUT"
```

### 监控 Celery Worker

```bash
# 查看 Worker 状态
docker-compose logs -f celery-worker

# 访问 Flower 监控面板
# http://localhost:5555
```

### 性能指标

**查看任务执行时间**：
```bash
docker-compose logs celery-worker | grep "任务完成"
```

**查看并发情况**：
```bash
docker-compose logs celery-worker | grep "开始执行任务"
```

---

## 💡 调优建议

### 1. CPU 密集型任务

如果任务主要消耗 CPU：
- 增加 `CELERY_WORKER_CONCURRENCY`
- 减少 `MAX_CONCURRENT_GENERATIONS`

### 2. 内存密集型任务

如果内存占用高：
- 减少 `MAX_CONCURRENT_GENERATIONS`
- 减少 `MAX_CONCURRENT_TASKS`

### 3. API 限流

如果遇到 API 限流：
- 减少 `MAX_CONCURRENT_GENERATIONS`
- 增加任务间隔

### 4. 网络较慢

如果网络不稳定：
- 增加所有超时值
- 减少并发数

---

## 🚨 常见问题

### Q1: 任务经常超时怎么办？

**解决方案**：
```bash
# 增加超时时间
CELERY_TASK_TIME_LIMIT=14400  # 4小时
TEST_EXECUTION_TIMEOUT=600  # 10分钟
```

### Q2: 服务器内存不足怎么办？

**解决方案**：
```bash
# 减少并发
MAX_CONCURRENT_GENERATIONS=5
MAX_CONCURRENT_TASKS=3
CELERY_WORKER_CONCURRENCY=2
```

### Q3: API 频繁报错怎么办？

**解决方案**：
```bash
# 降低并发，避免超过 API 限制
MAX_CONCURRENT_GENERATIONS=5
```

### Q4: 如何最大化速度？

**解决方案**：
```bash
# 高并发配置（需要足够资源）
MAX_CONCURRENT_GENERATIONS=20
MAX_CONCURRENT_TASKS=10
CELERY_WORKER_CONCURRENCY=8
```

---

## 📚 相关文档

- [快速开始](../1-快速开始.md)
- [系统架构和API](../4-系统架构和API.md)
- [CHANGELOG.md](../CHANGELOG.md)

---

## 🎯 最佳实践

1. **从默认值开始**：不要一开始就设置很高的并发
2. **监控资源使用**：观察 CPU、内存、网络使用情况
3. **逐步调整**：根据实际情况慢慢增加并发
4. **记录配置**：记录不同项目的最佳配置
5. **环境隔离**：开发环境和生产环境使用不同的配置

---

**修改配置后记得重启服务**：
```bash
docker-compose restart api celery-worker
```

