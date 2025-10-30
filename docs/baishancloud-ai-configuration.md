# 百山云 AI 配置说明

## 概述

百山云 AI 是一个兼容 OpenAI API 格式的国内 LLM 服务平台，具有以下优势：

- ✅ **OpenAI 兼容**：无缝迁移现有应用
- ✅ **超低延迟**：平均响应 <300ms，QPS 支持 1000+
- ✅ **多语言生成**：中文、英文、德语等 100+ 语言
- ✅ **代码专精**：支持多种编程语言生成与修复
- ✅ **免费使用**：内部提供的模型可免费使用

## 支持的模型

### 通用大语言模型

| 模型名称 | 类别 | 推荐用途 |
|---------|------|---------|
| **GLM-4.5** | 通用大语言模型 | ⭐ 代码生成、测试编写 |
| **Qwen3-235B-A22B-2507** | 通用大语言模型 | ⭐ 复杂代码逻辑、高质量测试 |
| **DeepSeek-V3** | 通用大语言模型 | 深度推理、复杂问题 |
| Qwen3-32B-FP8 | 通用大语言模型 | 通用任务 |
| Qwen2.5-72B-Instruct | 通用大语言模型 | 指令遵循 |
| Kimi-K2-Instruct | 通用大语言模型 | 长上下文 |

### 代码专用模型

| 模型名称 | 类别 | 推荐用途 |
|---------|------|---------|
| **Qwen3-Coder-480B-A35B-Instruct** | 代码模型 | 代码生成、测试编写 |

### 其他模型

- **检索增强模型**：BAAI/bge-m3
- **重排序模型**：bge-reranker-v2-m3, Qwen3-Reranker 系列
- **蒸馏模型**：DeepSeek-R1 系列
- **视觉语言模型**：Qwen2.5-VL-7B-Instruct

## 配置步骤

### 1. 获取 API Key

1. 登录百山云控制台：https://ai.baishan.com/
2. 进入 **个人中心 > API 密钥**
3. 创建或查看 API Key
4. 复制完整的 Key（包含 `sk-` 前缀）

示例返回数据：
```json
{
  "data": {
    "key": "sk-xxx",
    "display_key": "sk-xxx",
    "models": "Qwen3-235B-A22B-2507,Qwen3-32B-FP8,GLM-4.5,DeepSeek-V3",
    "unlimited_quota": true
  }
}
```

### 2. 配置环境变量

在 `.env` 文件中配置：

```bash
# AI提供商选择
AI_PROVIDER=baishan

# 百山云 AI 配置
BAISHAN_API_KEY=sk-your-baishan-api-key-here  # 替换为你的 API Key
BAISHAN_MODEL=GLM-4.5                          # 推荐模型
BAISHAN_BASE_URL=https://api.edgefn.net/v1    # 固定地址
```

### 3. 推荐配置

#### 代码生成推荐配置

```bash
AI_PROVIDER=baishan
BAISHAN_API_KEY=sk-your-api-key
BAISHAN_MODEL=GLM-4.5
BAISHAN_BASE_URL=https://api.edgefn.net/v1
```

**适用场景**：
- Go 单元测试生成
- C/C++ 测试生成
- 代码修复和优化

#### 复杂逻辑推荐配置

```bash
AI_PROVIDER=baishan
BAISHAN_API_KEY=sk-your-api-key
BAISHAN_MODEL=Qwen3-235B-A22B-2507
BAISHAN_BASE_URL=https://api.edgefn.net/v1
```

**适用场景**：
- 复杂业务逻辑测试
- 高覆盖率测试生成
- 深度代码分析

## API 接口详情

### 接口地址

```
https://api.edgefn.net/v1
```

### 认证方式

```
Authorization: Bearer YOUR_API_KEY
```

**注意**：系统会自动处理 `sk-` 前缀，无需手动去除。

### 请求示例

```bash
curl -X POST https://api.edgefn.net/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "messages": [
      {
        "role": "system",
        "content": "你是一个专业的Go测试工程师"
      },
      {
        "role": "user",
        "content": "为这个函数生成测试代码"
      }
    ],
    "temperature": 0.3,
    "max_tokens": 2000
  }'
```

