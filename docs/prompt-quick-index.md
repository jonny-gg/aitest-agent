# 提示词快速索引

快速查找项目中的测试生成提示词模板。

**详细文档**: 请参阅 [提示词模板汇总.md](./提示词模板汇总.md)

---

## 📋 提示词列表

### Golang 测试提示词

| 提示词方法 | 用途 | 生成内容 | 推荐场景 |
|-----------|------|---------|---------|
| `golang_standard_test()` | Go 标准测试 | table-driven test | 简单函数测试 |
| `golang_ginkgo_test()` | Ginkgo BDD 测试（单函数） | 测试框架代码 | 需要 BDD 风格 |
| `golang_ginkgo_file_test()` | Ginkgo 文件测试 | 多函数测试框架 | 批量生成测试 |
| `golang_fix_test()` | 测试修复 | 修复后的测试代码 | 测试执行失败 |
| `golang_syntax_fix()` | 语法错误修复 | 修复后的代码 | 语法错误 |

### C++ 测试提示词

| 提示词方法 | 用途 | 生成内容 | 推荐场景 |
|-----------|------|---------|---------|
| `cpp_google_test()` | Google Test | 完整测试代码 | C++ 项目测试 |
| `cpp_fix_test()` | 测试修复 | 修复后的测试代码 | 测试执行失败 |

### C 测试提示词

| 提示词方法 | 用途 | 生成内容 | 推荐场景 |
|-----------|------|---------|---------|
| `c_unit_test()` | C 单元测试 | CUnit/Check/Unity 测试 | C 项目测试 |
| `c_fix_test()` | 测试修复 | 修复后的测试代码 | 测试执行失败 |

### 系统提示词

| 提示词方法 | 用途 | 内容 |
|-----------|------|-----|
| `system_prompt()` | 系统提示词 | AI 角色定位、测试原则、最佳实践 |

---

## 🔍 按场景查找

### 场景 1: 初次生成测试

**Go 项目**:
- 单个函数: `golang_ginkgo_test()` - BDD 风格，清晰的场景描述
- 整个文件: `golang_ginkgo_file_test()` - 批量生成多个函数的测试
- 简单测试: `golang_standard_test()` - 轻量级 table-driven test

**C++ 项目**:
- `cpp_google_test()` - 业界标准的 Google Test 框架

**C 项目**:
- `c_unit_test()` - 支持 CUnit、Check、Unity 框架

### 场景 2: 测试失败需要修复

| 语言 | 提示词 | 修复内容 |
|------|--------|---------|
| Go | `golang_fix_test()` | 编译错误、运行时错误、断言失败 |
| C++ | `cpp_fix_test()` | 编译错误、断言失败 |
| C | `c_fix_test()` | 编译错误、内存问题 |

### 场景 3: 语法错误修复

| 语言 | 提示词 | 修复内容 |
|------|--------|---------|
| Go | `golang_syntax_fix()` | 语法错误、格式问题、导入错误 |

---

## 🎯 快速选择指南

### 问题 1: 我应该使用哪个测试框架？

**Go 项目**:
```
需要 BDD 风格描述？
  ├─ 是 → golang_ginkgo_test()
  └─ 否 → golang_standard_test()

需要批量生成？
  └─ 是 → golang_ginkgo_file_test()
```

**C++ 项目**:
```
→ cpp_google_test() (推荐使用 Google Test)
```

**C 项目**:
```
→ c_unit_test(test_framework="cunit|check|unity")
```

### 问题 2: 生成的测试有错误怎么办？

```
语法错误（Go）？
  └─ golang_syntax_fix()

测试执行失败？
  ├─ Go → golang_fix_test()
  ├─ C++ → cpp_fix_test()
  └─ C → c_fix_test()
```

### 问题 3: 如何确保生成高质量的测试？

**关键原则**:
1. ✅ 使用 **同包测试**（Go）: `package xxx` 而非 `package xxx_test`
2. ✅ **不生成未使用的变量**
3. ✅ 覆盖 **三种场景**: Normal、Boundary、Exception
4. ✅ 使用 **AAA 模式**: Arrange-Act-Assert
5. ✅ **纯函数优先**，有依赖才使用 mock

---

## 📝 使用示例

### 示例 1: 生成 Ginkgo 测试

