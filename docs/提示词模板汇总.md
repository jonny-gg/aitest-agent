# 提示词模板汇总

本文档汇总了 AI Test Agent 项目中所有用于生成单元测试的提示词模板。

**文件位置**: `backend/app/services/prompt_templates.py`

---

## 📋 目录

1. [Golang 测试提示词](#golang-测试提示词)
   - [Go 标准测试框架](#1-go-标准测试框架)
   - [Ginkgo BDD 测试框架（单函数）](#2-ginkgo-bdd-测试框架单函数)
   - [Ginkgo 整个文件测试](#3-ginkgo-整个文件测试)
   - [Go 测试修复](#4-go-测试修复)
   - [Go 语法错误修复](#5-go-语法错误修复)
2. [C++ 测试提示词](#c-测试提示词)
   - [Google Test 框架](#1-google-test-框架)
   - [C++ 测试修复](#2-c-测试修复)
3. [C 测试提示词](#c-测试提示词-1)
   - [C 单元测试](#1-c-单元测试)
   - [C 测试修复](#2-c-测试修复-1)
4. [系统提示词](#系统提示词)
5. [提示词使用指南](#提示词使用指南)
6. [核心设计原则](#核心设计原则)

---

## Golang 测试提示词

### 1. Go 标准测试框架

**方法**: `golang_standard_test()`

**用途**: 为 Go 函数生成基于标准库 `testing` 包的单元测试

**参数**:
```python
func_name: str      # 函数名
func_body: str      # 函数体代码
params: List[str]   # 参数列表
return_type: str    # 返回类型
receiver: str       # 接收者（可选）
```

**核心要求**:
- 使用 Go 标准库的 `testing` 包
- 测试函数名应为 `Test{func_name}`
- 使用 table-driven test 风格
- 覆盖正常、边界、异常场景
- 包含清晰的测试用例描述

**生成示例**:
```go
func TestCalMemory(t *testing.T) {
    tests := []struct {
        name string
        memoryMB int
        want string
    }{
        {"正常值", 1024, "1"},
        {"边界值", 0, "0"},
        {"异常值", -1, "0"},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // 测试逻辑
        })
    }
}
```

**适用场景**: 
- 简单的纯函数测试
- 不需要 BDD 风格的项目
- 遗留代码的测试补充

---

### 2. Ginkgo BDD 测试框架（单函数）

**方法**: `golang_ginkgo_test()`

**用途**: 为单个 Go 函数生成基于 Ginkgo/Gomega 的 BDD 风格测试框架（只生成框架结构，不生成具体实现）

**参数**:
```python
func_name: str      # 函数名
func_body: str      # 函数体代码
params: List[str]   # 参数列表
return_type: str    # 返回类型
receiver: str       # 接收者
module_path: str    # Go 模块路径
package_name: str   # 包名
file_path: str      # 文件路径
```

**核心要求**:

#### 1. 包声明规则 ⭐ 重要
```go
// ✅ 正确：使用同包测试
package biz

// ❌ 错误：不要使用外部测试包
package biz_test
```

**为什么使用同包测试？**
- 可以直接访问包内的私有类型和函数
- 无需导入被测试的包
- 避免循环依赖问题
- 更简洁的代码结构

#### 2. 导入规则

**纯函数测试**（无外部依赖）:
```go
import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)
```

**有依赖的方法测试**（需要 mock）:
```go
import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    "github.com/golang/mock/gomock"
    "your-project/internal/mocks"
)
```

**严格禁止**:
- ❌ 不要导入其他项目内部包（除了 mocks）
- ❌ 不要导入被测试的包本身
- ❌ 不要导入不需要的包

#### 3. 测试框架结构

**只生成框架，不生成具体实现**:
```go
var _ = Describe("CalMemory", func() {
    // ❌ 不要在这里声明未使用的变量
    // ✅ 只在需要时声明
    
    BeforeEach(func() {
        // TODO: 如果需要初始化，在这里说明
        // 例如: calculator := NewCalculator()
    })
    
    Context("when memory is divisible by 1024", func() {
        It("should return integer value", func() {
            // TODO: 实现测试逻辑
            //
            // 测试场景：内存值可以被1024整除
            // 输入参数: memoryMB = 1024
            // 预期输出: 返回字符串 "1"
            //
            // 测试步骤:
            // 1. Arrange: memoryMB := 1024
            // 2. Act: result := CalMemory(memoryMB)
            // 3. Assert: Expect(result).To(Equal("1"))
        })
    })
})
```

#### 4. 测试场景分类

**必须覆盖三种场景**:

**✓ Normal Case（正常场景）**
- 测试典型的业务流程和预期输入
- 验证正常情况下的输出结果
- 示例: 计算 1024MB → 返回 "1"

**✓ Boundary Case（边界场景）**
- 测试边界值和临界条件
- 包括: 零值、空值、最大值、最小值
- 示例: 内存为 0 → 返回 "0"

**✓ Exception Case（异常场景）**
- 测试错误处理和异常情况
- 包括: 负数、无效输入、数据库错误
- 示例: 负的内存值 → 返回错误

#### 5. 代码简洁性要求 ⭐ 重要

- ❌ **绝对不要生成未使用的变量声明**
- ❌ **不要在 Describe 块顶部声明变量**
- ✅ **如果变量暂时不需要，只在注释中说明**
- ✅ **保持代码最小化**，只生成必要的框架结构
- ✅ **如果 BeforeEach 不需要初始化，可以完全省略**

#### 6. 测试策略

**纯函数**（无副作用）:
- 直接传入参数测试，不需要 mock
- 示例: `CalMemory`, `CalDiskCapacity`, `CalIpNum`

**有依赖的方法**（依赖数据库、外部服务）:
- 使用 gomock 模拟依赖
- 示例: `CustomerList`, `GetBill`

**生成示例**:
```go
var _ = Describe("XdyEcsBillCase", func() {
    // ✅ 不声明未使用的变量
    
    Describe("CalMemory", func() {
        Context("when memory is divisible by 1024", func() {
            It("should return integer value", func() {
                // TODO: 实现测试逻辑
                //
                // 测试场景：测试内存值可以被1024整除
                // 输入参数: memoryMB = 1024
                // 预期输出: 返回字符串 "1"
                //
                // 测试步骤:
                // 1. Arrange: memoryMB := 1024
                // 2. Act: result := xdyEcsBillCase.CalMemory(memoryMB)
                // 3. Assert: Expect(result).To(Equal("1"))
            })
        })
        
        Context("when memory is zero", func() {
            It("should return 0", func() {
                // TODO: 实现测试逻辑
                //
                // 测试场景：边界条件 - 内存为0
                // 输入参数: memoryMB = 0
                // 预期输出: 返回字符串 "0"
                //
                // 测试步骤说明...
            })
        })
    })
})
```

**适用场景**:
- 需要 BDD 风格测试的项目
- 复杂的业务逻辑测试
- 需要清晰描述测试场景的情况

---

### 3. Ginkgo 整个文件测试

**方法**: `golang_ginkgo_file_test()`

**用途**: 为整个 Go 源文件的所有函数生成 Ginkgo 测试框架

**参数**:
```python
module_path: str           # Go 模块路径
package_name: str          # 包名
file_path: str             # 文件路径
functions_info: List[Dict] # 函数信息列表
source_code_snippet: str   # 源代码片段（可选）
```

**函数信息结构**:
```python
{
    'signature': 'func CalMemory(memoryMB int) string',
    'executable_lines': 10,
    'complexity': 2,
    'test_count': 3,
    'normal_count': 1,
    'edge_count': 1,
    'error_count': 1
}
```

**核心要求**:
- 为每个函数生成一个 `Describe` 块
- 根据函数复杂度和代码行数决定测试用例数量
- 使用 Context 组织不同的测试场景
- 每个 It 块只包含注释说明，不包含具体实现
- 遵守同包测试规则
- 不生成未使用的变量

**生成示例**:
```go
var _ = Describe("XdyEcsBillCase", func() {
    
    Describe("CalMemory", func() {
        Context("when memory is divisible by 1024", func() {
            It("should return integer value", func() {
                // TODO: 实现测试逻辑
            })
        })
    })
    
    Describe("CalDiskCapacity", func() {
        Context("when disk capacity is greater than present", func() {
            It("should return correct billable capacity", func() {
                // TODO: 实现测试逻辑
            })
        })
    })
    
    Describe("CalBillStartEndTime", func() {
        Context("when bill period overlaps with request", func() {
            It("should use correct end time", func() {
                // TODO: 实现测试逻辑
            })
        })
    })
})
```

**适用场景**:
- 为整个文件批量生成测试
- 需要一次性覆盖多个函数
- 初次添加测试覆盖

---

### 4. Go 测试修复

**方法**: `golang_fix_test()`

**用途**: 修复执行失败的 Go 测试代码

**参数**:
```python
original_test: str  # 原始测试代码
error_output: str   # 错误输出
source_code: str    # 源代码上下文
module_path: str    # Go 模块路径
package_name: str   # 包名
```

**修复要求**:
1. 分析错误原因（编译错误、运行时错误、断言失败）
2. 修复所有错误，使测试能够通过
3. 保持测试的完整性和覆盖范围
4. 确保包名和导入路径正确
5. 遵守同包测试规则
6. 不导入不必要的包

**常见问题修复**:
- **导入路径错误**: 使用正确的模块路径
- **包名错误**: 使用 `package xxx`（同包测试）
- **Mock 相关**:
  - 纯函数：不需要 mock，直接传参数
  - 有依赖的方法：确保正确导入 gomock 和 mocks
  - 检查 mock 期望设置是否正确
- **类型不匹配**: 检查源代码，使用正确的类型
- **nil 指针**: 添加适当的 nil 检查

**适用场景**:
- 测试执行失败需要修复
- 编译错误需要调整
- 断言失败需要重新设计

---

### 5. Go 语法错误修复

**方法**: `golang_syntax_fix()`

**用途**: 修复测试代码中的语法错误

**参数**:
```python
test_code: str              # 测试代码
syntax_errors: List[str]    # 语法错误列表
file_analysis: Dict         # 文件分析结果
language: str               # 编程语言
test_framework: str         # 测试框架
```

**修复要求**:
1. 只修复语法错误，不改变测试逻辑
2. 确保代码符合测试框架规范
3. 保持代码结构和测试覆盖范围不变
4. 确保包名和导入语句正确
5. 移除所有 markdown 代码块标记

**适用场景**:
- AI 生成的代码有语法错误
- 包含 markdown 格式标记
- 导入语句错误

---

## C++ 测试提示词

### 1. Google Test 框架

**方法**: `cpp_google_test()`

**用途**: 为 C++ 函数生成基于 Google Test 的单元测试

**参数**:
```python
func_name: str  # 函数名
func_body: str  # 函数体代码
```

**核心要求**:
- 使用 Google Test 框架
- 覆盖正常、边界、异常情况
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试用例应该独立且可重复
- 包含清晰的测试描述

**生成示例**:
```cpp
TEST(CalculatorTest, AddPositiveNumbers) {
    // Arrange
    Calculator calc;
    int a = 5, b = 3;
    
    // Act
    int result = calc.Add(a, b);
    
    // Assert
    EXPECT_EQ(8, result);
}

TEST(CalculatorTest, AddZero) {
    // Arrange
    Calculator calc;
    
    // Act
    int result = calc.Add(0, 0);
    
    // Assert
    EXPECT_EQ(0, result);
}
```

**常用断言**:
- `EXPECT_EQ(expected, actual)` - 相等判断
- `EXPECT_NE(val1, val2)` - 不相等判断
- `EXPECT_TRUE(condition)` - 真值判断
- `EXPECT_FALSE(condition)` - 假值判断
- `ASSERT_TRUE(condition)` - 强制断言（失败即停止）
- `EXPECT_THROW(statement, exception)` - 异常判断

**适用场景**:
- C++ 项目的单元测试
- 需要严格类型检查的测试
- 性能敏感的代码测试

---

### 2. C++ 测试修复

**方法**: `cpp_fix_test()`

**用途**: 修复执行失败的 C++ 测试代码

**参数**:
```python
original_test: str  # 原始测试代码
error_output: str   # 错误输出
```

**修复要求**:
1. 分析错误原因
2. 修复所有错误
3. 保持测试完整性
4. 确保包含正确的头文件

**适用场景**:
- 测试编译失败
- 测试运行时错误
- 断言失败需要调整

---

## C 测试提示词

### 1. C 单元测试

**方法**: `c_unit_test()`

**用途**: 为 C 函数生成单元测试

**参数**:
```python
func_name: str         # 函数名
func_body: str         # 函数体代码
test_framework: str    # 测试框架（默认 "cunit"）
```

**支持的测试框架**:
- CUnit
- Check
- Unity

**核心要求**:
- 覆盖正常、边界、异常情况
- 测试用例应该独立且可重复
- 包含清晰的测试描述
- 适当的断言

**生成示例**（CUnit）:
```c
void test_add_positive_numbers(void) {
    // Arrange
    int a = 5, b = 3;
    
    // Act
    int result = add(a, b);
    
    // Assert
    CU_ASSERT_EQUAL(result, 8);
}

void test_add_zero(void) {
    // Arrange
    int a = 0, b = 0;
    
    // Act
    int result = add(a, b);
    
    // Assert
    CU_ASSERT_EQUAL(result, 0);
}
```

**适用场景**:
- C 语言项目的单元测试
- 嵌入式系统测试
- 底层系统代码测试

---

### 2. C 测试修复

**方法**: `c_fix_test()`

**用途**: 修复执行失败的 C 测试代码

**参数**:
```python
original_test: str  # 原始测试代码
error_output: str   # 错误输出
```

**修复要求**:
1. 分析错误原因
2. 修复所有错误
3. 保持测试完整性
4. 确保包含正确的头文件

**适用场景**:
- 测试编译失败
- 测试运行时错误
- 内存泄漏问题

---

## 系统提示词

**方法**: `system_prompt()`

**用途**: 为 AI 模型提供通用的系统级提示词，定义其作为测试工程师的角色和职责

**核心内容**:

### 角色定位
🎯 专业的测试工程师，擅长为各种编程语言编写高质量的单元测试

### 核心职责
1. 理解代码的业务逻辑和功能
2. 识别可测试的方法和边界条件
3. 编写清晰、完整、可维护的测试用例
4. 确保测试覆盖正常、边界和异常场景

### 测试设计原则

#### 1. 优先级排序
- ✅ **高优先级**: 纯函数（无副作用）、核心业务逻辑、复杂计算
- ⚠️ **中优先级**: 有外部依赖但可 mock 的方法
- ❌ **低优先级**: 简单的 getter/setter、第三方库封装

#### 2. 三段式测试结构（AAA Pattern）
```
Arrange（准备）- 设置测试数据和环境
Act（执行）    - 调用被测试的方法
Assert（断言） - 验证结果是否符合预期
```

#### 3. 测试场景覆盖

**✓ Normal Case（正常场景）**
- 测试典型的业务流程，使用常见的有效输入
- 示例: 计算 1024MB 内存 → 应返回 "1GB"

**✓ Boundary Case（边界场景）**
- 测试边界值和临界条件
- 包括: 零值、空值、最大值、最小值、空集合
- 示例: 内存为 0 → 应返回 "0GB"

**✓ Exception Case（异常场景）**
- 测试错误处理和异常情况
- 包括: 负数、无效输入、超出范围、依赖失败
- 示例: 数据库连接失败 → 应抛出或返回错误

#### 4. 测试独立性
- 每个测试应该独立运行，不依赖其他测试
- 测试之间不应该有顺序依赖
- 使用 setup/teardown 确保测试环境一致

#### 5. 可读性优先
- 使用清晰的测试命名
- 添加必要的注释说明意图
- 使用真实且有意义的测试数据
- 让测试成为代码的文档

### 测试策略选择
- ✅ **纯函数**（无外部依赖）：直接测试，通过不同参数组合验证行为
- ✅ **有依赖的方法**（依赖数据库、外部服务）：使用 mock 模拟依赖

### Mock 使用指南

**何时使用 Mock**:
- 外部服务调用（API、数据库、文件系统）
- 耗时操作（网络请求、复杂计算）
- 不稳定的依赖（随机数、当前时间）
- 难以复现的场景（错误条件、边界情况）

**Mock 最佳实践**:
1. **只 mock 你拥有的接口** - 不要直接 mock 第三方库
2. **验证交互而非实现** - 关注行为，不是实现细节
3. **保持 mock 简单** - 避免过度复杂的 mock 设置
4. **使用真实数据** - mock 返回的数据应该真实可信

### 测试覆盖率目标
- 代码覆盖率达到 80%+
- 核心业务逻辑 100% 覆盖
- 所有公开 API 都有测试
- 重点覆盖复杂计算和关键业务流程

### 生成要求
- 语法正确，可以直接运行
- 每个测试只验证一件事
- 使用 Arrange-Act-Assert 结构并添加注释
- 测试命名清晰易懂
- 不添加额外的解释文字，只生成代码

---

## 提示词使用指南

### 1. 如何选择合适的提示词

| 场景 | 推荐提示词 | 原因 |
|------|----------|------|
| Go 项目，需要 BDD 风格 | `golang_ginkgo_test` | 清晰的场景描述，易维护 |
| Go 项目，简单测试 | `golang_standard_test` | 轻量级，适合简单场景 |
| Go 项目，批量生成 | `golang_ginkgo_file_test` | 一次性覆盖多个函数 |
| C++ 项目 | `cpp_google_test` | 业界标准，功能强大 |
| C 项目 | `c_unit_test` | 适合嵌入式和底层代码 |
| 测试失败需要修复 | `xxx_fix_test` | 自动分析和修复错误 |

### 2. 提示词调用流程

```python
from backend.app.services.prompt_templates import get_prompt_templates

# 获取提示词模板实例
templates = get_prompt_templates()

# 生成 Ginkgo 测试
prompt = templates.golang_ginkgo_test(
    func_name="CalMemory",
    func_body="...",
    params=["memoryMB int"],
    return_type="string",
    receiver="c *Calculator",
    module_path="github.com/example/project",
    package_name="biz",
    file_path="internal/biz/calculator.go"
)

# 将提示词发送给 AI
response = ai_client.generate(prompt)
```

### 3. 提示词优化建议

**为新语言添加提示词**:
1. 在 `PromptTemplates` 类中添加新方法
2. 遵循现有的命名规范: `{language}_{framework}_test`
3. 包含完整的测试框架说明
4. 提供清晰的示例代码
5. 添加常见错误处理指南

**优化现有提示词**:
1. 收集测试生成失败的案例
2. 分析 AI 生成的错误模式
3. 在提示词中添加更明确的约束
4. 使用示例代码引导正确生成
5. 添加禁止性规则（❌ 不要...）

---

## 核心设计原则

### 1. 提示词结构化

每个提示词都应包含以下部分：

```
## 项目信息
- 提供上下文信息（模块路径、包名、文件路径）

## 目标函数/代码
- 展示需要测试的代码

## 核心要求（必须严格遵守）
- 明确的规则和约束
- 使用 ✅ 和 ❌ 标记正确和错误的做法

## 测试框架要求
- 框架特定的规范
- 代码结构要求

## 模板参考
- 提供优秀的示例代码
- 展示预期的输出格式

## 输出要求
- 明确输出格式
- 避免常见错误
```

### 2. 渐进式约束

提示词的约束层次：

1. **总体规则**: 适用于所有测试的通用规则
2. **框架规则**: 特定测试框架的规范
3. **语言规则**: 编程语言特定的要求
4. **项目规则**: 当前项目的约定

### 3. 示例驱动

- 每个提示词都应包含清晰的示例代码
- 示例应展示最佳实践
- 使用注释说明关键点
- 对比正确和错误的做法

### 4. 错误预防

在提示词中明确禁止常见错误：

```
❌ 不要使用外部测试包（package xxx_test）
❌ 不要导入被测试的包
❌ 不要生成未使用的变量
❌ 不要在 Describe 块顶部声明变量
```

### 5. 可维护性

- 集中管理所有提示词
- 使用 Python 方法封装
- 支持参数化和复用
- 易于版本控制和更新

---

## 提示词演进历史

### v1.0.0 - 初始版本
- 基础的 Go、C++、C 测试提示词
- 简单的测试生成逻辑

### v1.1.0 - 集中化管理
- 创建 `PromptTemplates` 类
- 所有提示词集中管理
- 支持参数化配置

### v1.2.0 - 代码基测试
- 添加基于代码分析的智能测试生成
- 根据函数复杂度动态调整测试用例数量

### v1.3.0 - 同包测试策略
- 强制使用 `package xxx`（不使用 `_test` 后缀）
- 优化导入规则
- 避免循环依赖

### v1.4.0 - 代码简洁性优化
- **不生成未使用的变量声明**
- 移除 Describe 块顶部的变量声明
- 在注释中说明需要的变量
- 保持生成的测试代码简洁

---

## 最佳实践

### 1. 提示词编写

**✅ 好的提示词**:
- 结构清晰，层次分明
- 包含丰富的示例代码
- 明确的约束和规则
- 对比正确和错误的做法
- 使用表情符号增强可读性

**❌ 差的提示词**:
- 模糊不清的描述
- 缺少示例
- 规则过于宽泛
- 没有错误预防

### 2. 测试生成

**优先级**:
1. 纯函数（无副作用）
2. 核心业务逻辑
3. 复杂计算
4. 有依赖的方法（需要 mock）
5. 简单的 getter/setter

**测试策略**:
- 纯函数：直接测试，不使用 mock
- 有依赖的方法：使用 mock 模拟依赖
- 每个函数至少 3 种场景：Normal、Boundary、Exception

### 3. 代码质量

**确保生成的测试**:
- ✅ 语法正确，可以直接编译
- ✅ 没有未使用的变量
- ✅ 遵守同包测试规则
- ✅ 覆盖正常、边界、异常场景
- ✅ 包含清晰的注释说明

---

## 总结

### 📊 提示词统计

| 类别 | 提示词数量 | 用途 |
|------|----------|------|
| Golang | 5 个 | Go 测试生成和修复 |
| C++ | 2 个 | C++ 测试生成和修复 |
| C | 2 个 | C 测试生成和修复 |
| 系统 | 1 个 | 通用系统提示词 |
| **总计** | **10 个** | 全面覆盖测试生成需求 |

### 🎯 核心特点

1. **结构化设计**: 每个提示词都有清晰的结构和层次
2. **示例驱动**: 丰富的示例代码引导 AI 正确生成
3. **错误预防**: 明确禁止常见错误，提高生成质量
4. **同包测试**: Go 测试使用同包策略，避免循环依赖
5. **代码简洁**: 不生成未使用的变量，保持代码干净

### 🚀 持续改进

提示词会根据以下因素持续优化：
- 用户反馈和实际使用情况
- AI 生成的代码质量分析
- 新的测试框架和最佳实践
- 编程语言的演进

---

**文档版本**: v1.4.0  
**最后更新**: 2025-10-30  
**维护者**: AI Test Agent Team

