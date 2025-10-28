"""
AI 测试生成提示词模板管理

所有提示词集中在这里管理，便于维护和定制
"""

from typing import Dict, List
from pathlib import Path


class PromptTemplates:
    """提示词模板管理器"""
    
    # ==================== Golang 测试提示词 ====================
    
    @staticmethod
    def golang_standard_test(
        func_name: str,
        func_body: str,
        params: List[str],
        return_type: str,
        receiver: str = ""
    ) -> str:
        """Go 标准测试框架提示词"""
        return f"""请为以下Go函数生成完整的单元测试。

## 目标函数
```go
func {func_name}({', '.join(params)}) {return_type} {{
{func_body}
}}
```

## 测试要求
1. 使用Go标准库的testing包
2. 测试函数名应为 Test{func_name}
3. 覆盖以下场景:
   - 正常输入的测试用例
   - 边界条件测试
   - 异常输入测试（如果适用）
4. 使用table-driven test风格（如果适合）
5. 包含清晰的测试用例描述
6. 使用适当的断言

## 示例格式
```go
func Test{func_name}(t *testing.T) {{
    tests := []struct {{
        name string
        // 输入参数
        want // 期望结果
    }}{{
        // 测试用例
    }}
    
    for _, tt := range tests {{
        t.Run(tt.name, func(t *testing.T) {{
            // 测试逻辑
        }})
    }}
}}
```

请只返回测试代码，不要包含额外的解释。
"""
    
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
- 文件路径: {file_path}

## 目标函数
```go
func {func_name}({', '.join(params)}) {return_type} {{
{func_body}
}}
```

## 重要规则（必须遵守）

### 1. 包声明
**必须使用同包测试（in-package testing）**:
```go
package {package_name}  // ✅ 正确：使用同包名
```

**不要使用外部测试包**:
```go
package {package_name}_test  // ❌ 错误：不要使用 _test 后缀
```

### 2. 导入规则（根据测试类型决定）

**纯函数测试（无外部依赖）**:
```go
import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)
```

**有依赖的方法测试（需要 mock）**:
```go
import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    "github.com/golang/mock/gomock"
    "your-project/internal/mocks"  // 根据实际项目路径
)
```

**严格禁止导入以下内容**:
- ❌ **绝对不要**导入其他项目内部包（除了 mocks）
- ❌ **绝对不要**导入被测试的包本身（使用同包测试）
- ❌ **绝对不要**导入不需要的包

**关于 Mock 的重要说明**:
- ✅ **纯函数优先测试**：无副作用、无外部依赖的函数直接测试，不需要 mock
- ✅ **有依赖时使用 Mock**：对于依赖数据库、外部服务的方法，使用 gomock 模拟依赖
- 📋 **测试策略分类**：
  - 纯函数（如计算、转换）：直接传入参数测试，无需 mock
  - 有依赖的方法（如数据库操作）：使用 gomock.NewController() 和 mock 对象

**同包测试说明**:
由于使用同包测试（package {package_name}），所有包内的类型、函数、变量都可以直接使用，
**无需也不应该**导入任何项目内部的包。如果你发现自己想要导入项目内部的包，
这说明你没有正确使用同包测试模式。

### 3. 类型和函数引用
因为使用同包测试，可以直接使用包内的所有类型和函数:
```go
var config *Config  // ✅ 直接使用，不需要包名前缀
result := SomeFunction()  // ✅ 直接调用包内函数
```

### 4. 测试方式和策略

**🎯 测试策略分类**:
1. **纯函数优先**: 无副作用的函数最容易测试，应优先覆盖
   - 示例: CalMemory, CalDiskCapacity, CalIpNum, CalBillStartEndTime
   - 这些方法无外部依赖，可以直接测试，不需要 mock

2. **使用 Mock 测试依赖**: 依赖数据库或外部服务的方法
   - 示例: CustomerList, GetBill 等依赖数据库的方法
   - 需要使用 gomock 模拟数据库操作

**📊 测试场景分类** (每个方法至少包含以下三种场景):

✓ **Normal Case (正常场景)**
  - 测试典型的业务流程和预期输入
  - 验证正常情况下的输出结果
  - 示例: 计算正常的内存值、处理有效的时间范围

✓ **Boundary Case (边界场景)**
  - 测试边界值和临界条件
  - 包括: 零值、空值、最大值、最小值
  - 示例: 内存为0、空IP列表、时间范围为0

✓ **Exception Case (异常场景)**
  - 测试错误处理和异常情况
  - 包括: 负数、超出范围、无效输入、数据库错误
  - 示例: 负的内存值、数据库连接失败