```python
from backend.app.services.prompt_templates import get_prompt_templates

templates = get_prompt_templates()

# 生成单个函数的 Ginkgo 测试
prompt = templates.golang_ginkgo_test(
    func_name="CalMemory",
    func_body="return fmt.Sprintf(\"%.1f\", float64(memoryMB)/1024)",
    params=["memoryMB int"],
    return_type="string",
    receiver="c *Calculator",
    module_path="github.com/example/project",
    package_name="biz",
    file_path="internal/biz/calculator.go"
)

# 发送给 AI 生成测试
test_code = ai_client.generate(prompt)
```

### 示例 2: 批量生成测试

```python
# 为整个文件生成测试
functions_info = [
    {
        'signature': 'func CalMemory(memoryMB int) string',
        'executable_lines': 10,
        'complexity': 2,
        'test_count': 3,
        'normal_count': 1,
        'edge_count': 1,
        'error_count': 1
    },
    {
        'signature': 'func CalDiskCapacity(disk, present int) int',
        'executable_lines': 5,
        'complexity': 1,
        'test_count': 3,
        'normal_count': 1,
        'edge_count': 1,
        'error_count': 1
    }
]

prompt = templates.golang_ginkgo_file_test(
    module_path="github.com/example/project",
    package_name="biz",
    file_path="internal/biz/calculator.go",
    functions_info=functions_info
)

test_code = ai_client.generate(prompt)
```

### 示例 3: 修复失败的测试

```python
# 测试执行失败，需要修复
prompt = templates.golang_fix_test(
    original_test=failed_test_code,
    error_output=error_message,
    source_code=source_code,
    module_path="github.com/example/project",
    package_name="biz"
)

fixed_code = ai_client.generate(prompt)
```

---

## 🔧 提示词参数说明

### Golang 提示词参数

#### `golang_ginkgo_test()` 参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `func_name` | str | ✅ | 函数名 | `"CalMemory"` |
| `func_body` | str | ✅ | 函数体代码 | `"return fmt.Sprintf(...)"` |
| `params` | List[str] | ✅ | 参数列表 | `["memoryMB int"]` |
| `return_type` | str | ✅ | 返回类型 | `"string"` |
| `receiver` | str | ✅ | 接收者 | `"c *Calculator"` |
| `module_path` | str | ✅ | Go 模块路径 | `"github.com/example/project"` |
| `package_name` | str | ✅ | 包名 | `"biz"` |
| `file_path` | str | ✅ | 文件路径 | `"internal/biz/calculator.go"` |

#### `golang_ginkgo_file_test()` 参数

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `module_path` | str | ✅ | Go 模块路径 | `"github.com/example/project"` |
| `package_name` | str | ✅ | 包名 | `"biz"` |
| `file_path` | str | ✅ | 文件路径 | `"internal/biz/calculator.go"` |
| `functions_info` | List[Dict] | ✅ | 函数信息列表 | `[{...}, {...}]` |
| `source_code_snippet` | str | ❌ | 源代码片段 | `"func CalMemory(...) {...}"` |

**`functions_info` 结构**:
```python
{
    'signature': 'func CalMemory(memoryMB int) string',  # 函数签名
    'executable_lines': 10,                               # 可执行行数
    'complexity': 2,                                      # 复杂度
    'test_count': 3,                                      # 建议测试用例数
    'normal_count': 1,                                    # 正常场景数
    'edge_count': 1,                                      # 边界场景数
    'error_count': 1                                      # 异常场景数
}
```

---

## 📊 提示词对比

### Ginkgo vs Standard Test

| 特性 | `golang_ginkgo_test` | `golang_standard_test` |
|------|---------------------|----------------------|
| 测试风格 | BDD（Describe/Context/It） | Table-driven test |
| 场景描述 | ✅ 清晰的自然语言描述 | ⚠️ 结构化的数据表 |
| 可读性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 学习曲线 | 中等（需要学习 Ginkgo） | 简单（Go 标准库） |
| 适用场景 | 复杂业务逻辑、需要清晰描述 | 简单函数、纯计算逻辑 |
| 依赖 | Ginkgo/Gomega | 无（标准库） |

**推荐**:
- 新项目、复杂业务逻辑 → `golang_ginkgo_test`
- 简单函数、快速测试 → `golang_standard_test`

---

## ⚠️ 常见问题

### Q1: 为什么 Go 测试使用同包（`package xxx`）而不是 `package xxx_test`？

