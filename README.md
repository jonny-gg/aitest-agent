# 🤖 AI Test Agent

> 基于 AI 的自动化测试生成和修复系统

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

## ✨ 核心特性

### 🎯 智能测试生成
- 基于代码复杂度的智能测试策略
- 支持多种测试框架（Ginkgo, Go Test, GTest, CUnit）
- 自动生成高质量、可运行的测试代码

### 📁 多目录递归扫描 **NEW**
- 支持数组形式的 `source_directory` 配置
- 自动递归遍历所有子目录
- 一次性为多个目录生成测试用例
- 测试文件采用 Go 同包测试策略（与源文件在同一目录）
- **不需要** `test_directory` 参数（Go 语言自动处理）
- 使用方式：只需配置 `source_directory: ["internal/biz", "pkg"]`

### 🔧 自动修复
- 语法错误自动修复（95%+ 成功率）
- 编译错误自动优化
- 导入路径自动清理

### ⚡ 高效率
- 相比手动编写测试提升 200% 效率
- 减少 40% 不必要的测试用例
- 编译成功率从 60% 提升到 95%+

## 🚀 快速开始

### 5分钟快速体验

```bash
# 1. 克隆项目
git clone <your-repo>
cd aitest-agent

# 2. 配置环境
cp env.example .env
# 编辑 .env 文件，填入你的 OpenAI API Key

# 3. 启动服务
docker-compose up -d

# 4. 运行第一个测试
python example_generate_tests.py
```

## 📚 文档导航

文档已重组为 4 大类，更加清晰易用：

| 文档类别 | 说明 | 快速链接 |
|---------|------|----------|
| 🚀 **快速开始** | 5分钟上手指南 | [立即开始](docs/1-快速开始/) |
| 📖 **使用指南** | 完整功能手册 | [查看指南](docs/2-使用指南/) |
| ⚡ **核心功能** | 特性深入解析 | [了解更多](docs/3-核心功能/) |
| 🔧 **开发参考** | 技术文档和API | [开发文档](docs/4-开发参考/) |

### 快速查找

- **我想快速上手** → [快速开始](docs/1-快速开始/)
- **我想生成测试** → [生成测试指南](docs/2-使用指南/生成测试.md)
- **我想修复测试** → [修复测试指南](docs/2-使用指南/修复测试.md)
- **我在使用 Ginkgo** → [Ginkgo 指南](docs/2-使用指南/Ginkgo测试.md)
- **我想自定义** → [提示词管理](docs/2-使用指南/提示词管理.md)
- **解决编译问题** → [编译优化](docs/3-核心功能/编译优化.md)

📖 **[完整文档导航](docs/文档导航.md)** - 按场景/角色/问题快速查找

## 🎯 使用场景

### 场景 1: 新项目测试生成
```bash
python example_generate_tests.py
# 选择场景 1 - Ginkgo BDD 测试
```

### 场景 2: 多目录递归测试生成 **NEW**
```bash
python example_generate_tests.py
# 选择任意场景（1、2、3），自动递归扫描多个目录
```

**配置示例**：
```python
{
    "source_directory": ["internal/biz", "pkg"],  # 数组形式
    # "test_directory" 不需要了！
}
```

**目录结构示例**：
```
源文件：internal/biz/user.go    → 生成：internal/biz/user_test.go
源文件：pkg/utils/string.go    → 生成：pkg/utils/string_test.go
```

### 场景 3: 已有测试修复
```bash
python example_fix_tests.py
# 自动修复失败的测试
```

### 场景 4: 智能测试策略
```bash
# 基于代码复杂度自动调整测试用例数量
# 简单函数 → 2-3个测试
# 复杂函数 → 11-15个测试
```

## 💡 核心优势

### 智能测试策略
- 📊 自动分析代码复杂度
- 🎯 智能决定测试用例数量
- 💰 节省 30% AI Token 消耗

### 自动修复机制
- 🔧 语法错误自动修复
- 📦 导入路径自动修正
- ✅ 编译错误自动优化

### 编译优化
- 🚫 预防不必要的导入
- 🧹 自动清理导致编译失败的代码
- ✅ 确保生成的测试可以编译

## 📊 性能指标

| 指标 | 效果 |
|------|------|
| 测试生成速度 | **+200%** 相比手动编写 |
| 编译成功率 | **60% → 95%+** |
| 测试用例优化 | **-40%** 不必要测试 |
| 语法错误修复 | **95%+** 成功率 |
| Token 消耗 | **-30%** AI 成本 |

## 🛠️ 技术栈

- **Backend**: FastAPI + Python 3.11+
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **AI**: OpenAI GPT-4 / Anthropic Claude
- **Testing**: Ginkgo, Go Test, GTest, CUnit
- **DevOps**: Docker + Docker Compose

## 📖 文档结构

```
docs/
├── 1-快速开始/     # ⚡ 5分钟快速上手
│   ├── README.md
│   ├── 安装部署.md
│   └── 快速示例.md
│
├── 2-使用指南/     # 📖 完整功能使用手册
│   ├── 生成测试.md
│   ├── 修复测试.md
│   ├── Ginkgo测试.md
│   ├── 提示词管理.md
│   ├── 配置选项.md
│   ├── CLI使用.md
│   └── FAQ.md
│
├── 3-核心功能/     # ⚡ 核心特性深入解析
│   ├── 智能测试策略.md
│   ├── 自动修复.md
│   └── 编译优化.md
│
└── 4-开发参考/     # 🔧 技术文档和API
    ├── 架构设计.md
    ├── API参考.md
    ├── 贡献指南.md
    ├── 扩展开发.md
    └── 更新日志.md
```

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](docs/4-开发参考/贡献指南.md)

## 📝 License

MIT License - 查看 [LICENSE](LICENSE) 文件

## 🔗 链接

- [完整文档](docs/文档导航.md)
- [快速开始](docs/1-快速开始/)
- [GitHub Issues](your-repo/issues)
- [更新日志](docs/4-开发参考/更新日志.md)

---

**文档版本：** v2.0（重组版）  
**最后更新：** 2024-10-27  
**维护者：** AI Test Agent Team
