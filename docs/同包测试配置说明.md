# Go 同包测试配置说明

## 📋 概述

AI Test Agent 使用 **同包测试（In-Package Testing）** 策略，测试代码和源代码在同一个 package 中。

## 🎯 同包测试 vs 外部测试包

### 同包测试（✅ 推荐使用）

```go
// 文件: internal/biz/user.go
package biz

type User struct {
    ID   int
    Name string
}

func (u *User) GetName() string {
    return u.Name
}
```

```go
// 文件: internal/biz/user_test.go
package biz  // ✅ 使用相同的包名

import (
    "testing"
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestUser(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "User Suite")
}

var _ = Describe("User", func() {
    var user *User  // ✅ 可以直接使用，无需包名前缀
    
    BeforeEach(func() {
        user = &User{ID: 1, Name: "John"}  // ✅ 直接访问
    })
    
    Describe("GetName", func() {
        It("should return user name", func() {
            result := user.GetName()  // ✅ 直接调用
            Expect(result).To(Equal("John"))
        })
    })
})
```

### 外部测试包（❌ 不推荐）

```go
// 文件: internal/biz/user_test.go
package biz_test  // ❌ 使用 _test 后缀

import (
    "testing"
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    
    // ❌ 需要导入被测试的包
    "your-project/internal/biz"
)

func TestUser(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "User Suite")
}

var _ = Describe("User", func() {
    var user *biz.User  // ❌ 需要包名前缀
    
    BeforeEach(func() {
        user = &biz.User{ID: 1, Name: "John"}  // ❌ 需要包名前缀
    })
    
    Describe("GetName", func() {
        It("should return user name", func() {
            result := user.GetName()  // ❌ 可能需要包名前缀
            Expect(result).To(Equal("John"))
        })
    })
})
```

## ✨ 同包测试的优势

### 1. 避免导入问题
```go
// ✅ 同包测试 - 无需导入
package biz

import (
    "testing"
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

// ❌ 外部测试包 - 需要导入，可能失败
package biz_test

import (
    "testing"
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    
    "your-project/internal/biz"  // 可能导致编译错误
)
```

### 2. 可以测试未导出的函数和类型

```go
// 源代码
package biz

// 未导出的函数
func calculateDiscount(price float64) float64 {
    return price * 0.9
}

// 同包测试 - ✅ 可以测试
package biz

var _ = Describe("calculateDiscount", func() {
    It("should calculate discount", func() {
        result := calculateDiscount(100.0)  // ✅ 可以直接调用
        Expect(result).To(Equal(90.0))
    })
})

// 外部测试包 - ❌ 无法测试
package biz_test

var _ = Describe("calculateDiscount", func() {
    It("should calculate discount", func() {
        result := biz.calculateDiscount(100.0)  // ❌ 编译错误：未导出
        Expect(result).To(Equal(90.0))
    })
})
```

### 3. 避免循环依赖

同包测试不会引入额外的导入，避免了可能的循环依赖问题。

### 4. 更高的编译成功率

- 不依赖项目的模块路径配置
- 不需要处理 vendor 依赖
- 不会因为 go.mod 配置问题导致失败

## 🔧 系统配置

### 提示词模板配置

在 `backend/app/services/prompt_templates.py` 中已配置：

```python
def golang_ginkgo_test(...):
    return f"""
    ### 1. 包声明
    **必须使用同包测试（in-package testing）**:
    ```go
    package {package_name}  // ✅ 正确：使用同包名
    ```
    
    **不要使用外部测试包**:
    ```go
    package {package_name}_test  // ❌ 错误：不要使用 _test 后缀
    ```
    
    ### 2. 导入规则
    **只导入必需的包**:
    ```go
    import (
        "testing"
        
        . "github.com/onsi/ginkgo/v2"
        . "github.com/onsi/gomega"
    )
    ```
    
    **严格禁止**:
    - ❌ 不要导入项目内部包
    - ❌ 不要导入被测试的包本身
    - ❌ 不要使用 _test 包名后缀
    """
```

### 自动清理功能

系统会自动清理不必要的导入：

```python
def _clean_internal_imports(self, test_code: str) -> str:
    """
    清理测试代码中不必要的项目内部导入
    
    对于同包测试，不应该导入项目内部的任何包
    """
    # 自动移除项目内部包的导入
    # 保留标准库和第三方库（如 ginkgo, gomega）
```

## 📝 使用示例

### 完整的测试文件示例