## 测试设计原则

### 1. 优先级排序
- ✅ **高优先级**: 纯函数（无副作用）、核心业务逻辑、复杂计算
- ⚠️ **中优先级**: 有外部依赖但可 mock 的方法
- ❌ **低优先级**: 简单的 getter/setter、第三方库封装

### 2. 三段式测试结构 (AAA Pattern)
每个测试用例都应遵循 AAA 模式：
```go
It("should do something", func() {{
    // Arrange - 准备测试数据和环境
    input := prepareTestData()
    
    // Act - 执行被测试的方法
    result := methodUnderTest(input)
    
    // Assert - 验证结果是否符合预期
    Expect(result).To(Equal(expected))
}})
```

### 3. 每个测试只验证一件事
- 保持测试的单一职责，易于定位问题
- 如果需要验证多个方面，拆分成多个测试用例

### 4. 使用真实且有意义的数据
- 时间戳用真实日期并添加注释（如 `// 2021-09-01`）
- IP 地址使用真实格式（如 `8.8.8.8`, `192.168.1.1`）
- 增强测试的可读性和可维护性

### 5. 测试覆盖率目标
- 代码覆盖率达到 80%+
- 核心业务逻辑 100% 覆盖
- 所有公开 API 都有测试

## 测试要求
1. 使用Ginkgo BDD测试框架和Gomega断言库
2. 使用Describe/Context/It结构组织测试
3. 使用BeforeEach进行测试前置设置（初始化对象或 mock controller）
4. 使用AfterEach进行清理（如 ctrl.Finish() 验证 mock 期望）
5. 覆盖场景:
   - Normal: 正常输入的测试用例（多个典型场景）
   - Boundary: 边界条件测试（空值、零值、极限值等）
   - Exception: 异常输入测试（错误输入、nil指针、数据库错误等）
6. 测试用例需要自包含（self-contained），不依赖外部状态
7. 使用Gomega的流畅断言API
8. 每个 Context 应该描述一个测试场景，每个 It 应该测试一个具体用例

## BDD 风格测试结构

**测试组织层次**:
```go
Describe("方法名", func() {{
    Context("when 场景描述", func() {{
        It("should 预期行为", func() {{
            // Arrange - 准备测试数据
            input := testData

            // Act - 执行被测试的方法
            result := methodUnderTest(input)

            // Assert - 验证结果
            Expect(result).To(Equal(expected))
        }})
    }})
}})
```

**测试命名规范**:
- **Describe**: 描述被测试的方法或功能
- **Context**: 描述测试场景 (when/given)
- **It**: 描述预期行为 (should)

示例:
```
Describe("CalMemory")
  Context("when memory is divisible by 1024")
    It("should return integer value without decimal")
```

## 优秀的测试模板参考

### 模板1: 纯函数测试（无 Mock）

以下是测试纯函数的完整示例：

