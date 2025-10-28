# 示例脚本使用指南

AI Test Agent 提供了两个核心示例脚本，涵盖完整的测试生成和修复流程。

## 📁 脚本列表

### 1. `example_generate_tests.py` - 测试生成示例

**功能：** 演示如何使用 AI 生成单元测试

**包含场景：**
- ✅ **场景1**: Kratos 项目 + Ginkgo BDD 测试
- ✅ **场景2**: 智能测试生成（基于代码复杂度，新功能）
- ✅ **场景3**: 标准 Go Test 框架
- ✅ **场景4**: 查看 Ginkgo 测试示例代码

**使用方法：**
```bash
python example_generate_tests.py
```

**特点：**
- 交互式菜单，选择不同场景
- 自动展示测试生成过程
- 支持查看代码复杂度分析
- 包含完整的测试统计和覆盖率信息

---

### 2. `example_fix_tests.py` - 测试修复示例

**功能：** 演示如何修复已生成的测试代码

**包含场景：**
- ✅ **场景1**: 快速修复（同步模式）
- ✅ **场景2**: 异步并发修复（速度提升 3-5 倍）
- ✅ **场景3**: 异步修复 + Git 自动提交
- ✅ **场景4**: 性能对比展示

**使用方法：**
```bash
python example_fix_tests.py
```

**特点：**
- 交互式配置修复参数
- 支持同步和异步两种模式
- 可选 Git 自动提交和推送
- 实时显示修复进度和结果

---

## 🚀 快速开始

### 测试生成流程

1. **运行测试生成示例：**
   ```bash
   python example_generate_tests.py
   ```

2. **选择场景：**
   - 推荐新用户选择 **场景2**（智能测试生成）
   - Kratos 项目选择 **场景1**

3. **等待完成：**
   - 系统会自动克隆代码
   - 分析代码结构
   - 生成测试文件
   - 执行测试并收集覆盖率

---

### 测试修复流程

1. **运行测试修复示例：**
   ```bash
   python example_fix_tests.py
   ```

2. **选择修复模式：**
   - 少量文件（< 20个）：选择 **场景1**（快速修复）
   - 大量文件（≥ 20个）：选择 **场景2**（异步并发）
   - 需要自动提交：选择 **场景3**（带 Git）

3. **配置参数：**
   ```
   工作空间路径: /app/workspace/xxx
   测试目录: internal/biz
   编程语言: golang
   测试框架: ginkgo
   Git 用户名: utest-agent
   ```

---

## 🎯 场景选择指南

### 何时使用场景1（Ginkgo + Kratos）

适用于：
- 使用 Kratos 框架的微服务项目
- 需要 BDD 风格测试
- 包含复杂的依赖注入

特点：
- Describe/Context/It 清晰结构
- BeforeEach/AfterEach 依赖管理
- Gomega 流畅断言

---

### 何时使用场景2（智能测试生成）⭐ 推荐

适用于：
- 所有 Go 项目
- 需要优化测试用例数量
- 关注成本和效率

优势：
- 自动计算可执行代码行数
- 根据复杂度智能决定测试数量
- 简单函数 2-3 个用例，复杂函数 11-15 个
- 自动分配正常/边界/异常场景 (40%/30%/30%)

示例输出：
```
📊 智能代码分析结果:
   文件包含 5 个函数，建议生成 28 个测试用例 (正常:11, 边界:9, 异常:8)
   CreateUser: 建议生成 6 个测试用例 (正常:2, 边界:2, 异常:2)
   ValidateEmail: 建议生成 2 个测试用例 (正常:1, 边界:1, 异常:0)
```

---

### 何时使用场景3（标准 Go Test）

适用于：
- 标准 Go 项目
- 不需要 BDD 风格
- 喜欢 Table-driven test

特点：
- Go 原生 testing 包
- 简单直接
- 无需额外依赖

---

## 📊 性能对比

### 测试修复性能