### 流式响应

百山云支持流式响应（SSE 协议），设置 `stream=true`：

```json
{
  "model": "GLM-4.5",
  "messages": [...],
  "stream": true
}
```

## 使用示例

### Python 代码示例

```python
from app.config import get_settings
from app.services.test_generator import GolangTestGenerator

# 创建测试生成器（使用百山云）
generator = GolangTestGenerator(
    ai_provider="baishan",
    repo_path="/path/to/repo"
)

# 生成测试
test_code = generator.generate_tests_for_file(
    file_analysis=file_info,
    language="golang",
    test_framework="ginkgo"
)
```

### Docker Compose 配置

```yaml
services:
  api:
    environment:
      - AI_PROVIDER=baishan
      - BAISHAN_API_KEY=${BAISHAN_API_KEY}
      - BAISHAN_MODEL=GLM-4.5
      - BAISHAN_BASE_URL=https://api.edgefn.net/v1
```

## 性能对比

| 指标 | OpenAI GPT-4 | 百山云 GLM-4.5 | 百山云 Qwen3-235B |
|-----|-------------|----------------|------------------|
| 平均响应时间 | ~2000ms | **<300ms** ⚡ | ~500ms |
| QPS 支持 | 200 | **1000+** 🚀 | 800 |
| 代码生成质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 中文支持 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ 🇨🇳 | ⭐⭐⭐⭐⭐ 🇨🇳 |
| 费用 | $$ | **免费** 💰 | **免费** 💰 |

## 错误处理

### 常见错误代码

| 状态码 | 错误类型 | 解决方案 |
|-------|---------|---------|
| 400 | 参数校验失败 | 检查请求参数格式 |
| 401 | 鉴权失败 | 检查 API Key 是否正确 |
| 429 | 配额超限 | 等待或联系管理员增加配额 |
| 500 | 服务内部错误 | 重试或联系技术支持 |

### 错误响应示例

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error"
  }
}
```

## 切换提供商

### 从 OpenAI 切换到百山云

只需修改 `.env` 文件：

```bash
# 修改前
AI_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4

# 修改后
AI_PROVIDER=baishan
BAISHAN_API_KEY=sk-yyy
BAISHAN_MODEL=GLM-4.5
```

### 重启服务

```bash
cd /Users/jonny/aitest-agent
docker-compose restart api celery-worker
```

## 最佳实践

### 1. 模型选择建议

- **日常测试生成**：使用 `GLM-4.5`（速度快，质量好）
- **复杂代码测试**：使用 `Qwen3-235B-A22B-2507`（质量更高）
- **代码修复**：使用 `GLM-4.5`（响应快，修复准确）

### 2. 并发配置

由于百山云支持 QPS 1000+，可以提高并发数：

```bash
MAX_CONCURRENT_GENERATIONS=20  # 并发生成数
MAX_CONCURRENT_TASKS=10        # 并发任务数
CELERY_WORKER_CONCURRENCY=8    # Worker 并发数
```

### 3. 超时配置

```bash
CELERY_TASK_TIME_LIMIT=7200    # 任务总超时（2小时）
TEST_EXECUTION_TIMEOUT=300      # 测试执行超时（5分钟）
```

## 技术支持

- **API 文档**：https://ai.baishan.com/docs/docs/llm-api.html
- **控制台**：https://ai.baishan.com/
- **技术支持**：联系管理员

## 更新日志

### v1.4.0 (2025-10-29)

- ✅ 添加百山云 AI 支持
- ✅ 兼容 OpenAI API 格式
- ✅ 支持所有测试生成器（Go, C, C++）
- ✅ 自动处理 API Key 前缀
- ✅ 完整文档和配置示例

## 参考资料

- [百山云 LLM API 文档](https://ai.baishan.com/docs/docs/llm-api.html)
- [OpenAI API 兼容性说明](https://platform.openai.com/docs)
- [环境变量配置说明](./环境变量配置说明.md)