```go
var _ = Describe("XdyEcsBillCase", func() {{
    var (
        xdyEcsBillCase *XdyEcsBillCase
    )

    BeforeEach(func() {{
        // 创建实例用于测试纯函数
        // 纯函数不依赖外部服务，直接传入 nil 或简单值
        xdyEcsBillCase = NewXdyEcsBillCase(nil, nil, nil, nil)
    }})

    Describe("CalMemory", func() {{
        // Normal Case - 正常场景
        Context("when memory is divisible by 1024", func() {{
            It("should return integer value without decimal", func() {{
                // Arrange - 准备测试数据
                memoryMB := 1024
                
                // Act - 执行方法
                result := xdyEcsBillCase.CalMemory(memoryMB)
                
                // Assert - 验证结果
                Expect(result).To(Equal("1"))
            }})

            It("should return correct value for 2048 MB", func() {{
                // Arrange
                memoryMB := 2048
                
                // Act
                result := xdyEcsBillCase.CalMemory(memoryMB)
                
                // Assert
                Expect(result).To(Equal("2"))
            }})
        }})

        // Normal Case - 带小数的正常场景
        Context("when memory has decimal places", func() {{
            It("should return value with one decimal place", func() {{
                // Arrange
                memoryMB := 1536 // 1.5 GB
                
                // Act
                result := xdyEcsBillCase.CalMemory(memoryMB)
                
                // Assert
                Expect(result).To(Equal("1.5"))
            }})
        }})

        // Boundary Case - 边界场景
        Context("when memory is zero", func() {{
            It("should return 0", func() {{
                // Arrange
                memoryMB := 0
                
                // Act
                result := xdyEcsBillCase.CalMemory(memoryMB)
                
                // Assert
                Expect(result).To(Equal("0"))
            }})
        }})
    }})

    Describe("CalDiskCapacity", func() {{
        Context("when disk capacity is greater than present capacity", func() {{
            It("should return correct billable disk capacity", func() {{
                result := xdyEcsBillCase.CalDiskCapacity(100, 40)
                Expect(result).To(Equal(60))
            }})

            It("should return correct value for 80GB disk with 40GB present", func() {{
                result := xdyEcsBillCase.CalDiskCapacity(80, 40)
                Expect(result).To(Equal(40))
            }})
        }})

        Context("when disk capacity equals present capacity", func() {{
            It("should return 0", func() {{
                result := xdyEcsBillCase.CalDiskCapacity(40, 40)
                Expect(result).To(Equal(0))
            }})
        }})

        Context("when disk capacity is less than present capacity", func() {{
            It("should return negative value", func() {{
                result := xdyEcsBillCase.CalDiskCapacity(20, 40)
                Expect(result).To(Equal(-20))
            }})
        }})
    }})

    Describe("CalBillStartEndTime", func() {{
        Context("when bill period overlaps with request period", func() {{
            It("should use request end time if bill is still ongoing (billEndTime = 0)", func() {{
                isBill, retStartTime, retEndTime := xdyEcsBillCase.CalBillStartEndTime(
                    1630368000, // 2021-09-01 (bill start)
                    0,          // Still ongoing
                    1630368000, // 2021-09-01 (request start)
                    1632960000, // 2021-09-30 (request end)
                )
                Expect(isBill).To(BeTrue())
                Expect(retStartTime).To(Equal(1630368000))
                Expect(retEndTime).To(Equal(1632960000)) // Should use request end time
            }})

            It("should use bill end time if bill ends before request end", func() {{
                isBill, retStartTime, retEndTime := xdyEcsBillCase.CalBillStartEndTime(
                    1630368000, // 2021-09-01 (bill start)
                    1631577600, // 2021-09-14 (bill end, before request end)
                    1630368000, // 2021-09-01 (request start)
                    1632960000, // 2021-09-30 (request end)
                )
                Expect(isBill).To(BeTrue())
                Expect(retEndTime).To(Equal(1631577600)) // Should use bill end time
            }})

            It("should use request start time if bill starts before request", func() {{
                isBill, retStartTime, retEndTime := xdyEcsBillCase.CalBillStartEndTime(
                    1625097600, // 2021-07-01 (bill start)
                    1633046400, // 2021-10-01 (bill end)
                    1630368000, // 2021-09-01 (request start)
                    1632960000, // 2021-09-30 (request end)
                )
                Expect(isBill).To(BeTrue())
                Expect(retStartTime).To(Equal(1630368000)) // Should use request start time
                Expect(retEndTime).To(Equal(1632960000))   // Should use request end time
            }})
        }})

        Context("when bill period does not overlap with request period", func() {{
            It("should not bill if bill end time is before request start time", func() {{
                isBill, _, _ := xdyEcsBillCase.CalBillStartEndTime(
                    1625097600, // 2021-07-01
                    1627689600, // 2021-07-31
                    1630368000, // 2021-09-01
                    1633046400, // 2021-10-01
                )
                Expect(isBill).To(BeFalse())
            }})

            It("should not bill if bill start time is after request end time", func() {{
                isBill, _, _ := xdyEcsBillCase.CalBillStartEndTime(
                    1633651200, // 2021-10-08
                    1635897600, // 2021-11-03
                    1630368000, // 2021-09-01
                    1633046400, // 2021-10-01
                )
                Expect(isBill).To(BeFalse())
            }})
        }})
    }})
}})
```

### 模板2: 使用 Mock 测试有依赖的方法

以下是使用 gomock 测试有外部依赖方法的示例：

