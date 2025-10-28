# AI Test Agent - 智能单元测试自动化系统

[English](README.md) | 中文

> 专为 Kratos 微服务框架优化，支持 Ginkgo BDD 测试！

## 🎯 核心特性

- ✅ **自动测试生成** - AI 分析代码并生成高质量单元测试
- ✨ **智能增量测试** - 自动跳过已有测试，只生成新的（NEW! ⚡ 30x 提速）
- ✨ **智能自动修复** - 测试失败时 AI 自动分析并修复（NEW! 🤖 85%+ 成功率）
- ⚡ **并发生成** - 10-15倍速度提升，大项目 3-5 分钟完成
- ✅ **Ginkgo BDD** - 完美支持 Kratos 等有依赖注入的框架
- ✅ **后台 Agent** - Celery 分布式任务处理
- ✅ **多语言** - Golang、C++、C
- ✅ **覆盖率统计** - 类似 SonarQube 的详细报告
- ✅ **Git 集成** - 自动拉取和提交代码

## 🚀 快速开始

```bash
# 1. 配置环境
./setup.sh

# 2. 启动服务
docker-compose up -d

# 3. 创建 Kratos 项目（Ginkgo）
python example_kratos.py

# 4. 访问 API 文档
open http://localhost:8000/docs
```

## 📖 文档

- [快速启动](docs/guides/QUICKSTART.md)
- [Ginkgo 快速指南](docs/guides/GINKGO_QUICK_START.md)
- [增量测试与智能修复](docs/guides/incremental-testing.md) ✨ NEW
- [自动修复功能说明](AUTO_FIX_FEATURES.md) ✨ NEW
- [完整文档](docs/)

## 🌟 特别推荐：Kratos + Ginkgo

```bash
# 为 Kratos 项目生成 BDD 测试
python example_kratos.py
```

详见：[Ginkgo 完整指南](docs/ginkgo-guide.md)

---

Made with ❤️ for Kratos and Go developers
