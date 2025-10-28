# 提示词模板系统说明

## ✨ 新特性：集中式提示词管理

我们实现了**集中式提示词管理**系统，所有 AI 提示词现在都在程序内部预先定义，而不是由客户端指定。

## 📍 核心文件

```
backend/app/services/prompt_templates.py  # 提示词模板集中管理
```

## 🎯 主要优势

### 1. 统一标准
所有测试生成使用一致的、经过验证的提示词策略。

### 2. 质量保证
- ✅ 自动检测 Go 模块路径（从 go.mod）
- ✅ 智能推断包名和导入路径
- ✅ 自动替换占位符
- ✅ 确保符合框架规范

### 3. 易于维护
修改提示词只需编辑一个文件，所有引用自动更新。

### 4. 安全可控
避免客户端传入不安全或低质量的提示词。

## 📚 可用的提示词模板

### Golang 测试生成

```python
from app.services.prompt_templates import get_prompt_templates

templates = get_prompt_templates()

# 1. Go 标准测试（testing 包）
prompt = templates.golang_standard_test(
    func_name="Calculate",
    func_body="return a + b",
    params=["a int", "b int"],
    return_type="int",
    receiver=""
)

# 2. Ginkgo BDD 测试
prompt = templates.golang_ginkgo_test(
    func_name="CreateUser",
    func_body="...",
    params=["ctx context.Context", "req *pb.CreateUserRequest"],
    return_type="(*pb.CreateUserReply, error)",
    receiver="*UserService",
    module_path="bt.baishancloud.com/baishanone/cloud-ecs-api",
    package_name="service",
    file_path="internal/service/user.go"
)

# 3. 整个文件的 Ginkgo 测试
prompt = templates.golang_ginkgo_file_test(
    module_path="your-module",
    package_name="biz",
    file_path="internal/biz/user.go",
    functions_info=[...],
    source_code_snippet="..."
)

# 4. 修复失败的测试
prompt = templates.golang_fix_test(
    original_test="...",
    error_output="...",
    source_code="...",
    module_path="your-module",
    package_name="biz"
)

# 5. 修复语法错误
prompt = templates.golang_syntax_fix(
    test_code="...",
    syntax_errors=["error1", "error2"],
    file_analysis={...},
    language="golang",
    test_framework="ginkgo"
)
```

### C++ 测试生成

```python
# Google Test
prompt = templates.cpp_google_test(
    func_name="calculate",
    func_body="return a + b;"
)

# 修复失败的测试
prompt = templates.cpp_fix_test(
    original_test="...",
    error_output="..."
)
```

### C 测试生成

```python
# C 单元测试
prompt = templates.c_unit_test(
    func_name="calculate",
    func_body="return a + b;",
    test_framework="cunit"
)

# 修复失败的测试
prompt = templates.c_fix_test(
    original_test="...",
    error_output="..."
)
```

### 系统提示词

```python
# 通用系统提示词
system_msg = templates.system_prompt()
```

## 🔧 如何定制提示词

### 方法 1: 修改现有模板

编辑 `backend/app/services/prompt_templates.py` 文件：

```python
@staticmethod
def golang_ginkgo_test(...) -> str:
    """Ginkgo BDD 测试框架提示词"""
    return f"""请为以下Go函数生成基于Ginkgo/Gomega的BDD风格单元测试。

## 你的定制规则
1. 使用特定的命名约定
2. 添加额外的测试场景
3. ...

请只返回测试代码。
"""
```

### 方法 2: 添加新模板

在 `PromptTemplates` 类中添加新方法：

```python
@staticmethod
def golang_custom_test(func_name: str, custom_param: str) -> str:
    """自定义测试提示词"""
    return f"""
    为 {func_name} 生成自定义测试
    自定义参数: {custom_param}
    """
```

然后在 `test_generator.py` 中使用：

```python
def _build_custom_prompt(self, function_info: Dict) -> str:
    return self.prompt_templates.golang_custom_test(
        func_name=function_info['name'],
        custom_param="your_value"
    )
```

## 🔄 修改提示词后

```bash
# 重启服务使更改生效
docker-compose restart backend celery-worker

# 测试新的提示词
python example_generate_tests.py
```

## 🎓 提示词设计原则

### 1. 结构清晰
```
## 第一部分：上下文信息
## 第二部分：目标代码
## 第三部分：规则要求
## 第四部分：示例格式
## 第五部分：输出要求
```

### 2. 包含示例
在提示词中包含具体的代码示例，帮助 AI 理解预期格式。

### 3. 明确约束
明确说明什么能做、什么不能做。

### 4. 参数化设计
使用参数而不是硬编码值。

## 📖 详细文档

完整的提示词管理指南：
- [docs/guides/PROMPT_MANAGEMENT.md](docs/guides/PROMPT_MANAGEMENT.md)

## 🎉 示例效果

### 自动生成的导入路径

**以前（错误）：**
```go
import "your-module-path/internal/biz"
```

**现在（正确）：**
```go
import "bt.baishancloud.com/baishanone/cloud-ecs-api/internal/biz"
```

### 自动推断的包名

**文件位置：** `internal/biz/user.go`

**自动生成：**
```go
package biz  // 同包测试，直接使用 biz
```

或

```go
package biz_test  // 外部测试，使用 biz_test
```

## ❓ 常见问题

**Q: 提示词可以在运行时修改吗？**
A: 不建议。提示词应该在代码中预定义，通过版本控制管理。

**Q: 如何为特定项目定制提示词？**
A: 修改 `prompt_templates.py` 文件，或通过项目配置参数影响提示词内容。

**Q: 客户端可以传入自定义提示词吗？**
A: 不可以。为了保证质量和安全，所有提示词都在服务器端预定义。

## 🚀 开始使用

系统已经内置了所有必需的提示词模板，你可以直接使用：

```bash
# 运行示例
python example_generate_tests.py

# 选择场景 1 或 2，查看自动生成的测试
```

生成的测试将自动：
- ✅ 使用正确的模块路径
- ✅ 使用正确的包名
- ✅ 包含正确的导入语句
- ✅ 遵循框架最佳实践

无需任何手动配置！🎊