```go
var _ = Describe("CostCase", func() {{
    var (
        costCase       *CostCase
        mockRepo       *mocks.MockRepository
        mockLogger     *mocks.MockLogger
        ctrl           *gomock.Controller
        ctx            context.Context
    )

    BeforeEach(func() {{
        // 初始化 mock controller
        ctrl = gomock.NewController(GinkgoT())
        mockRepo = mocks.NewMockRepository(ctrl)
        mockLogger = mocks.NewMockLogger(ctrl)
        ctx = context.Background()
        
        // 创建被测试对象，注入 mock 依赖
        costCase = NewCostCase(mockRepo, mockLogger)
    }})

    AfterEach(func() {{
        // 验证所有 mock 期望都被满足
        ctrl.Finish()
    }})

    Describe("GetCustomerBill", func() {{
        // Normal Case - 正常场景：数据库返回成功
        Context("when database returns data successfully", func() {{
            It("should return customer bill list", func() {{
                // Arrange - 准备测试数据和 mock 期望
                customerID := "cust001"
                expectedBills := []Bill{{
                    {{CustomerID: "cust001", Amount: 100.5}},
                    {{CustomerID: "cust002", Amount: 200.0}},
                }}
                
                // 设置 mock 期望
                mockRepo.EXPECT().
                    FindBills(ctx, customerID).
                    Return(expectedBills, nil)

                // Act - 执行被测试的方法
                result, err := costCase.GetCustomerBill(ctx, customerID)

                // Assert - 验证结果
                Expect(err).NotTo(HaveOccurred())
                Expect(result).To(Equal(expectedBills))
                Expect(len(result)).To(Equal(2))
            }})
        }})

        // Exception Case - 异常场景：数据库错误
        Context("when database returns error", func() {{
            It("should handle database connection error gracefully", func() {{
                // Arrange
                customerID := "cust001"
                
                // 设置 mock 返回错误
                mockRepo.EXPECT().
                    FindBills(ctx, customerID).
                    Return(nil, errors.New("database connection failed"))

                // Act
                result, err := costCase.GetCustomerBill(ctx, customerID)

                // Assert
                Expect(err).To(HaveOccurred())
                Expect(result).To(BeNil())
                Expect(err.Error()).To(ContainSubstring("database connection failed"))
            }})
        }})

        // Boundary Case - 边界场景：返回空列表
        Context("when customer has no bills", func() {{
            It("should return empty list", func() {{
                // Arrange
                customerID := "cust999"
                
                // 设置 mock 返回空列表
                mockRepo.EXPECT().
                    FindBills(ctx, customerID).
                    Return([]Bill{{}}, nil)

                // Act
                result, err := costCase.GetCustomerBill(ctx, customerID)

                // Assert
                Expect(err).NotTo(HaveOccurred())
                Expect(result).To(BeEmpty())
            }})
        }})
    }})
}})
```

## Mock 使用指南

### 何时使用 Mock
- 外部服务调用 (API, 数据库, 文件系统)
- 耗时操作 (网络请求, 复杂计算)
- 不稳定的依赖 (随机数, 当前时间)
- 难以复现的场景 (错误条件, 边界情况)

### Mock 最佳实践
1. **只 mock 你拥有的接口** - 不要直接 mock 第三方库
2. **验证交互而非实现** - 关注行为，不是实现细节
3. **保持 mock 简单** - 避免过度复杂的 mock 设置
4. **使用真实数据** - mock 返回的数据应该真实可信

### Mock 使用步骤

**1. 在 BeforeEach 中初始化**:
```go
BeforeEach(func() {{
    // 创建 mock controller
    ctrl = gomock.NewController(GinkgoT())
    
    // 初始化所有需要的 mock 对象
    mockRepo = mocks.NewMockRepository(ctrl)
    mockLogger = mocks.NewMockLogger(ctrl)
    
    // 创建被测试对象，注入 mock 依赖
    costCase = NewCostCase(mockRepo, mockLogger)
}})
```

**2. 设置 Mock 期望**:
```go
// 使用 .EXPECT() 设置期望的方法调用
// 使用 .Return() 设置返回值
mockRepo.EXPECT().
    FindBills(ctx, "cust001").
    Return(expectedBills, nil)

// 可以使用 .Times() 设置调用次数
mockLogger.EXPECT().
    Info(gomock.Any()).
    Times(1)
```

**3. 在 AfterEach 中验证**:
```go
AfterEach(func() {{
    // 调用 ctrl.Finish() 验证所有期望都被满足
    ctrl.Finish()
}})
```

## 测试结构要点

1. **清晰的层次结构**:
   - 第一层 Describe: 描述被测试的类或结构体
   - 第二层 Describe: 描述被测试的方法
   - Context: 描述测试场景（"when xxx"）
   - It: 描述期望行为（"should xxx"）

2. **BeforeEach 的使用**:
   - 在外层 Describe 中设置通用的测试数据
   - 对纯函数：创建实例，依赖传 nil
   - 对有依赖的方法：初始化 mock controller 和 mock 对象

3. **测试用例组织**:
   - 按照不同的输入条件分组（正常值、边界值、特殊值、零值）
   - 每个 It 只测试一个具体场景
   - 使用描述性的字符串说明测试意图
   - **直接传入不同的参数组合来测试不同的行为**

4. **断言风格**:
   - 使用 Gomega 的流畅断言 API
   - `Expect(actual).To(Equal(expected))` 
   - **添加行内注释说明测试数据的含义**（如 `// 2021-09-01 (bill start)`）
   - 对多返回值分别进行断言验证