```go
// 文件: internal/biz/config_test.go
package biz  // ✅ 与源代码同包

import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

// 测试套件注册函数
func TestBiz(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Biz Suite")
}

// 测试用例
var _ = Describe("Config", func() {
    var config *Config  // ✅ 直接使用类型
    
    BeforeEach(func() {
        // TODO: 初始化测试对象
        config = &Config{
            TableName: "test_table",
        }
    })
    
    AfterEach(func() {
        // TODO: 清理工作
        config = nil
    })
    
    Describe("TableName", func() {
        Context("when normal scenario", func() {
            It("should return expected table name", func() {
                // TODO: 实现测试逻辑
                //
                // 测试场景：测试正常情况下获取表名
                // 输入参数: config.TableName = "test_table"
                // 预期输出: 返回 "test_table"
                //
                // 测试步骤:
                // 1. Arrange: config := &Config{TableName: "test_table"}
                // 2. Act: result := config.TableName()
                // 3. Assert: Expect(result).To(Equal("test_table"))
            })
        })
        
        Context("when edge case", func() {
            It("should handle empty table name correctly", func() {
                // TODO: 实现测试逻辑
                //
                // 测试场景：测试空表名的边界情况
                // 输入参数: config.TableName = ""
                // 预期输出: 返回默认表名或空字符串
                //
                // 测试步骤:
                // 1. Arrange: config := &Config{TableName: ""}
                // 2. Act: result := config.TableName()
                // 3. Assert: Expect(result).To(BeEmpty())
            })
        })
    })
})
```

## 🚀 运行测试

### 基本运行

```bash
# 进入项目目录
cd /path/to/project

# 运行测试
go test -v ./internal/biz/

# 使用 Ginkgo 运行
ginkgo -r -v ./internal/biz/
```

### 使用 -mod=mod 避免 vendor 限制

```bash
# 适用于使用 vendor 的项目
go test -mod=mod -v ./internal/biz/
ginkgo -r -v --mod=mod ./internal/biz/
```

## ⚠️ 注意事项

### 1. 导入规则

**只能导入这些包**：
- `testing` - Go 标准测试库
- `github.com/onsi/ginkgo/v2` - Ginkgo BDD 框架
- `github.com/onsi/gomega` - Gomega 断言库
- 必要的标准库（如 `context`, `time` 等）

**不能导入**：
- ❌ 项目内部包（如 `internal/repo`, `internal/service`）
- ❌ 被测试的包本身
- ❌ Mock 包（除非必要）

### 2. 测试文件命名

```bash
# ✅ 正确命名
user.go       → user_test.go
config.go     → config_test.go
service.go    → service_test.go

# ✅ 也可以按功能命名
user.go       → user_crud_test.go
              → user_validation_test.go
```

### 3. 包声明检查

生成测试后，检查包声明：

```bash
# 检查所有测试文件的包声明
grep "^package" internal/biz/*_test.go

# 应该输出（正确）：
# internal/biz/config_test.go:package biz
# internal/biz/user_test.go:package biz

# 不应该输出（错误）：
# internal/biz/config_test.go:package biz_test  ❌
```

## 🔍 故障排查

### 问题：测试无法编译

**检查包声明**：
```bash
head -1 internal/biz/config_test.go
```

应该显示：
```go
package biz  // ✅ 正确
```

而不是：
```go
package biz_test  // ❌ 错误
```

**解决方案**：修改包声明，移除 `_test` 后缀

### 问题：无法找到类型或函数

如果看到类似错误：
```
undefined: Config
undefined: User
```

**可能原因**：
1. 使用了外部测试包（`package biz_test`）
2. 类型或函数未导出（小写字母开头）

**解决方案**：
1. 改为同包测试（`package biz`）
2. 确保类型和函数已导出（大写字母开头）

### 问题：导入路径错误

如果看到类似错误：
```
cannot find module providing package your-project/internal/biz
```

**原因**：使用了外部测试包并导入了项目内部包

**解决方案**：改为同包测试，移除项目内部包的导入

## 📚 相关文档

- [CHANGELOG.md](../CHANGELOG.md) - 版本变更历史
- [Ginkgo 完全指南](./2-Ginkgo完全指南.md) - Ginkgo 测试框架详细说明
- [测试生成和修复](./2-测试生成和修复.md) - 测试生成功能说明
- [系统架构和API](./4-系统架构和API.md) - 系统架构文档

## 💡 最佳实践

### 1. 测试独立性

每个测试应该是独立的，使用 BeforeEach/AfterEach 确保清理：

```go
var _ = Describe("Service", func() {
    var service *Service
    
    BeforeEach(func() {
        service = NewService()
    })
    
    AfterEach(func() {
        service.Close()
        service = nil
    })
})
```

### 2. 使用有意义的描述

```go
// ✅ 好的描述
It("should return user name when user exists", func() { ... })

// ❌ 不好的描述
It("test 1", func() { ... })
```

### 3. 遵循 AAA 模式

```go
It("should calculate total price", func() {
    // Arrange - 准备测试数据
    price := 100.0
    quantity := 3
    
    // Act - 执行被测试的方法
    total := CalculateTotal(price, quantity)
    
    // Assert - 验证结果
    Expect(total).To(Equal(300.0))
})
```

## 🎉 总结

使用同包测试策略的好处：
- ✅ 避免复杂的导入问题
- ✅ 可以测试未导出的函数
- ✅ 更高的编译成功率
- ✅ 更简单的测试实现
- ✅ 避免循环依赖

AI Test Agent 已全面配置为使用同包测试，无需手动修改！

