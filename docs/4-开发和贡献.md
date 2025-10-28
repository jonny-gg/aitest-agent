# 💻 开发和贡献指南

本指南介绍如何参与 AI Test Agent 的开发和贡献。

---

## 📋 目录

1. [开发环境搭建](#开发环境搭建)
2. [代码规范](#代码规范)
3. [贡献流程](#贡献流程)
4. [扩展开发](#扩展开发)
5. [更新日志](#更新日志)

---

## 开发环境搭建

### 前置要求

- Python 3.9+
- Docker & Docker Compose
- Git
- Go 1.21+ (用于测试 Golang 项目)
- OpenAI API Key

### 本地开发环境

#### 1. 克隆项目

```bash
git clone <repository-url>
cd aitest-agent
```

#### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r backend/requirements.txt
```

#### 3. 配置环境变量

```bash
cp env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

#### 4. 启动服务

```bash
# 启动数据库和 Redis
docker-compose up -d postgres redis

# 启动 API 服务（开发模式）
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 Celery Worker（另一个终端）
celery -A app.celery_app worker --loglevel=info

# 启动 Flower 监控（可选）
celery -A app.celery_app flower
```

#### 5. 验证安装

```bash
# 健康检查
curl http://localhost:8000/health

# 访问 API 文档
open http://localhost:8000/docs

# 访问 Flower
open http://localhost:5555
```

### IDE 配置

#### VS Code

推荐安装以下扩展：

- Python
- Pylance
- Python Docstring Generator
- GitLens

**settings.json**：

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### PyCharm

1. 打开项目
2. 配置 Python 解释器（虚拟环境）
3. 启用 Black 格式化
4. 配置 pytest 作为测试运行器

---

## 代码规范

### Python 代码风格

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范：

- 使用 **4 空格**缩进
- 每行最多 **88 字符**（Black 默认）
- 使用 **snake_case** 命名变量和函数
- 使用 **PascalCase** 命名类
- 使用 **UPPER_CASE** 命名常量

### 代码格式化

使用 Black 进行代码格式化：

```bash
# 格式化单个文件
black backend/app/services/test_generator.py

# 格式化整个项目
black backend/

# 检查格式（不修改）
black --check backend/
```

### 类型注解

推荐使用类型注解：

```python
from typing import List, Dict, Optional

def generate_tests(
    file_path: str,
    language: str = "golang",
    framework: str = "ginkgo"
) -> Dict[str, any]:
    """
    生成测试代码
    
    Args:
        file_path: 源文件路径
        language: 编程语言
        framework: 测试框架
        
    Returns:
        生成结果字典
    """
    pass
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def calculate_test_cases(
    executable_lines: int,
    complexity: int
) -> int:
    """
    计算建议的测试用例数量。
    
    根据可执行代码行数和圈复杂度计算应该生成多少测试用例。
    
    Args:
        executable_lines: 可执行代码行数
        complexity: 圈复杂度
        
    Returns:
        建议的测试用例数量
        
    Raises:
        ValueError: 如果参数为负数
        
    Examples:
        >>> calculate_test_cases(25, 5)
        6
    """
    pass
```

### Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
# 功能
feat: 添加 Ginkgo 混合模式支持

# 修复
fix: 修复导入路径清理bug

# 文档
docs: 更新快速开始指南

# 优化
refactor: 重构测试生成器代码

# 性能
perf: 优化异步修复性能

# 测试
test: 添加单元测试

# 构建
build: 更新依赖版本

# CI/CD
ci: 添加 GitHub Actions 配置
```

---

## 贡献流程

### 1. Fork 项目

在 GitHub 上 Fork 项目到你的账号。

### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 3. 开发

按照代码规范进行开发，确保：

- ✅ 代码通过所有测试
- ✅ 添加必要的单元测试
- ✅ 更新相关文档
- ✅ 代码格式正确

### 4. 测试

```bash
# 运行单元测试
pytest backend/tests/

# 运行特定测试
pytest backend/tests/test_generator.py

# 代码覆盖率
pytest --cov=backend/app backend/tests/
```

### 5. 提交

```bash
git add .
git commit -m "feat: add your feature description"
```

### 6. 推送

```bash
git push origin feature/your-feature-name
```

### 7. 创建 Pull Request

在 GitHub 上创建 Pull Request，描述你的修改内容。

### PR 模板

```markdown
## 描述

简要描述本次 PR 的目的和改动内容。

## 类型

- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 代码优化
- [ ] 性能改进
- [ ] 测试

## 改动内容

- 改动1
- 改动2
- 改动3

## 测试

描述如何测试这些改动。

## 相关 Issue

Closes #issue_number
```

---

## 扩展开发

### 添加新的测试框架

#### 1. 在提示词模板中添加支持

编辑 `backend/app/services/prompt_templates.py`：

```python
@staticmethod
def your_new_framework_test(
    func_name: str,
    func_body: str,
    # ... 其他参数
) -> str:
    """你的新框架提示词"""
    return f"""
    为以下函数生成使用 YourFramework 的测试代码：
    
    函数名: {func_name}
    函数体: {func_body}
    
    要求：
    1. 使用 YourFramework 语法
    2. 覆盖多种场景
    3. ...
    """
```

#### 2. 在测试生成器中添加逻辑

编辑 `backend/app/services/test_generator.py`：

```python
def _build_prompt(self, function_info: Dict) -> str:
    if self.test_framework == "your_framework":
        return self.prompt_templates.your_new_framework_test(
            func_name=function_info['name'],
            func_body=function_info['body'],
            # ...
        )
    # ... 其他框架
```

#### 3. 添加测试

```python
# backend/tests/test_your_framework.py
def test_your_framework_generation():
    generator = TestGenerator(
        language="your_language",
        test_framework="your_framework",
        module_path="your/module"
    )
    
    result = generator.generate_tests_for_file(
        file_path="test_file.ext",
        module_path="your/module",
        package_name="test_package"
    )
    
    assert result is not None
    assert "your_framework_specific_code" in result
```

### 添加新的编程语言

#### 1. 添加代码分析器

创建 `backend/app/services/analyzers/your_language_analyzer.py`：

```python
class YourLanguageAnalyzer:
    def analyze_file(self, file_path: str) -> List[Dict]:
        """
        分析源文件，提取函数信息
        
        Returns:
            函数信息列表
        """
        functions = []
        # 实现你的语言的代码分析逻辑
        return functions
```

#### 2. 集成到测试生成器

编辑 `backend/app/services/test_generator.py`：

```python
from app.services.analyzers.your_language_analyzer import YourLanguageAnalyzer

def __init__(self, language: str, ...):
    if language == "your_language":
        self.analyzer = YourLanguageAnalyzer()
    # ... 其他语言
```

---

## 更新日志

### v1.2.0 (2024-10-27)

**新功能**：
- ✨ 添加集中式提示词管理系统
- ✨ 实现自动清理内部导入功能
- ✨ 支持异步并发测试修复（速度提升 3-5 倍）

**改进**：
- 🔧 优化 Ginkgo 测试生成提示词
- 🔧 改进混合模式性能
- 🔧 增强编译错误防护

**修复**：
- 🐛 修复循环依赖导致的编译错误
- 🐛 修复包名推断不准确问题
- 🐛 修复 vendor 不一致问题

### v1.1.0 (2024-10-15)

**新功能**：
- ✨ 添加智能测试用例数量策略
- ✨ 支持基于代码复杂度的测试生成
- ✨ 实现自动修复失败的测试

**改进**：
- 🔧 优化测试生成速度
- 🔧 改进 AI 提示词质量

**修复**：
- 🐛 修复 markdown 标记清理问题
- 🐛 修复导入路径替换bug

### v1.0.0 (2024-10-01)

**首次发布**：
- 🎉 支持 Golang Ginkgo BDD 测试生成
- 🎉 支持标准 Go test 生成
- 🎉 支持 C++ Google Test 生成
- 🎉 实现混合模式测试生成
- 🎉 支持自动提交和 PR 创建

---

## 📚 相关资源

- **[GitHub 仓库](https://github.com/your-org/aitest-agent)** - 源代码
- **[问题追踪](https://github.com/your-org/aitest-agent/issues)** - 报告 bug
- **[讨论区](https://github.com/your-org/aitest-agent/discussions)** - 提问和讨论
- **[Wiki](https://github.com/your-org/aitest-agent/wiki)** - 更多文档

---

## 🤝 贡献者

感谢所有为 AI Test Agent 做出贡献的开发者！

<!-- 可以添加贡献者列表 -->

---

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。

---

## 🎉 总结

欢迎参与 AI Test Agent 的开发！

✅ **清晰的代码规范** - 保证代码质量  
✅ **完善的开发流程** - 轻松参与贡献  
✅ **详细的文档** - 快速上手  
✅ **活跃的社区** - 获得帮助和支持  

期待您的贡献！🚀