5. **测试策略选择**:
   - ✅ **纯函数**：直接测试，不使用 mock
   - ✅ **有依赖的方法**：使用 gomock 和 mock 对象
   - 重点是参数的不同组合和场景覆盖（正常、边界、异常）

## Gomega 常用断言
- `Expect(actual).To(Equal(expected))` - 相等判断
- `Expect(err).NotTo(HaveOccurred())` - 无错误
- `Expect(err).To(HaveOccurred())` - 有错误
- `Expect(value).To(BeNil())` - nil 判断
- `Expect(value).NotTo(BeNil())` - 非 nil 判断
- `Expect(slice).To(ContainElement(item))` - 包含元素
- `Expect(value).To(BeNumerically(">", 0))` - 数值比较
- `Expect(str).To(ContainSubstring("text"))` - 字符串包含
- `Expect(value).To(BeTrue())` / `BeFalse()` - 布尔判断

请参考上面的优秀模板，生成结构清晰、覆盖全面的测试代码。
只返回测试逻辑代码（Describe/Context/It部分），不要包含package声明、import语句和测试套件注册代码（TestXxx函数）。
"""
    
    @staticmethod
    def golang_ginkgo_file_test(
        module_path: str,
        package_name: str,
        file_path: str,
        functions_info: List[Dict],
        source_code_snippet: str = ""
    ) -> str:
        """Ginkgo 整个文件测试提示词"""
        
        # 构建函数列表
        functions_list = []
        for f in functions_info:
            func_desc = f"- {f['signature']}\n"
            func_desc += f"  代码行数: {f.get('executable_lines', 0)}行，复杂度: {f.get('complexity', 1)}\n"
            func_desc += f"  建议测试用例: {f.get('test_count', 3)}个 (正常:{f.get('normal_count', 1)}, 边界:{f.get('edge_count', 1)}, 异常:{f.get('error_count', 1)})"
            functions_list.append(func_desc)
        
        functions_list_str = "\n".join(functions_list)
        
        source_section = ""
        if source_code_snippet:
            source_section = f"""
## 源代码片段（供参考）
```go
{source_code_snippet}
```
"""
        
        return f"""请为以下Go源文件的函数生成Ginkgo BDD测试逻辑。

## 项目信息
- Go模块路径: {module_path}
- 包名: {package_name}
- 文件路径: {file_path}

## 需要测试的函数
{functions_list_str}
{source_section}

## 重要规则（必须严格遵守）

### 1. 包声明与导入
**必须使用同包测试**:
```go
package {package_name}  // ✅ 正确
```

**只导入必需的包**:
```go
import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)
```

**导入规则（根据测试类型）**:
- 纯函数测试：只导入 testing, ginkgo, gomega
- 有依赖的方法：可以导入 gomock 和 mocks 包

### 2. 测试结构
- 为每个函数生成一个 Describe 块
- 使用 Context 组织不同的测试场景
- 使用 It 编写具体的测试用例
- 根据上面的建议测试用例数量生成测试

### 3. 测试策略
**根据函数类型选择策略**:
1. **纯函数**（无外部依赖）：直接测试，通过不同参数组合验证行为
2. **有依赖的方法**（数据库、外部服务）：使用 gomock 模拟依赖

**场景覆盖**:
- Normal Case: 正常业务流程
- Boundary Case: 边界值和临界条件（零值、空值、最大/最小值）
- Exception Case: 错误处理和异常情况（负数、无效输入、数据库错误）

### 4. 测试质量要求
- 每个测试用例应该独立
- 使用有意义的描述（Describe/Context/It）
- 覆盖正常、边界、异常三种场景
- 使用 Gomega 的流畅断言
- 添加注释说明测试数据的含义
- 使用真实且有意义的数据（时间戳用真实日期，IP用真实IP）

## 优秀的测试模板参考

请根据函数类型选择合适的测试策略：
- **纯函数**：参考"模板1: 纯函数测试"
- **有依赖的方法**：参考"模板2: 使用 Mock 测试"

### 纯函数测试示例