| 文件数 | 同步模式 | 异步模式 | 速度提升 |
|--------|---------|---------|---------|
| 10个   | 30秒    | 10秒    | 3.0x    |
| 25个   | 75秒    | 25秒    | 3.0x    |
| 46个   | 180秒   | 45秒    | 4.0x    |
| 100个  | 400秒   | 90秒    | 4.4x    |

**建议：**
- < 20 个文件：使用同步模式（简单直观）
- ≥ 20 个文件：使用异步模式（速度更快）

---

## 💡 常见用法

### 示例1: 快速体验智能测试生成

```bash
# 1. 运行脚本
python example_generate_tests.py

# 2. 选择场景 2
请输入选项: 2

# 3. 查看智能分析结果
📊 智能代码分析结果:
   CreateUser: 建议生成 6 个测试用例 (正常:2, 边界:2, 异常:2)
   ...
```

---

### 示例2: 修复测试并自动提交

```bash
# 1. 运行脚本
python example_fix_tests.py

# 2. 选择场景 3（异步 + Git）
请输入选项: 3

# 3. 配置参数
工作空间路径: /app/workspace/xxx
Git 用户名: utest-agent

# 4. 查看结果
✅ Git 状态: 成功
🌿 分支: feat/fix-tests-20250120-143022
💾 已提交: 是
🚀 已推送: 是
```

---

### 示例3: 查看 Ginkgo 示例代码

```bash
# 1. 运行脚本
python example_generate_tests.py

# 2. 选择场景 4
请输入选项: 4

# 3. 查看完整的 Ginkgo 测试示例
```

---

## 🔧 配置说明

### 测试生成配置

```python
project_data = {
    "name": "项目名称",
    "git_url": "仓库地址",
    "git_branch": "分支名",
    "language": "golang",              # 编程语言
    "test_framework": "ginkgo",        # ginkgo 或 go_test
    "source_directory": "internal/biz", # 源码目录
    "test_directory": "internal/biz",   # 测试目录
    "coverage_threshold": 80.0,         # 覆盖率目标
    "auto_commit": True,                # 自动提交
    "create_pr": True                   # 创建 PR
}
```

---

### 测试修复配置

```python
fix_config = {
    "workspace_path": "/app/workspace/xxx",  # 工作空间路径
    "test_directory": "internal/biz",        # 测试目录
    "language": "golang",                    # 编程语言
    "test_framework": "ginkgo",              # 测试框架
    "max_fix_attempts": 5,                   # 最大修复次数
    "auto_git_commit": True,                 # 启用 Git
    "git_username": "utest-agent",           # Git 用户名
    "git_branch_name": "feat/fix-tests",     # 可选：分支名
}
```

---

## 📚 相关文档

- [智能测试生成文档](docs/guides/CODE_BASED_TEST_GENERATION.md)
- [Ginkgo 快速开始](docs/guides/GINKGO_QUICK_START.md)
- [自动修复功能](docs/guides/AUTO_FIX_SUMMARY.md)
- [快速开始指南](docs/guides/QUICKSTART.md)

---

## ❓ 常见问题

### Q: 两个脚本有什么区别？

**A:** 
- `example_generate_tests.py` - 从零开始生成测试
- `example_fix_tests.py` - 修复已有测试的语法错误

---

### Q: 智能测试生成和普通生成有什么不同？

**A:** 智能测试生成会：
1. 计算每个函数的可执行代码行数
2. 分析代码复杂度
3. 根据复杂度决定测试用例数量
4. 自动分配测试场景比例

普通生成则使用固定的测试用例数量。

---

### Q: 异步修复比同步快多少？

**A:** 
- 通常快 3-5 倍
- 文件越多，优势越明显
- 并发数默认为 10，可调整

---

### Q: Git 自动提交安全吗？

**A:** 
- 会创建新分支，不影响主分支
- 可以审查后再合并
- 支持自定义提交信息
- 推荐使用 `utest-agent` 用户名

---

## 🎉 开始使用

选择一个场景开始体验：

```bash
# 测试生成
python example_generate_tests.py

# 测试修复
python example_fix_tests.py
```

祝您使用愉快！🚀