**A**: 同包测试（in-package testing）的优势：
- ✅ 可以直接访问包内的私有类型和函数
- ✅ 无需导入被测试的包，避免循环依赖
- ✅ 代码更简洁，导入更少
- ✅ 适合单元测试（测试实现细节）

**外部测试包**（`package xxx_test`）适用场景：
- 集成测试
- 只测试公开 API
- 避免测试代码污染包的命名空间

### Q2: 为什么生成的测试只有注释，没有具体实现？

**A**: 这是设计策略（**框架模式**）：
1. **快速生成**: AI 生成测试框架比完整实现更快、更准确
2. **可控性**: 开发者可以根据实际需求补充具体实现
3. **避免错误**: AI 生成的完整实现可能有错误，框架模式降低风险
4. **灵活性**: 开发者可以选择实现哪些测试用例

**如何补充实现**:
- 测试框架中的注释已经详细说明了测试步骤
- 按照 Arrange-Act-Assert 三步完成
- 参考注释中的示例代码

### Q3: 如何控制生成的测试用例数量？

**A**: 
- **单函数测试**: 默认生成 Normal、Boundary、Exception 三种场景
- **文件测试**: 根据 `functions_info` 中的 `test_count` 动态调整
- **自定义**: 修改 `functions_info` 中的计数字段

```python
functions_info = [{
    'signature': 'func CalMemory(memoryMB int) string',
    'test_count': 5,        # 总共 5 个测试用例
    'normal_count': 2,      # 2 个正常场景
    'edge_count': 2,        # 2 个边界场景
    'error_count': 1        # 1 个异常场景
}]
```

### Q4: 生成的测试代码有未使用的变量怎么办？

**A**: 这个问题已在 v1.4.0 中修复：
- ✅ 提示词已更新，明确禁止生成未使用的变量
- ✅ 变量只在注释中说明，不实际声明
- ✅ BeforeEach 中也只包含注释说明

**如果还出现此问题**:
1. 确保使用最新的提示词模板
2. 重启服务以加载新的提示词
3. 使用 `golang_syntax_fix()` 修复现有代码

---

## 🚀 进阶使用

### 1. 自定义提示词

在 `backend/app/services/prompt_templates.py` 中添加新方法：

```python
@staticmethod
def golang_benchmark_test(func_name: str, func_body: str) -> str:
    """Go 性能基准测试提示词"""
    return f"""请为以下Go函数生成性能基准测试。
    
## 目标函数
```go
func {func_name}(...) {{
{func_body}
}}
```

## 基准测试要求
1. 使用 testing.B
2. 测试函数名为 Benchmark{func_name}
3. 包含不同规模的输入测试
4. 使用 b.ResetTimer() 重置计时器

请只返回测试代码。
"""
```

### 2. 组合使用提示词

```python
# 先生成测试框架
prompt1 = templates.golang_ginkgo_test(...)
test_framework = ai_client.generate(prompt1)

# 如果有语法错误，修复
if has_syntax_errors(test_framework):
    prompt2 = templates.golang_syntax_fix(
        test_code=test_framework,
        syntax_errors=errors
    )
    test_framework = ai_client.generate(prompt2)

# 如果测试执行失败，修复
if test_failed:
    prompt3 = templates.golang_fix_test(
        original_test=test_framework,
        error_output=error_msg,
        source_code=source
    )
    fixed_test = ai_client.generate(prompt3)
```

### 3. 批处理优化

```python
# 批量生成多个文件的测试
for file_path in go_files:
    functions_info = analyze_file(file_path)
    
    prompt = templates.golang_ginkgo_file_test(
        module_path=get_module_path(),
        package_name=get_package_name(file_path),
        file_path=file_path,
        functions_info=functions_info
    )
    
    test_code = ai_client.generate(prompt)
    save_test_file(file_path, test_code)
```

---

## 📚 相关文档

- [提示词模板汇总.md](./提示词模板汇总.md) - 详细的提示词说明文档
- [测试代码简洁性优化.md](./测试代码简洁性优化.md) - 代码简洁性优化说明
- [百山云AI配置说明.md](./百山云AI配置说明.md) - 百山云 AI 配置指南
- [同包测试配置说明.md](./同包测试配置说明.md) - 同包测试策略说明
- [环境变量配置说明.md](./环境变量配置说明.md) - 环境变量配置文档

---

**快速索引版本**: v1.0.0  
**最后更新**: 2025-10-30  
**维护者**: AI Test Agent Team