```go
var _ = Describe("XdyEcsBillCase", func() {{
    var (
        xdyEcsBillCase *XdyEcsBillCase
    )

    BeforeEach(func() {{
        // 创建实例用于测试纯函数
        xdyEcsBillCase = NewXdyEcsBillCase(nil, nil, nil, nil)
    }})

    Describe("CalMemory", func() {{
        Context("when memory is divisible by 1024", func() {{
            It("should return integer value without decimal", func() {{
                result := xdyEcsBillCase.CalMemory(1024)
                Expect(result).To(Equal("1"))
            }})

            It("should return correct value for 2048 MB", func() {{
                result := xdyEcsBillCase.CalMemory(2048)
                Expect(result).To(Equal("2"))
            }})
        }})

        Context("when memory has decimal places", func() {{
            It("should return value with one decimal place", func() {{
                result := xdyEcsBillCase.CalMemory(1536) // 1.5 GB
                Expect(result).To(Equal("1.5"))
            }})
        }})

        Context("when memory is zero", func() {{
            It("should return 0", func() {{
                result := xdyEcsBillCase.CalMemory(0)
                Expect(result).To(Equal("0"))
            }})
        }})
    }})

    Describe("CalDiskCapacity", func() {{
        // Normal Case - 正常场景
        Context("when disk capacity is greater than present capacity", func() {{
            It("should return correct billable disk capacity", func() {{
                // Arrange
                diskCapacity := 100
                presentCapacity := 40
                
                // Act
                result := xdyEcsBillCase.CalDiskCapacity(diskCapacity, presentCapacity)
                
                // Assert
                Expect(result).To(Equal(60))
            }})
        }})

        // Boundary Case - 边界场景
        Context("when disk capacity equals present capacity", func() {{
            It("should return 0", func() {{
                // Arrange
                diskCapacity := 40
                presentCapacity := 40
                
                // Act
                result := xdyEcsBillCase.CalDiskCapacity(diskCapacity, presentCapacity)
                
                // Assert
                Expect(result).To(Equal(0))
            }})
        }})
    }})

    Describe("CalBillStartEndTime", func() {{
        // Normal Case - 正常场景：时间段重叠
        Context("when bill period overlaps with request period", func() {{
            It("should use request end time if bill is still ongoing (billEndTime = 0)", func() {{
                // Arrange
                billStartTime := 1630368000   // 2021-09-01 (bill start)
                billEndTime := 0              // Still ongoing
                requestStartTime := 1630368000 // 2021-09-01 (request start)
                requestEndTime := 1632960000   // 2021-09-30 (request end)
                
                // Act
                isBill, retStartTime, retEndTime := xdyEcsBillCase.CalBillStartEndTime(
                    billStartTime, billEndTime, requestStartTime, requestEndTime,
                )
                
                // Assert
                Expect(isBill).To(BeTrue())
                Expect(retStartTime).To(Equal(1630368000))
                Expect(retEndTime).To(Equal(1632960000)) // Should use request end time
            }})

            It("should use bill end time if bill ends before request end", func() {{
                // Arrange
                billStartTime := 1630368000    // 2021-09-01 (bill start)
                billEndTime := 1631577600      // 2021-09-14 (bill end, before request end)
                requestStartTime := 1630368000 // 2021-09-01 (request start)
                requestEndTime := 1632960000   // 2021-09-30 (request end)
                
                // Act
                isBill, _, retEndTime := xdyEcsBillCase.CalBillStartEndTime(
                    billStartTime, billEndTime, requestStartTime, requestEndTime,
                )
                
                // Assert
                Expect(isBill).To(BeTrue())
                Expect(retEndTime).To(Equal(1631577600)) // Should use bill end time
            }})
        }})

        // Boundary Case - 边界场景：时间段不重叠
        Context("when bill period does not overlap with request period", func() {{
            It("should not bill if bill end time is before request start time", func() {{
                // Arrange
                billStartTime := 1625097600    // 2021-07-01
                billEndTime := 1627689600      // 2021-07-31
                requestStartTime := 1630368000 // 2021-09-01
                requestEndTime := 1633046400   // 2021-10-01
                
                // Act
                isBill, _, _ := xdyEcsBillCase.CalBillStartEndTime(
                    billStartTime, billEndTime, requestStartTime, requestEndTime,
                )
                
                // Assert
                Expect(isBill).To(BeFalse())
            }})
        }})
    }})
}})
```

## 测试结构要点

1. **清晰的层次结构**:
   - 第一层 Describe: 描述被测试的类或结构体（如果多个函数属于同一个类）
   - 第二层 Describe: 描述被测试的方法
   - Context: 描述测试场景（"when xxx"）
   - It: 描述期望行为（"should xxx"）

2. **BeforeEach 的使用**:
   - 在外层 Describe 中设置通用的测试数据
   - 纯函数：创建实例，依赖项传 nil
   - 有依赖的方法：初始化 mock controller 和 mock 对象
   - 每个测试用例执行前都会运行

3. **测试用例组织**:
   - 按照不同的输入条件分组（正常值、边界值、特殊值、零值）
   - 每个 It 只测试一个具体场景
   - 使用描述性的字符串说明测试意图
   - 每个 Context 包含多个相关的 It
   - 覆盖 Normal, Boundary, Exception 三种场景

4. **断言风格**:
   - 使用 Gomega 的流畅断言 API
   - `Expect(actual).To(Equal(expected))`
   - **添加行内注释说明测试数据的含义**（如 `// 2021-09-01 (bill start)`）
   - 对多返回值分别进行断言验证

5. **测试策略选择**:
   - ✅ **纯函数**（无外部依赖）：直接测试，通过参数组合覆盖各种场景
   - ✅ **有依赖的方法**（数据库、外部服务）：使用 gomock 和 mock 对象
   - 重点是场景覆盖：正常、边界、异常
   - 使用真实且有意义的数据

## 输出格式
请只返回测试逻辑代码，包含所有函数的 Describe 块。
不要包含 package 声明、import 语句和套件注册函数。

请参考上面的优秀模板，为所有函数生成结构清晰、覆盖全面的测试逻辑。
"""
    
    @staticmethod
    def golang_fix_test(
        original_test: str,
        error_output: str,
        source_code: str,
        module_path: str,
        package_name: str
    ) -> str:
        """Go 测试修复提示词"""
        return f"""以下Go测试代码执行失败，请分析失败原因并修复测试代码。

## 项目信息
- Go模块路径: {module_path}
- 包名: {package_name}

## 原始测试代码
```go
{original_test}
```

## 错误输出
```
{error_output}
```

## 源代码上下文
```go
{source_code}
```

## 修复要求
1. 分析错误原因（编译错误、运行时错误、断言失败等）
2. 修复所有错误，使测试能够通过
3. 保持测试的完整性和覆盖范围
4. 确保包名和导入路径正确
5. 如果是 Ginkgo 测试，遵守同包测试规则
6. 不要导入不必要的包

## 常见问题修复指南
- 导入路径错误：使用正确的模块路径 {module_path}
- 包名错误：使用 package {package_name}（Ginkgo同包测试）
- Mock 相关：
  * 纯函数测试：不需要 mock，直接传参数
  * 有依赖的方法：确保正确导入 gomock 和 mocks 包
  * 检查 mock 期望设置是否正确
- 类型不匹配：检查源代码，使用正确的类型
- nil 指针：添加适当的 nil 检查

请返回修复后的完整测试代码，不要包含额外的解释。
"""
    
    @staticmethod
    def golang_syntax_fix(
        test_code: str,
        syntax_errors: List[str],
        file_analysis: Dict,
        language: str,
        test_framework: str
    ) -> str:
        """Go 语法错误修复提示词"""
        errors_str = "\n".join([f"- {err}" for err in syntax_errors])
        
        return f"""以下测试代码存在语法错误，请修复这些错误。

## 测试代码
```go
{test_code}
```

## 语法错误
{errors_str}

## 修复要求
1. 只修复语法错误，不要改变测试逻辑
2. 确保代码符合 {test_framework} 框架规范
3. 保持代码结构和测试覆盖范围不变
4. 确保包名和导入语句正确
5. 移除所有 markdown 代码块标记

请返回修复后的完整代码，不要包含 markdown 格式标记和额外解释。
"""
    
    # ==================== C++ 测试提示词 ====================
    
    @staticmethod
    def cpp_google_test(
        func_name: str,
        func_body: str
    ) -> str:
        """C++ Google Test 提示词"""
        return f"""请为以下C++函数生成完整的单元测试。

## 目标函数
```cpp
{func_name}(...) {{
{func_body}
}}
```

## Google Test示例
```cpp
TEST(TestSuiteName, TestName) {{
    // Arrange
    // Act
    // Assert
    EXPECT_EQ(expected, actual);
    ASSERT_TRUE(condition);
}}
```

## 测试要求
1. 覆盖正常情况、边界条件和异常情况
2. 使用AAA模式（Arrange-Act-Assert）
3. 测试用例应该独立且可重复
4. 包含清晰的测试描述

请只返回测试代码，不要包含额外的解释。
"""
    
    @staticmethod
    def cpp_fix_test(
        original_test: str,
        error_output: str
    ) -> str:
        """C++ 测试修复提示词"""
        return f"""以下C++测试代码执行失败，请分析失败原因并修复。

## 原始测试代码
```cpp
{original_test}
```

## 错误输出
```
{error_output}
```

## 修复要求
1. 分析错误原因
2. 修复所有错误
3. 保持测试完整性
4. 确保包含正确的头文件

请返回修复后的完整测试代码。
"""
    
    # ==================== C 测试提示词 ====================
    
    @staticmethod
    def c_unit_test(
        func_name: str,
        func_body: str,
        test_framework: str = "cunit"
    ) -> str:
        """C 单元测试提示词"""
        return f"""请为以下C函数生成完整的单元测试。

## 目标函数
```c
{func_name}(...) {{
{func_body}
}}
```

## 测试框架
使用{test_framework}

## 测试要求
1. 覆盖正常情况、边界条件和异常情况
2. 测试用例应该独立且可重复
3. 包含清晰的测试描述
4. 适当的断言

请只返回测试代码，不要包含额外的解释。
"""
    
    @staticmethod
    def c_fix_test(
        original_test: str,
        error_output: str
    ) -> str:
        """C 测试修复提示词"""
        return f"""以下C语言测试代码执行失败，请分析失败原因并修复。

## 原始测试代码
```c
{original_test}
```

## 错误输出
```
{error_output}
```

## 修复要求
1. 分析错误原因
2. 修复所有错误
3. 保持测试完整性
4. 确保包含正确的头文件

请返回修复后的完整测试代码。
"""
    
    # ==================== 系统提示词 ====================
    
    @staticmethod
    def system_prompt() -> str:
        """通用系统提示词"""
        return """🎯 你是一个专业的测试工程师，擅长为各种编程语言编写高质量的单元测试。

## 核心职责
1. 理解代码的业务逻辑和功能
2. 识别可测试的方法和边界条件
3. 编写清晰、完整、可维护的测试用例
4. 确保测试覆盖正常、边界和异常场景

## 测试设计原则

### 1. 优先级排序
- ✅ **高优先级**: 纯函数（无副作用）、核心业务逻辑、复杂计算
- ⚠️ **中优先级**: 有外部依赖但可 mock 的方法
- ❌ **低优先级**: 简单的 getter/setter、第三方库封装

### 2. 三段式测试结构 (AAA Pattern)
```
Arrange (准备) - 设置测试数据和环境
Act (执行)     - 调用被测试的方法
Assert (断言)  - 验证结果是否符合预期
```

### 3. 测试场景覆盖（每个方法至少包含三种场景）

**✓ Normal Case (正常场景)**
- 测试典型的业务流程，使用常见的有效输入
- 示例: 计算 1024MB 内存 → 应返回 "1GB"

**✓ Boundary Case (边界场景)**
- 测试边界值和临界条件
- 包括: 零值、空值、最大值、最小值、空集合
- 示例: 内存为 0 → 应返回 "0GB"

**✓ Exception Case (异常场景)**
- 测试错误处理和异常情况
- 包括: 负数、无效输入、超出范围、依赖失败
- 示例: 数据库连接失败 → 应抛出或返回错误

### 4. 测试独立性
- 每个测试应该独立运行，不依赖其他测试
- 测试之间不应该有顺序依赖
- 使用 setup/teardown 确保测试环境一致

### 5. 可读性优先
- 使用清晰的测试命名
- 添加必要的注释说明意图
- 使用真实且有意义的测试数据（时间戳用真实日期，IP用真实IP）
- 让测试成为代码的文档

## 测试策略选择
- ✅ **纯函数**（无外部依赖）：直接测试，通过不同参数组合验证行为，不使用 mock
- ✅ **有依赖的方法**（依赖数据库、外部服务）：使用 mock 模拟依赖

## Mock 使用指南

**何时使用 Mock**:
- 外部服务调用 (API, 数据库, 文件系统)
- 耗时操作 (网络请求, 复杂计算)
- 不稳定的依赖 (随机数, 当前时间)
- 难以复现的场景 (错误条件, 边界情况)

**Mock 最佳实践**:
1. **只 mock 你拥有的接口** - 不要直接 mock 第三方库
2. **验证交互而非实现** - 关注行为，不是实现细节
3. **保持 mock 简单** - 避免过度复杂的 mock 设置
4. **使用真实数据** - mock 返回的数据应该真实可信

## 测试覆盖率目标
- 代码覆盖率达到 80%+
- 核心业务逻辑 100% 覆盖
- 所有公开 API 都有测试
- 重点覆盖复杂计算和关键业务流程

## 生成要求
- 语法正确，可以直接运行
- 每个测试只验证一件事
- 使用 Arrange-Act-Assert 结构并添加注释
- 测试命名清晰易懂
- 不添加额外的解释文字，只生成代码
"""


# 单例实例
_prompt_templates = PromptTemplates()


def get_prompt_templates() -> PromptTemplates:
    """获取提示词模板实例"""
    return _prompt_templates

