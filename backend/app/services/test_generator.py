"""AI测试生成服务"""
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger
import openai
import anthropic

from app.config import get_settings
from app.services.test_case_strategy import get_test_case_strategy
from app.services.prompt_templates import get_prompt_templates


class TestGenerator:
    """测试生成器基类"""
    
    def __init__(self, ai_provider: str = "openai", repo_path: str = None):
        self.settings = get_settings()
        self.ai_provider = ai_provider
        self.repo_path = repo_path
        self.module_path = self._detect_module_path() if repo_path else "your-module-path"
        self.prompt_templates = get_prompt_templates()
        
        if ai_provider == "openai":
            self.client = openai.OpenAI(api_key=self.settings.openai_api_key)
            self.model = self.settings.openai_model
        elif ai_provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
            self.model = self.settings.anthropic_model
        elif ai_provider == "baishan":
            # 百山云 AI - 兼容 OpenAI API 格式
            # 处理 API key：去掉 sk- 前缀
            api_key = self.settings.baishan_api_key
            if api_key.startswith("sk-"):
                api_key = api_key[3:]  # 去掉 sk- 前缀
            
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=self.settings.baishan_base_url
            )
            self.model = self.settings.baishan_model
            logger.info(f"✅ 使用百山云 AI - 模型: {self.model}, Base URL: {self.settings.baishan_base_url}")
    
    def _extract_message_content(self, message) -> str:
        """
        提取 AI 响应消息内容
        
        处理不同 AI 提供商的响应格式：
        - OpenAI: message.content
        - 百山云 GLM-4.6: message.reasoning_content (推理模式) 或 message.content
        - Anthropic: message.content (通过不同的API)
        
        Args:
            message: AI 响应消息对象
            
        Returns:
            提取的文本内容
        """
        # 优先使用 content，如果为 None 则尝试 reasoning_content（百山云推理模式）
        content = message.content
        if content is None:
            content = getattr(message, 'reasoning_content', None)
        return content or ""
    
    def _detect_module_path(self) -> str:
        """从 go.mod 检测 Go 模块路径"""
        if not self.repo_path:
            return "your-module-path"
        
        go_mod_path = Path(self.repo_path) / "go.mod"
        if not go_mod_path.exists():
            logger.warning(f"go.mod 不存在: {go_mod_path}")
            return "your-module-path"
        
        try:
            with open(go_mod_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('module '):
                        module_path = line.split('module ')[-1].strip()
                        logger.info(f"✅ 检测到模块路径: {module_path}")
                        return module_path
        except Exception as e:
            logger.warning(f"读取 go.mod 失败: {e}")
        
        return "your-module-path"
    
    def _auto_fix_test_code(self, test_code: str, language: str, test_framework: str = None) -> str:
        """
        自动修复生成的测试代码
        
        修复内容：
        1. 清理 markdown 代码块标记
        2. 替换导入路径占位符
        3. 确保 Ginkgo 测试有测试套件注册
        4. 清理不必要的项目内部导入（避免编译失败）
        
        Args:
            test_code: 原始测试代码
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            修复后的测试代码
        """
        if language != 'golang':
            return test_code
        
        import re
        
        # 1. 彻底清理所有 markdown 代码块标记
        test_code = test_code.strip()
        
        # 移除开头的所有可能的 markdown 标记: ```go, ```golang, ```markdown, ``` 等
        markdown_starts = ['```golang', '```go', '```markdown', '```text', '```']
        for marker in markdown_starts:
            if test_code.startswith(marker):
                # 移除标记和后面的换行符
                test_code = test_code[len(marker):].lstrip('\n\r')
                break
        
        # 移除结尾的 markdown 标记
        if test_code.endswith('```'):
            test_code = test_code.rstrip('`').rstrip()
        
        # 额外检查：移除任何残留的单独一行的 markdown 标记
        lines = test_code.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # 跳过只包含 markdown 标记的行
            if stripped in ['```', '```go', '```golang', '```markdown', '```text']:
                continue
            cleaned_lines.append(line)
        test_code = '\n'.join(cleaned_lines)
        
        # 2. 替换导入路径占位符
        if self.module_path and self.module_path != "your-module-path":
            test_code = re.sub(
                r'"your-module-path(/[^"]*)"',
                f'"{self.module_path}\\1"',
                test_code
            )
        
        # 3. 对于 Ginkgo 测试，确保有测试套件注册
        if test_framework == 'ginkgo':
            has_test_func = re.search(r'func\s+Test\w+\s*\(\s*t\s+\*testing\.T\s*\)', test_code)
            has_run_specs = 'RunSpecs(' in test_code
            
            if not has_test_func and not has_run_specs:
                # 需要添加测试套件注册
                import_match = re.search(r'(import\s*\([^)]+\))', test_code, re.DOTALL)
                if import_match:
                    import_block = import_match.group(1)
                    
                    # 确保导入了 testing
                    if '"testing"' not in import_block:
                        new_import = import_block.rstrip(')') + '\n\t"testing"\n)'
                        test_code = test_code.replace(import_block, new_import)
                    
                    # 添加测试套件注册函数
                    package_match = re.search(r'package\s+(\w+)', test_code)
                    if package_match:
                        package_name = package_match.group(1).replace('_test', '')
                        suite_func = f'\n\nfunc Test{package_name.capitalize()}(t *testing.T) {{\n\tRegisterFailHandler(Fail)\n\tRunSpecs(t, "{package_name.capitalize()} Suite")\n}}\n'
                        
                        # 在第一个 var _ = Describe 之前插入
                        describe_pos = test_code.find('var _ = Describe(')
                        if describe_pos > 0:
                            test_code = test_code[:describe_pos] + suite_func + test_code[describe_pos:]
        
        # 4. 清理不必要的项目内部导入（避免编译失败）
        test_code = self._clean_internal_imports(test_code)
        
        logger.debug("✅ 测试代码自动修复完成")
        return test_code
    
    def _clean_internal_imports(self, test_code: str) -> str:
        """
        清理测试代码中不必要的项目内部导入
        
        对于同包测试（package xxx 而不是 package xxx_test），
        不应该导入项目内部的任何包，因为所有类型和函数都可以直接访问。
        
        Args:
            test_code: 测试代码
            
        Returns:
            清理后的测试代码
        """
        import re
        
        # 检查是否是同包测试
        package_match = re.search(r'package\s+(\w+)', test_code)
        if not package_match:
            return test_code
        
        package_name = package_match.group(1)
        is_in_package_test = not package_name.endswith('_test')
        
        # 注意：外部测试包也需要清理不必要的导入
        # 但要保留被测试包本身的导入（如果有的话）
        # 对于外部测试包，我们也要清理其他不必要的项目内部导入
        
        # 查找 import 块
        import_match = re.search(r'import\s*\((.*?)\)', test_code, re.DOTALL)
        if not import_match:
            # 没有 import 块，无需清理
            return test_code
        
        original_import_block = import_match.group(0)
        import_content = import_match.group(1)
        
        # 解析导入的包
        import_lines = []
        removed_imports = []
        
        for line in import_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是项目内部导入
            # 项目内部导入通常包含模块路径
            if self.module_path and self.module_path != "your-module-path":
                if f'"{self.module_path}' in line:
                    # 这是项目内部的导入
                    # 对于同包测试，应该移除所有项目内部导入
                    # 对于外部测试包，保留被测试包本身的导入（通常不包含 /repo, /service 等子包）
                    if is_in_package_test:
                        # 同包测试：移除所有项目内部导入
                        removed_imports.append(line)
                        logger.info(f"🧹 清理不必要的内部导入（同包测试）: {line}")
                        continue
                    else:
                        # 外部测试包：只移除明显不必要的导入（如 /repo, /mocks 等）
                        if any(pattern in line for pattern in ['/repo"', '/mocks"', '/mock"', '/internal/service']):
                            removed_imports.append(line)
                            logger.info(f"🧹 清理不必要的内部导入（外部测试）: {line}")
                            continue
                        # 保留可能是被测试包的导入
                        logger.debug(f"保留被测试包的导入: {line}")
            
            # 检查是否导入了常见的项目内部包模式
            internal_patterns = [
                r'".*/internal/',  # internal/ 包
                r'".*/pkg/',       # pkg/ 包（如果是同项目的）
                r'".*/api/',       # api/ 包
                r'".*/cmd/',       # cmd/ 包
            ]
            
            is_internal = False
            for pattern in internal_patterns:
                if re.search(pattern, line):
                    # 但是要排除标准库和第三方库
                    if not line.startswith('"') or '/' not in line.strip('"'):
                        continue
                    # 检查是否是第三方库（包含域名）
                    import_path = re.search(r'"([^"]+)"', line)
                    if import_path:
                        path = import_path.group(1)
                        # 如果包含点号，可能是第三方库（如 github.com/...）
                        if '.' not in path.split('/')[0]:
                            # 不包含域名，很可能是项目内部包
                            is_internal = True
                            break
            
            if is_internal:
                removed_imports.append(line)
                logger.info(f"🧹 清理可能导致编译失败的导入: {line}")
                continue
            
            # 保留这个导入
            import_lines.append(line)
        
        if not removed_imports:
            # 没有需要清理的导入
            return test_code
        
        # 重建 import 块
        if import_lines:
            new_import_content = '\n\t' + '\n\t'.join(import_lines) + '\n'
            new_import_block = f'import ({new_import_content})'
        else:
            # 所有导入都被移除了，这不应该发生，保留至少 testing 和 ginkgo/gomega
            new_import_block = '''import (
\t"testing"
\t
\t. "github.com/onsi/ginkgo/v2"
\t. "github.com/onsi/gomega"
)'''
        
        # 替换原来的 import 块
        test_code = test_code.replace(original_import_block, new_import_block)
        
        logger.info(f"✅ 清理完成，移除了 {len(removed_imports)} 个不必要的导入")
        return test_code
    
    def generate_test(
        self,
        function_info: Dict,
        language: str,
        test_framework: str
    ) -> str:
        """生成单个函数的测试代码（已弃用，保留用于兼容）"""
        raise NotImplementedError
    
    def generate_tests_for_file(
        self,
        file_analysis: Dict,
        language: str,
        test_framework: str
    ) -> str:
        """
        为整个源文件生成测试代码（所有函数的测试统一放在一个测试文件中）
        
        Args:
            file_analysis: 文件分析结果（包含所有函数）
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            生成的测试代码
        """
        raise NotImplementedError
    
    def fix_test(
        self,
        original_test: str,
        test_output: str,
        file_analysis: Dict,
        language: str,
        test_framework: str
    ) -> str:
        """
        根据测试失败信息修复测试代码
        
        Args:
            original_test: 原始测试代码
            test_output: 测试执行输出（包含错误信息）
            file_analysis: 文件分析结果
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            修复后的测试代码
        """
        raise NotImplementedError
    
    def validate_syntax(self, test_code: str, temp_file_path: Path = None) -> Dict:
        """
        验证生成的测试代码语法是否正确
        
        Args:
            test_code: 测试代码
            temp_file_path: 临时文件路径（用于语法检查）
            
        Returns:
            验证结果字典: {'valid': bool, 'errors': List[str], 'formatted_code': str}
        """
        raise NotImplementedError
    
    def generate_and_validate(
        self,
        file_analysis: Dict,
        language: str,
        test_framework: str,
        test_dir: Path = None,
        use_hybrid_mode: bool = True,
        max_fix_attempts: int = 3
    ) -> Dict:
        """
        生成测试代码并自动修复语法错误
        
        工作流程：
        1. 生成测试代码
        2. 验证语法
        3. 如果有错误，调用AI修复
        4. 重复2-3直到通过或达到最大尝试次数
        
        Args:
            file_analysis: 文件分析结果
            language: 编程语言
            test_framework: 测试框架
            test_dir: 测试目录
            use_hybrid_mode: 是否使用混合模式
            max_fix_attempts: 最大修复尝试次数
            
        Returns:
            结果字典: {
                'success': bool,
                'test_code': str,
                'attempts': int,
                'validation_errors': List[str]
            }
        """
        source_file = Path(file_analysis.get('file_path', '')).name
        logger.info(f"🔧 开始为 {source_file} 生成并验证测试代码...")
        
        # 第1步：生成测试代码
        try:
            test_code = self.generate_tests_for_file(
                file_analysis,
                language,
                test_framework,
                test_dir=test_dir,
                use_hybrid_mode=use_hybrid_mode
            )
        except Exception as e:
            logger.error(f"❌ 生成测试代码失败: {e}")
            return {
                'success': False,
                'test_code': None,
                'attempts': 0,
                'validation_errors': [f"生成失败: {str(e)}"]
            }
        
        # 第2步：验证并自动修复循环
        for attempt in range(1, max_fix_attempts + 1):
            logger.info(f"🔍 第 {attempt} 次语法验证...")
            
            # 验证语法
            validation_result = self.validate_syntax(test_code)
            
            if validation_result['valid']:
                # 语法正确，使用格式化后的代码
                final_code = validation_result.get('formatted_code', test_code)
                logger.info(f"✅ 语法验证通过! (尝试次数: {attempt})")
                return {
                    'success': True,
                    'test_code': final_code,
                    'attempts': attempt,
                    'validation_errors': []
                }
            
            # 语法有错误
            errors = validation_result.get('errors', [])
            logger.warning(f"⚠️ 发现语法错误 (第 {attempt} 次): {errors}")
            
            # 如果已经是最后一次尝试，不再修复
            if attempt >= max_fix_attempts:
                logger.error(f"❌ 达到最大修复次数 ({max_fix_attempts})，放弃修复")
                return {
                    'success': False,
                    'test_code': test_code,
                    'attempts': attempt,
                    'validation_errors': errors
                }
            
            # 第3步：调用AI修复语法错误
            logger.info(f"🔧 调用 AI 修复语法错误...")
            try:
                test_code = self._fix_syntax_errors(
                    test_code,
                    errors,
                    file_analysis,
                    language,
                    test_framework
                )
                logger.info(f"✅ AI 修复完成，准备下一次验证...")
            except Exception as e:
                logger.error(f"❌ AI 修复失败: {e}")
                return {
                    'success': False,
                    'test_code': test_code,
                    'attempts': attempt,
                    'validation_errors': errors + [f"修复失败: {str(e)}"]
                }
        
        # 不应该到达这里
        return {
            'success': False,
            'test_code': test_code,
            'attempts': max_fix_attempts,
            'validation_errors': ['未知错误']
        }
    
    def _fix_syntax_errors(
        self,
        test_code: str,
        syntax_errors: List[str],
        file_analysis: Dict,
        language: str,
        test_framework: str
    ) -> str:
        """
        调用AI修复语法错误
        
        Args:
            test_code: 有语法错误的测试代码
            syntax_errors: 语法错误列表
            file_analysis: 文件分析结果
            language: 编程语言
            test_framework: 测试框架
            
        Returns:
            修复后的测试代码
        """
        source_file = Path(file_analysis.get('file_path', '')).name
        errors_text = '\n'.join([f"- {err}" for err in syntax_errors])
        
        # 构建源文件函数信息（提供更多上下文）
        functions = file_analysis.get('functions', [])
        source_context = ""
        if functions:
            funcs_summary = []
            for func in functions[:5]:  # 最多显示前5个函数，避免 prompt 过长
                func_name = func.get('name', '')
                func_body = func.get('body', '')
                if func_name and func_body:
                    # 限制函数体长度，避免 prompt 过长
                    if len(func_body) > 500:
                        func_body = func_body[:500] + "\n    // ... 更多代码"
                    funcs_summary.append(f"### {func_name}\n```{language}\n{func_body}\n```")
            
            if funcs_summary:
                source_context = f"\n\n## 源文件上下文（供参考）\n" + "\n\n".join(funcs_summary)
        
        # 构建 Ginkgo 套件要求说明
        ginkgo_suite_requirements = ""
        if test_framework == "ginkgo":
            ginkgo_suite_requirements = """
7. **Ginkgo 套件完整性检查**：
   - 必须包含 `package xxx` 声明（同包测试，不使用 _test 后缀）
   - 必须包含完整的 import 块（testing, ginkgo/v2, gomega）
   - 必须包含 `func TestXxx(t *testing.T)` 套件注册函数
   - 如果原代码缺少以上任何部分，请补充完整的 Ginkgo 套件模板
"""
        
        # 检测是否是文件被截断的问题（EOF 错误）
        is_truncated = any('EOF' in err for err in syntax_errors)
        truncation_hint = ""
        if is_truncated:
            truncation_hint = """
8. **文件被截断问题**：
   - 代码文件在末尾被截断，缺少结束的括号
   - 请特别注意：需要补全所有未闭合的函数、Context、Describe 和最外层的闭包
   - 确保最后有正确数量的 }) 来闭合所有层级的括号
   - 仔细数清楚需要几个右括号来闭合所有的左括号
"""
        
        prompt = f"""以下测试代码存在语法错误，请修复这些错误。

## 原始测试代码
```{language}
{test_code}
```

## 语法错误
{errors_text}

## 源文件
{source_file}{source_context}

## 修复要求
1. 仔细分析每个语法错误
2. 修复所有语法问题（括号匹配、缺少分号、markdown标记等）
3. 保持测试逻辑不变
4. 保持{test_framework}测试框架风格
5. 不要添加额外的解释文字
6. **重要**: 不要在代码中包含任何markdown标记（如 ```go, ```golang, ``` 等）
7. **必须返回完整的代码文件**，包括所有测试用例和正确闭合的括号{ginkgo_suite_requirements}{truncation_hint}

请只返回修复后的完整测试代码，不要包含任何markdown代码块标记或额外解释。
"""
        
        try:
            # 根据文件大小动态调整 max_tokens
            # 文件越大，需要越多的 tokens
            code_lines = len(test_code.split('\n'))
            # DeepSeek API 最大支持 65536 tokens
            max_tokens = 65536
            # if code_lines > 300:
            #     max_tokens = 65536  # 大文件（DeepSeek 最大值）
            # elif code_lines > 150:
            #     max_tokens = 32000   # 中等文件
            # else:
            #     max_tokens = 32000   # 小文件
            
            logger.debug(f"代码行数: {code_lines}, 使用 max_tokens: {max_tokens}")
            
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": f"你是专业的{language}测试工程师，擅长修复测试代码的语法错误。只返回修复后的完整代码，不要任何解释。特别注意：如果代码被截断，必须补全所有缺失的部分，包括所有需要闭合的括号。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,  # 降低温度，更精确
                    max_tokens=max_tokens
                )
                fixed_code = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                fixed_code = response.content[0].text
            
            # 提取代码块并清理markdown标记
            fixed_code = self._extract_code_block(fixed_code)
            
            # 再次应用自动修复（确保markdown标记清理干净）
            fixed_code = self._auto_fix_test_code(fixed_code, language, test_framework)
            
            # 对 Ginkgo 测试，确保包含套件模板
            if test_framework == "ginkgo":
                fixed_code = self._ensure_ginkgo_suite_template(fixed_code, file_analysis)
            
            return fixed_code
            
        except Exception as e:
            logger.error(f"调用AI修复语法错误失败: {e}")
            raise


class GolangTestGenerator(TestGenerator):
    """Golang测试生成器"""
    
    def _ensure_ginkgo_suite_template(self, test_code: str, file_analysis: Dict) -> str:
        """
        确保 Ginkgo 测试代码包含完整的套件模板
        
        检查并补充：
        1. package xxx 声明（同包测试，不使用 _test 后缀）
        2. import 块
        3. func TestXxx(t *testing.T) 套件注册函数
        
        Args:
            test_code: 测试代码
            file_analysis: 文件分析信息
            
        Returns:
            包含完整套件模板的测试代码
        """
        import re
        
        # 检查是否已包含套件注册函数
        has_test_func = bool(re.search(r'func\s+Test\w+\s*\(\s*t\s+\*testing\.T\s*\)', test_code))
        has_package = bool(re.match(r'^\s*package\s+\w+', test_code, re.MULTILINE))
        has_imports = 'import' in test_code and 'ginkgo' in test_code
        
        # 如果都有，直接返回
        if has_test_func and has_package and has_imports:
            logger.debug("✅ Ginkgo 套件模板完整")
            return test_code
        
        logger.warning(f"⚠️ Ginkgo 测试缺少套件模板 (package:{has_package}, import:{has_imports}, TestFunc:{has_test_func})")
        logger.info("🔧 自动补充 Ginkgo 套件模板...")
        
        # 提取测试逻辑（Describe/It 部分）
        # 移除可能存在的不完整的 package/import
        test_logic = test_code
        if has_package:
            # 保留 package 之后的内容
            test_logic = re.sub(r'^.*?package\s+\w+.*?\n', '', test_code, count=1, flags=re.DOTALL)
        if 'import' in test_logic:
            # 移除 import 块
            test_logic = re.sub(r'import\s*\([^)]*\)', '', test_logic, flags=re.DOTALL)
            test_logic = re.sub(r'import\s+"[^"]*"', '', test_logic)
        
        # 移除可能存在的不完整 Test 函数
        test_logic = re.sub(r'func\s+Test\w+[^{]*\{[^}]*\}', '', test_logic, flags=re.DOTALL)
        
        # 清理多余空行
        test_logic = re.sub(r'\n{3,}', '\n\n', test_logic).strip()
        
        # 从文件路径推断包名
        file_path = file_analysis.get('file_path', '')
        package_name = "unknown"
        import_path = self.module_path
        
        if file_path and self.module_path != "your-module-path":
            try:
                if '/internal/' in file_path:
                    package_path = 'internal/' + file_path.split('/internal/')[-1].rsplit('/', 1)[0]
                    import_path = f"{self.module_path}/{package_path}"
                    package_name = package_path.split('/')[-1]
                elif '/pkg/' in file_path:
                    package_path = 'pkg/' + file_path.split('/pkg/')[-1].rsplit('/', 1)[0]
                    import_path = f"{self.module_path}/{package_path}"
                    package_name = package_path.split('/')[-1]
                else:
                    # 从文件名推断
                    base_name = Path(file_path).stem
                    if base_name.endswith('_test'):
                        base_name = base_name[:-5]  # 移除 _test
                    package_name = base_name or "unknown"
            except Exception as e:
                logger.warning(f"无法从路径推断包名: {e}")
                package_name = "unknown"
        
        # 检测测试逻辑中使用的标准库包
        common_imports = []
        if 'context.' in test_logic or 'context.Context' in test_logic:
            common_imports.append('\t"context"')
        if 'time.' in test_logic or 'time.Time' in test_logic:
            common_imports.append('\t"time"')
        if 'errors.' in test_logic or 'errors.New' in test_logic:
            common_imports.append('\t"errors"')
        if 'fmt.' in test_logic or 'fmt.Sprintf' in test_logic or 'fmt.Errorf' in test_logic:
            common_imports.append('\t"fmt"')
        
        # 构建 import 块
        import_block = '"testing"'
        if common_imports:
            imports_str = '\n'.join(common_imports)
            import_block = f'{imports_str}\n\t"testing"'
        
        # 生成完整的套件模板
        complete_code = f"""package {package_name}

import (
\t{import_block}
\t
\t. "github.com/onsi/ginkgo/v2"
\t. "github.com/onsi/gomega"
)

func Test{package_name.capitalize()}(t *testing.T) {{
\tRegisterFailHandler(Fail)
\tRunSpecs(t, "{package_name.capitalize()} Suite")
}}

{test_logic}
"""
        
        logger.info(f"✅ 已补充完整的 Ginkgo 套件模板 (package: {package_name}, imports: {len(common_imports) + 3} 个)")
        return complete_code
    
    def generate_tests_for_file(
        self,
        file_analysis: Dict,
        language: str = "golang",
        test_framework: str = "go_test",
        test_dir: Path = None,
        use_hybrid_mode: bool = True
    ) -> str:
        """
        为Go源文件的所有函数生成测试（统一在一个测试文件中）
        
        Args:
            file_analysis: 文件分析结果
            language: 语言
            test_framework: 测试框架
            test_dir: 测试目录（混合模式需要）
            use_hybrid_mode: 是否使用混合模式（仅对Ginkgo有效）
            
        Returns:
            生成的测试代码
        """
        # 检测文件是否太大，需要分批生成
        if self._should_use_batch_generation(file_analysis):
            logger.info(f"📦 文件较大，使用分批生成模式")
            return self._generate_tests_in_batches(file_analysis, language, test_framework, test_dir)
        
        # 对于 Ginkgo 框架，尝试使用混合模式
        if test_framework == "ginkgo" and use_hybrid_mode:
            try:
                return self._generate_tests_hybrid(file_analysis, test_dir)
            except Exception as e:
                logger.warning(f"混合模式失败，回退到纯AI模式: {e}")
                # 回退到纯AI模式
        
        # 纯AI模式（标准go test或混合模式失败时）
        return self._generate_tests_pure_ai(file_analysis, language, test_framework)
    
    def _should_use_batch_generation(self, file_analysis: Dict) -> bool:
        """
        判断是否需要使用分批生成模式
        
        判断标准：
        1. 函数数量 > 8 个
        2. 总代码行数 > 500 行
        3. 平均复杂度 > 10
        
        Args:
            file_analysis: 文件分析结果
            
        Returns:
            是否需要分批生成
        """
        functions = file_analysis.get('functions', [])
        
        # 标准1: 函数数量
        func_count = len(functions)
        if func_count > 8:
            logger.debug(f"函数数量 {func_count} > 8，建议分批生成")
            return True
        
        # 标准2: 总代码行数
        total_lines = sum(func.get('executable_lines', 0) for func in functions)
        if total_lines > 500:
            logger.debug(f"总代码行数 {total_lines} > 500，建议分批生成")
            return True
        
        # 标准3: 平均复杂度
        if func_count > 0:
            avg_complexity = sum(func.get('complexity', 1) for func in functions) / func_count
            if avg_complexity > 10:
                logger.debug(f"平均复杂度 {avg_complexity:.1f} > 10，建议分批生成")
                return True
        
        return False
    
    def _generate_tests_in_batches(
        self,
        file_analysis: Dict,
        language: str,
        test_framework: str,
        test_dir: Path = None
    ) -> str:
        """
        分批生成测试代码并合并
        
        策略：
        1. 为每个函数单独生成测试
        2. 提取公共部分（package、imports、suite注册）
        3. 合并所有测试用例
        
        Args:
            file_analysis: 文件分析结果
            language: 编程语言
            test_framework: 测试框架
            test_dir: 测试目录
            
        Returns:
            合并后的完整测试代码
        """
        functions = file_analysis.get('functions', [])
        source_file_name = Path(file_analysis.get('file_path', '')).name
        
        logger.info(f"📦 开始分批生成 {len(functions)} 个函数的测试...")
        
        if test_framework == "ginkgo":
            return self._generate_ginkgo_tests_in_batches(file_analysis, test_dir)
        else:
            return self._generate_standard_tests_in_batches(file_analysis, language)
    
    def _generate_standard_tests_in_batches(self, file_analysis: Dict, language: str) -> str:
        """为标准 Go test 框架分批生成测试"""
        functions = file_analysis.get('functions', [])
        source_file_name = Path(file_analysis.get('file_path', '')).name
        package_name = file_analysis.get('package', 'main')
        
        test_functions = []
        failed_count = 0
        
        # 为每个函数单独生成测试
        for i, func in enumerate(functions, 1):
            func_name = func.get('name', 'unknown')
            logger.info(f"  [{i}/{len(functions)}] 生成 {func_name} 的测试...")
            
            try:
                # 为单个函数生成测试
                test_code = self.generate_test(func, language, "go_test")
                
                # 提取测试函数部分（去掉 package 和 import）
                test_func = self._extract_test_function(test_code)
                if test_func:
                    test_functions.append(test_func)
                    logger.info(f"  ✅ {func_name} 测试生成成功")
                else:
                    logger.warning(f"  ⚠️ {func_name} 测试提取失败")
                    failed_count += 1
                    
            except Exception as e:
                logger.warning(f"  ❌ {func_name} 测试生成失败: {e}")
                failed_count += 1
                continue
        
        if not test_functions:
            raise Exception("所有函数的测试生成都失败了")
        
        logger.info(f"✅ 分批生成完成: {len(test_functions)}/{len(functions)} 成功")
        
        # 合并所有测试函数
        test_code = f"""package {package_name}

import (
    "testing"
)

{chr(10).join(test_functions)}
"""
        
        return test_code
    
    def _generate_ginkgo_tests_in_batches(self, file_analysis: Dict, test_dir: Path) -> str:
        """为 Ginkgo 框架分批生成测试"""
        functions = file_analysis.get('functions', [])
        source_file_name = Path(file_analysis.get('file_path', '')).name
        
        # 1. 生成 Ginkgo 套件框架
        suite_code = self._generate_ginkgo_suite_template(file_analysis, test_dir)
        
        test_cases = []
        failed_count = 0
        
        # 2. 为每个函数单独生成测试用例
        for i, func in enumerate(functions, 1):
            func_name = func.get('name', 'unknown')
            logger.info(f"  [{i}/{len(functions)}] 生成 {func_name} 的测试...")
            
            try:
                # 为单个函数生成测试（只要测试逻辑，不要框架）
                # 创建一个只包含单个函数的临时 file_analysis
                single_func_analysis = {
                    **file_analysis,
                    'functions': [func]
                }
                
                test_logic = self._generate_test_logic_only(single_func_analysis)
                
                if test_logic and test_logic.strip():
                    test_cases.append(test_logic)
                    logger.info(f"  ✅ {func_name} 测试生成成功")
                else:
                    logger.warning(f"  ⚠️ {func_name} 测试为空")
                    failed_count += 1
                    
            except Exception as e:
                logger.warning(f"  ❌ {func_name} 测试生成失败: {e}")
                failed_count += 1
                continue
        
        if not test_cases:
            raise Exception("所有函数的测试生成都失败了")
        
        logger.info(f"✅ 分批生成完成: {len(test_cases)}/{len(functions)} 成功")
        
        # 3. 合并套件框架和所有测试用例
        final_code = suite_code + "\n\n" + "\n\n".join(test_cases)
        
        # 4. 检测并添加缺失的导入包
        final_code = self._add_missing_imports(final_code, "\n\n".join(test_cases))
        
        # 5. 自动修复
        final_code = self._auto_fix_test_code(final_code, "golang", "ginkgo")
        
        return final_code
    
    def _extract_test_function(self, test_code: str) -> str:
        """
        从完整测试代码中提取测试函数部分
        
        Args:
            test_code: 完整的测试代码
            
        Returns:
            只包含测试函数的代码
        """
        import re
        
        # 查找 func Test... 开始的部分
        pattern = r'(func\s+Test\w+\s*\([^)]*\)\s*\{.*?(?=\n(?:func\s+Test|\Z)))'
        matches = re.findall(pattern, test_code, re.DOTALL)
        
        if matches:
            return '\n\n'.join(matches)
        
        # 如果没找到，尝试更宽松的匹配
        lines = test_code.split('\n')
        in_test_func = False
        test_lines = []
        
        for line in lines:
            if line.strip().startswith('func Test'):
                in_test_func = True
            
            if in_test_func:
                test_lines.append(line)
        
        if test_lines:
            return '\n'.join(test_lines)
        
        return ""
    
    def _add_missing_imports(self, test_code: str, test_logic: str) -> str:
        """
        检测测试逻辑中使用的标准库包，并添加到 import 块中
        
        Args:
            test_code: 包含 import 块的完整测试代码
            test_logic: 测试逻辑部分
            
        Returns:
            添加了缺失导入的测试代码
        """
        import re
        
        # 检测测试逻辑中使用的常用标准库包
        needed_imports = []
        if 'context.' in test_logic or 'context.Context' in test_logic or 'context.Background' in test_logic:
            needed_imports.append('context')
        if 'time.' in test_logic or 'time.Time' in test_logic or 'time.Now' in test_logic:
            needed_imports.append('time')
        if 'errors.' in test_logic or 'errors.New' in test_logic or 'errors.Is' in test_logic:
            needed_imports.append('errors')
        if 'fmt.' in test_logic or 'fmt.Sprintf' in test_logic or 'fmt.Errorf' in test_logic:
            needed_imports.append('fmt')
        if 'strings.' in test_logic:
            needed_imports.append('strings')
        if 'strconv.' in test_logic:
            needed_imports.append('strconv')
        if 'json.' in test_logic or 'json.Marshal' in test_logic:
            needed_imports.append('encoding/json')
        if 'http.' in test_logic or 'http.Request' in test_logic:
            needed_imports.append('net/http')
        
        if not needed_imports:
            return test_code
        
        # 查找现有的 import 块
        import_match = re.search(r'import\s*\((.*?)\)', test_code, re.DOTALL)
        if not import_match:
            return test_code
        
        current_imports = import_match.group(1)
        
        # 检查哪些导入是缺失的
        missing_imports = []
        for pkg in needed_imports:
            if f'"{pkg}"' not in current_imports:
                missing_imports.append(pkg)
        
        if not missing_imports:
            return test_code
        
        # 在 "testing" 之前添加缺失的标准库导入
        new_imports_lines = [f'\t"{pkg}"' for pkg in missing_imports]
        new_imports_str = '\n'.join(new_imports_lines)
        
        # 替换 import 块
        new_import_block = current_imports.replace(
            '"testing"',
            f'{new_imports_str}\n\t"testing"'
        )
        
        updated_code = test_code.replace(
            import_match.group(0),
            f'import ({new_import_block})'
        )
        
        logger.info(f"✅ 自动添加缺失的导入包: {', '.join(missing_imports)}")
        return updated_code
    
    def _generate_tests_hybrid(
        self,
        file_analysis: Dict,
        test_dir: Path
    ) -> str:
        """
        混合模式生成Ginkgo测试：ginkgo bootstrap + AI生成测试逻辑
        
        优势：
        - 速度快40-50%（框架生成几乎即时）
        - 成本低30-40%（减少AI token消耗）
        - 框架100%正确（官方工具生成）
        """
        source_file_name = Path(file_analysis['file_path']).name
        logger.info(f"🚀 使用混合模式为 {source_file_name} 生成Ginkgo测试")
        
        # 1. 生成Ginkgo测试框架（suite）
        suite_code = self._generate_ginkgo_suite_template(file_analysis, test_dir)
        
        # 2. AI只生成测试逻辑（不包含package、import、suite注册）
        test_logic = self._generate_test_logic_only(file_analysis)
        
        # 3. 合并框架和测试逻辑
        final_code = suite_code + "\n\n" + test_logic
        
        # 4. 检测并添加缺失的导入包
        final_code = self._add_missing_imports(final_code, test_logic)
        
        # 5. 自动修复（主要是替换模块路径）
        final_code = self._auto_fix_test_code(final_code, "golang", "ginkgo")
        
        logger.info(f"✅ 混合模式生成完成: {source_file_name}")
        return final_code
    
    def _generate_tests_pure_ai(
        self,
        file_analysis: Dict,
        language: str,
        test_framework: str
    ) -> str:
        """纯AI模式生成测试（原有逻辑）"""
        prompt = self._build_file_test_prompt(file_analysis, test_framework)
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的Go测试工程师，擅长编写高质量的单元测试。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=65536  # DeepSeek API 最大支持 65536 tokens
                )
                test_code = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=65536,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                test_code = response.content[0].text
            
            # 提取代码块
            test_code = self._extract_code_block(test_code)
            
            # 自动修复生成的测试代码
            test_code = self._auto_fix_test_code(test_code, language, test_framework)
            
            source_file_name = Path(file_analysis['file_path']).name
            logger.info(f"✅ 为文件 {source_file_name} 生成测试成功")
            return test_code
        
        except Exception as e:
            logger.error(f"生成测试失败: {e}")
            raise
    
    def generate_test(
        self,
        function_info: Dict,
        language: str = "golang",
        test_framework: str = "go_test"
    ) -> str:
        """
        为Go函数生成测试（已弃用，保留用于兼容）
        
        Args:
            function_info: 函数信息字典
            language: 语言
            test_framework: 测试框架
            
        Returns:
            生成的测试代码
        """
        prompt = self._build_prompt(function_info, test_framework)
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的Go测试工程师，擅长编写高质量的单元测试。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                test_code = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                test_code = response.content[0].text
            
            # 提取代码块
            test_code = self._extract_code_block(test_code)
            
            # 自动修复生成的测试代码
            test_code = self._auto_fix_test_code(test_code, language, test_framework)
            
            logger.info(f"✅ 为函数 {function_info['name']} 生成测试成功")
            return test_code
        
        except Exception as e:
            logger.error(f"生成测试失败: {e}")
            raise
    
    def _build_prompt(self, function_info: Dict, test_framework: str = "go_test") -> str:
        """构建提示词（使用集中管理的模板）"""
        func_name = function_info['name']
        func_body = function_info.get('body', '')
        params = function_info.get('params', [])
        return_type = function_info.get('return_type', '')
        receiver = function_info.get('receiver', '')
        
        if test_framework == "ginkgo":
            return self._build_ginkgo_prompt(function_info)
        
        # 使用集中管理的提示词模板
        return self.prompt_templates.golang_standard_test(
            func_name=func_name,
            func_body=func_body,
            params=params,
            return_type=return_type,
            receiver=receiver
        )
    
    def _build_ginkgo_prompt(self, function_info: Dict) -> str:
        """构建Ginkgo测试的提示词（使用集中管理的模板）"""
        func_name = function_info['name']
        func_body = function_info.get('body', '')
        params = function_info.get('params', [])
        return_type = function_info.get('return_type', '')
        receiver = function_info.get('receiver', '')
        file_path = function_info.get('file_path', '')
        
        # 从文件路径推断包名
        package_name = self._extract_package_name(file_path)
        
        # 使用集中管理的提示词模板
        return self.prompt_templates.golang_ginkgo_test(
            func_name=func_name,
            func_body=func_body,
            params=params,
            return_type=return_type,
            receiver=receiver,
            module_path=self.module_path,
            package_name=package_name,
            file_path=file_path
        )
    
    def _extract_package_name(self, file_path: str) -> str:
        """从文件路径提取包名"""
        package_name = "main"
        if file_path:
            try:
                # 从文件路径提取包名
                # 例如: /path/to/repo/internal/biz/config.go -> biz
                if '/internal/' in file_path:
                    package_name = file_path.split('/internal/')[-1].split('/')[0]
                elif '/pkg/' in file_path:
                    package_name = file_path.split('/pkg/')[-1].split('/')[0]
                else:
                    # 尝试从路径最后的目录名获取包名
                    parts = file_path.rstrip('/').split('/')
                    for i in range(len(parts) - 1, -1, -1):
                        if parts[i] and not parts[i].endswith('.go'):
                            package_name = parts[i]
                            break
            except:
                package_name = "main"
        return package_name
    
    
    def _build_file_test_prompt(self, file_analysis: Dict, test_framework: str = "go_test") -> str:
        """构建为整个文件生成测试的提示词"""
        file_path = file_analysis.get('file_path', '')
        functions = file_analysis.get('functions', [])
        
        # 构建函数列表信息（包含函数体源代码）
        functions_info = []
        for func in functions:
            func_name = func.get('name', '')
            params = func.get('params', [])
            return_type = func.get('return_type', '')
            receiver = func.get('receiver', '')
            func_body = func.get('body', '')  # 获取函数体源代码
            
            func_signature = f"func {func_name}({', '.join(params)}) {return_type}"
            if receiver:
                func_signature = f"func ({receiver}) {func_name}({', '.join(params)}) {return_type}"
            
            # 包含函数签名和完整的函数体代码
            func_info = f"### {func_signature}\n```go\n{func_body}\n```"
            functions_info.append(func_info)
        
        functions_list = "\n\n".join(functions_info)
        
        if test_framework == "ginkgo":
            return self._build_file_ginkgo_prompt(file_analysis)
        
        # Go标准测试框架
        source_file_name = Path(file_path).name
        prompt = f"""请为以下Go源文件生成完整的单元测试。所有函数的测试都应该在一个测试文件中。

## 源文件信息
文件: {source_file_name}

## 源文件中的函数实现
{functions_list}

## 测试要求
1. 使用Go标准库的testing包
2. 为每个函数生成对应的测试函数（Test{"{函数名}"}）
3. 所有测试函数都放在同一个测试文件中
4. 每个测试函数覆盖以下场景:
   - 正常输入的测试用例
   - 边界条件测试
   - 异常输入测试（如果适用）
5. 使用table-driven test风格（如果适合）
6. 包含清晰的测试用例描述
7. 使用适当的断言

## 示例格式
```go
package xxx

import (
    "testing"
    // 其他必要的导入
)

func TestFunction1(t *testing.T) {{
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

func TestFunction2(t *testing.T) {{
    // 第二个函数的测试...
}}

// 更多测试函数...
```

请只返回完整的测试代码，不要包含额外的解释。确保使用同包测试（package {包名}，不使用 _test 后缀）。
"""
        return prompt
    
    def _build_file_ginkgo_prompt(self, file_analysis: Dict) -> str:
        """构建为整个文件生成Ginkgo测试的提示词"""
        file_path = file_analysis.get('file_path', '')
        functions = file_analysis.get('functions', [])
        
        # 从文件路径推断包名
        package_name = "main"
        if file_path:
            try:
                # 从文件路径提取包名
                if '/internal/' in file_path:
                    package_name = file_path.split('/internal/')[-1].split('/')[0]
                elif '/pkg/' in file_path:
                    package_name = file_path.split('/pkg/')[-1].split('/')[0]
                else:
                    parts = file_path.rstrip('/').split('/')
                    for i in range(len(parts) - 1, -1, -1):
                        if parts[i] and not parts[i].endswith('.go'):
                            package_name = parts[i]
                            break
            except:
                package_name = "main"
        
        # 获取测试用例策略
        strategy_engine = get_test_case_strategy()
        file_strategy = strategy_engine.calculate_for_file(file_analysis)
        
        # 构建函数列表（包含测试用例数量建议和函数体源代码）
        functions_info = []
        for func in functions:
            func_name = func.get('name', '')
            params = func.get('params', [])
            return_type = func.get('return_type', '')
            receiver = func.get('receiver', '')
            func_body = func.get('body', '')  # 获取函数体源代码
            executable_lines = func.get('executable_lines', 0)
            complexity = func.get('complexity', 1)
            
            func_signature = f"func {func_name}({', '.join(params)}) {return_type}"
            if receiver:
                func_signature = f"func ({receiver}) {func_name}({', '.join(params)}) {return_type}"
            
            # 获取该函数的测试用例策略
            func_strategy = file_strategy['function_strategies'].get(func_name, {})
            test_count = func_strategy.get('total_count', 3)
            normal_count = func_strategy.get('normal_cases', 1)
            edge_count = func_strategy.get('edge_cases', 1)
            error_count = func_strategy.get('error_cases', 1)
            
            func_info = {
                'name': func_name,
                'signature': func_signature,
                'body': func_body,  # 保存函数体源代码
                'executable_lines': executable_lines,
                'complexity': complexity,
                'test_count': test_count,
                'normal_count': normal_count,
                'edge_count': edge_count,
                'error_count': error_count
            }
            functions_info.append(func_info)
        
        # 构建详细的函数列表（包含测试要求和完整源代码）
        functions_list = []
        for f in functions_info:
            func_desc = f"### {f['signature']}\n"
            func_desc += f"**代码行数**: {f['executable_lines']}行 | **复杂度**: {f['complexity']} | "
            func_desc += f"**建议测试用例**: {f['test_count']}个 (正常:{f['normal_count']}, 边界:{f['edge_count']}, 异常:{f['error_count']})\n\n"
            func_desc += f"**函数实现**:\n```go\n{f['body']}\n```"
            functions_list.append(func_desc)
        
        functions_list_str = "\n\n".join(functions_list)
        
        source_file_name = Path(file_path).name
        total_test_cases = file_strategy['total_test_cases']
        
        # 从文件名生成测试套件函数名
        # 例如: user_config.go -> TestUserConfig
        # 例如: xdy_ecs_bill.go -> TestXdyEcsBill
        test_func_name = "Test" + "".join([word.capitalize() for word in source_file_name.replace('.go', '').split('_')])
        
        prompt = f"""请为以下Go源文件生成基于Ginkgo/Gomega的BDD风格单元测试框架。所有函数的测试框架都应该在一个测试文件中。

**重要说明：只生成测试框架代码，不要生成具体的测试实现逻辑。每个It块内只包含注释说明。**

## 项目信息
- Go模块路径: {self.module_path}
- 包名: {package_name}
- 源文件: {source_file_name}
- 建议总测试用例数: {total_test_cases}

## 源文件中的函数信息及测试用例要求
以下是每个函数的信息，请为每个函数生成对应的测试框架：

{functions_list_str}

## 核心要求（必须严格遵守）

### 1. 只生成测试框架结构
- **每个 It 块内只包含注释说明**，不包含具体的测试代码
- 使用 `// TODO: 实现测试逻辑` 作为占位符
- 在注释中详细说明测试场景、输入参数、预期输出和测试步骤
- 确保生成的代码能够通过 `go test -v` 编译

### 2. 包声明
**必须使用同包测试（in-package testing）**:
```go
package {package_name}  // ✅ 正确：使用同包名
```

### 3. 导入规则
**只导入这些包**:
```go
import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)
```

**不要导入**:
- ❌ 不要导入项目内部的其他包
- ❌ 不要导入 mock 包
- ❌ 不要导入被测试的包本身

### 4. 测试框架结构要求
1. 使用Ginkgo BDD的Describe/Context/It结构
2. 为每个函数创建一个Describe块
3. BeforeEach 和 AfterEach 中只包含注释说明
4. 严格按照每个函数建议的测试用例数量生成对应数量的 It 块：
   - 正常场景：生成指定数量的It块
   - 边界条件：生成指定数量的It块
   - 异常场景：生成指定数量的It块
5. 每个It块内只包含TODO注释和详细的测试说明

## 测试框架模板（只包含结构和注释）
```go
package {package_name}  // 同包测试

import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

// 测试套件注册函数（基于源文件名，避免冲突）
func {test_func_name}(t *testing.T) {{
    RegisterFailHandler(Fail)
    RunSpecs(t, "{test_func_name} Suite")
}}

var _ = Describe("{source_file_name.replace('.go', '')}", func() {{
    // 可选：共享的测试变量声明
    // var someVar *SomeType
    
    BeforeEach(func() {{
        // TODO: 初始化测试对象
        // 例如: someVar = NewSomeType(...)
    }})
    
    AfterEach(func() {{
        // TODO: 清理工作
    }})
    
    // 为每个函数创建一个Describe块
    Describe("Function1", func() {{
        Context("when 正常场景", func() {{
            It("should 返回预期结果", func() {{
                // TODO: 实现测试逻辑
                //
                // 测试场景说明：
                // - 输入参数: param1 = value1, param2 = value2
                // - 预期输出: 返回值应该是XXX
                //
                // 测试步骤:
                // 1. Arrange: 准备测试数据 (例如: input := "test")
                // 2. Act: 调用被测方法 (例如: result := Function1(input))
                // 3. Assert: 验证结果 (例如: Expect(result).To(Equal(expected)))
            }})
        }})
        
        Context("when 边界条件", func() {{
            It("should 正确处理边界值", func() {{
                // TODO: 实现测试逻辑
                //
                // 测试场景说明：
                // - 输入参数: 零值/空值/最大值等边界情况
                // - 预期输出: 应该如何处理边界值
                //
                // 测试步骤说明...
            }})
        }})
        
        Context("when 异常场景", func() {{
            It("should 返回适当错误", func() {{
                // TODO: 实现测试逻辑
                //
                // 测试场景说明：
                // - 输入参数: 无效输入/错误条件
                // - 预期输出: 应该返回错误
                //
                // 测试步骤说明...
            }})
        }})
    }})
    
    Describe("Function2", func() {{
        Context("when 正常场景", func() {{
            It("should 返回预期结果", func() {{
                // TODO: 实现测试逻辑
                //
                // 测试场景说明...
            }})
        }})
    }})
    
    // 为其他函数生成类似的测试框架...
}})
```

## 输出要求（非常重要）
1. **只返回测试框架代码**，不要返回具体的测试实现
2. 每个 It 块内只包含 `// TODO: 实现测试逻辑` 和详细的注释说明
3. BeforeEach 和 AfterEach 中也只包含注释说明
4. 确保使用 `package {package_name}`（不带 _test）
5. 只导入 testing、ginkgo 和 gomega
6. 不要导入任何项目内部包
7. 测试套件函数名必须为 `{test_func_name}`
8. 确保生成的代码能够通过 `go test -v` 编译（没有语法错误）

请严格按照以上规则生成测试框架代码（只包含结构和注释，不包含具体实现）。
"""
        return prompt
    
    def _generate_ginkgo_suite_template(
        self,
        file_analysis: Dict,
        test_dir: Path
    ) -> str:
        """
        生成Ginkgo测试套件框架
        
        尝试顺序：
        1. 如果已经有suite文件，复用其import和注册部分
        2. 否则手动生成标准模板
        """
        file_path = file_analysis.get('file_path', '')
        
        # 从文件路径推断包路径
        import_path = self.module_path
        package_name = "unknown"
        
        if file_path and self.module_path != "your-module-path":
            try:
                if '/internal/' in file_path:
                    package_path = 'internal/' + file_path.split('/internal/')[-1].rsplit('/', 1)[0]
                    import_path = f"{self.module_path}/{package_path}"
                    package_name = package_path.split('/')[-1]
                elif '/pkg/' in file_path:
                    package_path = 'pkg/' + file_path.split('/pkg/')[-1].rsplit('/', 1)[0]
                    import_path = f"{self.module_path}/{package_path}"
                    package_name = package_path.split('/')[-1]
                else:
                    # 尝试从test_dir提取包名
                    if test_dir:
                        package_name = test_dir.name
            except:
                if test_dir:
                    package_name = test_dir.name
        
        # 从源文件名生成唯一的测试函数名（避免同一包下的测试文件函数名冲突）
        test_func_name = package_name.capitalize()
        suite_name = f"{package_name.capitalize()} Suite"
        
        if file_path:
            # 提取源文件名（去掉.go后缀）
            source_file_name = Path(file_path).stem  # 例如: xdy_ecs_bill
            # 转换为驼峰命名
            test_func_name = self._snake_to_camel(source_file_name)
            suite_name = f"{test_func_name} Suite"
        
        # 生成标准Ginkgo套件模板 (同包测试，不导入项目内部包)
        suite_template = f"""package {package_name}

import (
\t"testing"
\t
\t. "github.com/onsi/ginkgo/v2"
\t. "github.com/onsi/gomega"
)

func Test{test_func_name}(t *testing.T) {{
\tRegisterFailHandler(Fail)
\tRunSpecs(t, "{suite_name}")
}}"""
        
        logger.debug(f"生成Ginkgo套件框架: package={package_name}, test_func=Test{test_func_name}")
        return suite_template
    
    def _snake_to_camel(self, snake_str: str) -> str:
        """
        将下划线命名转换为驼峰命名（首字母大写）
        
        例如:
        - user_config -> UserConfig
        - xdy_ecs_bill -> XdyEcsBill
        - simple -> Simple
        
        Args:
            snake_str: 下划线命名的字符串
            
        Returns:
            驼峰命名的字符串（首字母大写）
        """
        components = snake_str.split('_')
        return ''.join(word.capitalize() for word in components)
    
    def _generate_test_logic_only(self, file_analysis: Dict) -> str:
        """
        AI只生成测试逻辑部分（Describe/Context/It），不包含package、import、suite注册
        
        优势：
        - Prompt更短，生成更快
        - Token消耗减少30-40%
        - AI专注于测试逻辑，质量更高
        """
        file_path = file_analysis.get('file_path', '')
        functions = file_analysis.get('functions', [])
        
        # 获取测试用例策略
        strategy_engine = get_test_case_strategy()
        file_strategy = strategy_engine.calculate_for_file(file_analysis)
        
        # 构建函数列表（包含测试用例数量建议）
        functions_info = []
        for func in functions:
            func_name = func.get('name', '')
            params = func.get('params', [])
            return_type = func.get('return_type', '')
            receiver = func.get('receiver', '')
            executable_lines = func.get('executable_lines', 0)
            complexity = func.get('complexity', 1)
            
            func_signature = f"func {func_name}({', '.join(params)}) {return_type}"
            if receiver:
                func_signature = f"func ({receiver}) {func_name}({', '.join(params)}) {return_type}"
            
            # 获取该函数的测试用例策略
            func_strategy = file_strategy['function_strategies'].get(func_name, {})
            test_count = func_strategy.get('total_count', 3)
            normal_count = func_strategy.get('normal_cases', 1)
            edge_count = func_strategy.get('edge_cases', 1)
            error_count = func_strategy.get('error_cases', 1)
            
            func_desc = f"- {func_signature}\n"
            func_desc += f"  (代码{executable_lines}行, 复杂度{complexity}, 建议{test_count}个测试: 正常{normal_count}+边界{edge_count}+异常{error_count})"
            functions_info.append(func_desc)
        
        functions_list = "\n".join(functions_info)
        source_file_name = Path(file_path).stem
        total_test_cases = file_strategy['total_test_cases']
        
        # 简化的prompt，只要求生成测试框架
        prompt = f"""请为以下Go源文件的函数生成Ginkgo BDD测试框架代码。

**重要说明：只生成测试框架结构，不要生成具体的测试实现。每个It块内只包含注释说明。**

## 源文件
{Path(file_path).name}
建议总测试用例数: {total_test_cases}

## 函数列表及测试用例要求
{functions_list}

## 核心要求
1. **只返回 var _ = Describe(...) 测试框架代码**
2. **不要包含**: package声明、import语句、TestSuite注册函数
3. 为每个函数创建一个 Describe 块
4. 使用 Context/It 组织测试场景
5. **每个 It 块内只包含注释说明**，不包含具体的测试代码
6. 使用 `// TODO: 实现测试逻辑` 作为占位符
7. **严格按照每个函数建议的测试用例数量生成对应数量的 It 块**：
   - 正常场景：生成指定数量的It块
   - 边界条件：生成指定数量的It块
   - 异常场景：生成指定数量的It块
8. 在每个It块的注释中详细说明：测试场景、输入参数、预期输出、测试步骤

## 测试框架模板
```go
var _ = Describe("{source_file_name}", func() {{
\t// 可选：共享测试变量声明
\t// var someVar *SomeType
\t
\tBeforeEach(func() {{
\t\t// TODO: 初始化测试对象
\t\t// 例如: someVar = NewSomeType(...)
\t}})
\t
\tAfterEach(func() {{
\t\t// TODO: 清理工作
\t}})
\t
\tDescribe("Function1", func() {{
\t\tContext("when normal input", func() {{
\t\t\tIt("should return expected result", func() {{
\t\t\t\t// TODO: 实现测试逻辑
\t\t\t\t//
\t\t\t\t// 测试场景说明：
\t\t\t\t// - 输入参数: param = value
\t\t\t\t// - 预期输出: 返回XXX
\t\t\t\t//
\t\t\t\t// 测试步骤:
\t\t\t\t// 1. Arrange: 准备测试数据
\t\t\t\t// 2. Act: 调用被测方法
\t\t\t\t// 3. Assert: 验证结果
\t\t\t}})
\t\t}})
\t\t
\t\tContext("when edge case", func() {{
\t\t\tIt("should handle correctly", func() {{
\t\t\t\t// TODO: 实现测试逻辑
\t\t\t\t//
\t\t\t\t// 测试场景说明...
\t\t\t}})
\t\t}})
\t}})
\t
\tDescribe("Function2", func() {{
\t\t// 为第二个函数生成类似的测试框架...
\t}})
}})
```

只返回测试框架代码（只包含结构和注释，不包含具体实现），不要任何解释或额外内容。
"""
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是Ginkgo BDD测试专家。只生成测试框架代码，不要生成具体的测试实现。每个It块内只包含TODO注释和详细的测试说明。只返回代码，不要解释。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=3000  # 测试框架比完整实现更简短
                )
                test_logic = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=3000,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                test_logic = response.content[0].text
            
            # 提取代码块
            test_logic = self._extract_code_block(test_logic)
            
            logger.debug(f"✅ AI生成测试逻辑完成: {len(test_logic)} 字符")
            return test_logic
        
        except Exception as e:
            logger.error(f"AI生成测试逻辑失败: {e}")
            raise
    
    def fix_test(
        self,
        original_test: str,
        test_output: str,
        file_analysis: Dict,
        language: str = "golang",
        test_framework: str = "go_test"
    ) -> str:
        """
        根据测试失败信息修复Golang测试代码
        
        Args:
            original_test: 原始测试代码
            test_output: 测试失败输出
            file_analysis: 文件分析结果
            language: 语言
            test_framework: 测试框架
            
        Returns:
            修复后的测试代码
        """
        prompt = self._build_fix_prompt(
            original_test, 
            test_output, 
            file_analysis, 
            test_framework
        )
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的Go测试工程师，擅长分析测试失败原因并修复测试代码。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2500
                )
                fixed_test = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2500,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                fixed_test = response.content[0].text
            
            # 提取代码块
            fixed_test = self._extract_code_block(fixed_test)
            
            source_file = Path(file_analysis.get('file_path', '')).name
            logger.info(f"✅ 测试修复成功: {source_file}")
            return fixed_test
        
        except Exception as e:
            logger.error(f"测试修复失败: {e}")
            raise
    
    def _build_fix_prompt(
        self, 
        original_test: str, 
        test_output: str, 
        file_analysis: Dict,
        test_framework: str = "go_test"
    ) -> str:
        """构建测试修复提示词"""
        source_file = Path(file_analysis.get('file_path', '')).name
        
        prompt = f"""以下Go测试代码执行失败，请分析失败原因并修复测试代码。

## 原始测试代码
```go
{original_test}
```

## 测试失败输出
```
{test_output}
```

## 测试目标
源文件: {source_file}

## 修复要求
1. 仔细分析测试失败的原因（断言错误、逻辑错误、边界条件等）
2. 修复测试代码中的问题：
   - 如果是断言错误，修正期望值
   - 如果是测试逻辑错误，调整测试逻辑
   - 如果是边界条件问题，添加或修改测试用例
   - 如果是导入缺失，添加必要的导入
3. 保持测试框架风格（{"Ginkgo/Gomega" if test_framework == "ginkgo" else "标准testing包"}）
4. 确保修复后的测试能够通过
5. 保持代码清晰和良好的测试覆盖

## 注意事项
- 不要修改被测试函数的行为预期
- 如果原测试的断言值错误，根据函数实际行为修正
- 保持原有的测试结构和风格
- 添加必要的错误处理

请只返回修复后的完整测试代码，不要包含额外的解释。
"""
        return prompt
    
    def _extract_code_block(self, text: str) -> str:
        """从AI响应中提取代码块，清除所有markdown标识"""
        import re
        
        # 处理带语言标识的代码块: ```go, ```golang, ```markdown 等
        # 匹配模式: ```<language>\n<code>\n```
        pattern = r'```(?:go|golang|markdown|text)?\s*\n(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 处理简单的代码块标记（没有语言标识）
        if '```' in text:
            # 找到第一个```后的内容
            start_idx = text.find('```')
            remaining = text[start_idx + 3:]
            
            # 跳过第一行的语言标识（如果有）
            first_newline = remaining.find('\n')
            if first_newline != -1:
                remaining = remaining[first_newline + 1:]
            
            # 找到结束的```
            end_idx = remaining.find('```')
            if end_idx != -1:
                return remaining[:end_idx].strip()
        
        # 如果没有代码块标记，返回整个文本
        return text.strip()
    
    def validate_syntax(self, test_code: str, temp_file_path: Path = None) -> Dict:
        """
        验证Go测试代码语法是否正确
        
        使用 gofmt 来验证语法（gofmt 会在语法错误时返回非零退出码）
        
        Args:
            test_code: Go测试代码
            temp_file_path: 临时文件路径
            
        Returns:
            验证结果: {'valid': bool, 'errors': List[str], 'formatted_code': str}
        """
        import subprocess
        import tempfile
        
        # 如果没有提供临时文件路径，创建一个
        if temp_file_path is None:
            with tempfile.NamedTemporaryFile(mode='w', suffix='_test.go', delete=False) as f:
                f.write(test_code)
                temp_file_path = Path(f.name)
        else:
            # 写入测试代码到临时文件
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
        
        errors = []
        formatted_code = test_code
        
        try:
            # 使用 gofmt 验证语法并格式化
            result = subprocess.run(
                ['gofmt', '-e', str(temp_file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # gofmt 返回非零表示有语法错误
                errors.append(f"语法错误: {result.stderr}")
                logger.warning(f"❌ Go语法校验失败:\n{result.stderr}")
                return {'valid': False, 'errors': errors, 'formatted_code': test_code}
            
            # 如果有输出，说明代码可以被格式化（语法正确）
            if result.stdout:
                formatted_code = result.stdout
                logger.debug("✅ Go语法校验通过，代码已格式化")
            
            return {'valid': True, 'errors': [], 'formatted_code': formatted_code}
            
        except subprocess.TimeoutExpired:
            errors.append("语法检查超时")
            logger.warning("❌ Go语法校验超时")
            return {'valid': False, 'errors': errors, 'formatted_code': test_code}
        
        except FileNotFoundError:
            # gofmt 未安装，跳过语法检查
            logger.warning("⚠️ gofmt 未安装，跳过语法检查")
            return {'valid': True, 'errors': [], 'formatted_code': test_code}
        
        except Exception as e:
            errors.append(f"语法检查异常: {str(e)}")
            logger.error(f"❌ Go语法校验异常: {e}")
            return {'valid': False, 'errors': errors, 'formatted_code': test_code}
        
        finally:
            # 清理临时文件
            try:
                if temp_file_path and temp_file_path.exists():
                    temp_file_path.unlink()
            except:
                pass


class CppTestGenerator(TestGenerator):
    """C++测试生成器"""
    
    def generate_tests_for_file(
        self,
        file_analysis: Dict,
        language: str = "cpp",
        test_framework: str = "google_test",
        test_dir: Path = None,
        use_hybrid_mode: bool = False
    ) -> str:
        """
        为C++源文件的所有函数生成测试（支持智能测试用例策略）
        
        新功能：
        - 使用智能测试用例策略根据代码复杂度决定测试数量
        - 自动分配正常/边界/异常场景测试用例
        """
        functions = file_analysis.get('functions', [])
        
        if not functions:
            raise Exception("没有找到可测试的函数")
        
        # 获取智能测试用例策略
        from .test_case_strategy import get_test_case_strategy
        strategy_engine = get_test_case_strategy()
        file_strategy = strategy_engine.calculate_for_file(file_analysis)
        
        # 记录测试策略
        logger.info(f"📊 C++ 文件测试策略:")
        logger.info(f"   总测试用例: {file_strategy['total_test_cases']} 个")
        logger.info(f"   函数数量: {len(functions)} 个")
        
        # 为每个函数生成测试（带智能策略）
        test_codes = []
        for function in functions:
            try:
                func_name = function.get('name', 'unknown')
                func_strategy = file_strategy['function_strategies'].get(func_name, {})
                
                # 记录该函数的测试策略
                if func_strategy:
                    logger.info(f"   {func_name}: {func_strategy.get('total_count', 3)} 个测试用例 "
                               f"(正常:{func_strategy.get('normal_cases', 1)}, "
                               f"边界:{func_strategy.get('edge_cases', 1)}, "
                               f"异常:{func_strategy.get('error_cases', 1)})")
                
                test_code = self.generate_test(function, language, test_framework, func_strategy)
                test_codes.append(test_code)
            except Exception as e:
                logger.warning(f"为函数 {function.get('name', 'unknown')} 生成测试失败: {e}")
        
        if not test_codes:
            raise Exception("没有成功生成任何测试代码")
        
        # 合并所有测试代码
        return self._merge_test_codes(test_codes, file_analysis, test_framework)
    
    def _merge_test_codes(self, test_codes: List[str], file_analysis: Dict, test_framework: str) -> str:
        """
        智能合并多个测试代码
        
        Args:
            test_codes: 各个函数的测试代码列表
            file_analysis: 文件分析信息
            test_framework: 测试框架
            
        Returns:
            合并后的完整测试文件
        """
        if not test_codes:
            return ""
        
        # 提取文件路径信息
        file_path = file_analysis.get('file_path', '')
        source_file = Path(file_path).stem if file_path else 'test'
        
        # 构建头部（includes 和 using）
        if test_framework == "google_test":
            header = f"""#include <gtest/gtest.h>
#include "{source_file}.h"

// 自动生成的 Google Test 单元测试
// 使用智能测试用例策略，根据代码复杂度优化测试覆盖

"""
        else:  # catch2
            header = f"""#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>
#include "{source_file}.h"

"""
        
        # 合并所有测试代码（去除重复的头部）
        merged_tests = []
        for test_code in test_codes:
            # 移除单个测试中的 #include 重复声明
            cleaned = test_code
            if '#include' in cleaned:
                lines = cleaned.split('\n')
                cleaned = '\n'.join([line for line in lines if not line.strip().startswith('#include')])
            merged_tests.append(cleaned.strip())
        
        return header + '\n\n'.join(merged_tests)
    
    def generate_test(
        self,
        function_info: Dict,
        language: str = "cpp",
        test_framework: str = "google_test",
        test_strategy: Dict = None
    ) -> str:
        """
        为C++函数生成测试（支持智能测试用例策略）
        
        Args:
            function_info: 函数信息
            language: 语言
            test_framework: 测试框架
            test_strategy: 智能测试用例策略（包含 total_count, normal_cases, edge_cases, error_cases）
        """
        prompt = self._build_prompt(function_info, test_framework, test_strategy)
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的C++测试工程师，擅长使用Google Test编写单元测试。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                test_code = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                test_code = response.content[0].text
            
            test_code = self._extract_code_block(test_code)
            
            logger.info(f"✅ 为函数 {function_info['name']} 生成测试成功")
            return test_code
        
        except Exception as e:
            logger.error(f"生成测试失败: {e}")
            raise
    
    def fix_test(
        self,
        original_test: str,
        test_output: str,
        file_analysis: Dict,
        language: str = "cpp",
        test_framework: str = "google_test"
    ) -> str:
        """根据测试失败信息修复C++测试代码"""
        source_file = Path(file_analysis.get('file_path', '')).name
        
        prompt = f"""以下C++测试代码执行失败，请分析失败原因并修复。

## 原始测试代码
```cpp
{original_test}
```

## 测试失败输出
```
{test_output}
```

## 测试目标
源文件: {source_file}

## 修复要求
1. 分析失败原因（断言错误、内存问题、逻辑错误等）
2. 修复测试代码中的问题
3. 保持{test_framework}测试框架风格
4. 确保修复后的测试能够通过

请只返回修复后的完整测试代码。
"""
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的C++测试工程师，擅长分析和修复测试代码。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2500
                )
                fixed_test = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2500,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                fixed_test = response.content[0].text
            
            fixed_test = self._extract_code_block(fixed_test)
            source_file = Path(file_analysis.get('file_path', '')).name
            logger.info(f"✅ C++测试修复成功: {source_file}")
            return fixed_test
        
        except Exception as e:
            logger.error(f"C++测试修复失败: {e}")
            raise
    
    def _build_prompt(self, function_info: Dict, test_framework: str, test_strategy: Dict = None) -> str:
        """
        构建智能测试提示词（使用增强的 Prompt 模板）
        
        Args:
            function_info: 函数信息
            test_framework: 测试框架
            test_strategy: 智能测试用例策略
        """
        from .prompt_templates import PromptTemplates
        
        func_name = function_info.get('name', 'unknown')
        func_body = function_info.get('body', '')
        params = function_info.get('params', [])
        return_type = function_info.get('return_type', 'void')
        
        # 如果有测试策略，使用增强的 prompt
        if test_strategy:
            return PromptTemplates.cpp_google_test_with_strategy(
                func_name=func_name,
                func_body=func_body,
                params=params,
                return_type=return_type,
                test_framework=test_framework,
                total_tests=test_strategy.get('total_count', 3),
                normal_cases=test_strategy.get('normal_cases', 1),
                edge_cases=test_strategy.get('edge_cases', 1),
                error_cases=test_strategy.get('error_cases', 1),
                executable_lines=function_info.get('executable_lines', 0),
                complexity=function_info.get('complexity', 1)
            )
        else:
            # 回退到简单 prompt
            return PromptTemplates.cpp_google_test(func_name, func_body)
    
    def _extract_code_block(self, text: str) -> str:
        """从AI响应中提取代码块，清除所有markdown标识"""
        import re
        
        # 处理带语言标识的代码块: ```cpp, ```c++, ```markdown 等
        # 匹配模式: ```<language>\n<code>\n```
        pattern = r'```(?:cpp|c\+\+|markdown|text)?\s*\n(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 处理简单的代码块标记（没有语言标识）
        if '```' in text:
            # 找到第一个```后的内容
            start_idx = text.find('```')
            remaining = text[start_idx + 3:]
            
            # 跳过第一行的语言标识（如果有）
            first_newline = remaining.find('\n')
            if first_newline != -1:
                remaining = remaining[first_newline + 1:]
            
            # 找到结束的```
            end_idx = remaining.find('```')
            if end_idx != -1:
                return remaining[:end_idx].strip()
        
        # 如果没有代码块标记，返回整个文本
        return text.strip()
    
    def validate_syntax(self, test_code: str, temp_file_path: Path = None) -> Dict:
        """
        验证C++测试代码语法（简化版）
        
        注意：完整的C++语法检查需要编译环境，这里只做基础检查
        
        Args:
            test_code: C++测试代码
            temp_file_path: 临时文件路径
            
        Returns:
            验证结果: {'valid': bool, 'errors': List[str], 'formatted_code': str}
        """
        errors = []
        
        # 基础语法检查：括号匹配、基本结构
        if test_code.count('{') != test_code.count('}'):
            errors.append("语法错误: 大括号不匹配")
        
        if test_code.count('(') != test_code.count(')'):
            errors.append("语法错误: 小括号不匹配")
        
        # 检查是否包含必要的测试框架头文件
        if '#include' not in test_code:
            errors.append("警告: 缺少 #include 头文件")
        
        if errors:
            logger.warning(f"❌ C++语法校验失败: {errors}")
            return {'valid': False, 'errors': errors, 'formatted_code': test_code}
        
        logger.debug("✅ C++基础语法校验通过")
        return {'valid': True, 'errors': [], 'formatted_code': test_code}


class CTestGenerator(TestGenerator):
    """C测试生成器"""
    
    def generate_tests_for_file(
        self,
        file_analysis: Dict,
        language: str = "c",
        test_framework: str = "cunit",
        test_dir: Path = None,
        use_hybrid_mode: bool = False
    ) -> str:
        """
        为C源文件的所有函数生成测试（支持智能测试用例策略）
        
        新功能：
        - 使用智能测试用例策略根据代码复杂度决定测试数量
        - 自动分配正常/边界/异常场景测试用例
        """
        functions = file_analysis.get('functions', [])
        
        if not functions:
            raise Exception("没有找到可测试的函数")
        
        # 获取智能测试用例策略
        from .test_case_strategy import get_test_case_strategy
        strategy_engine = get_test_case_strategy()
        file_strategy = strategy_engine.calculate_for_file(file_analysis)
        
        # 记录测试策略
        logger.info(f"📊 C 文件测试策略:")
        logger.info(f"   总测试用例: {file_strategy['total_test_cases']} 个")
        logger.info(f"   函数数量: {len(functions)} 个")
        
        # 为每个函数生成测试（带智能策略）
        test_codes = []
        for function in functions:
            try:
                func_name = function.get('name', 'unknown')
                func_strategy = file_strategy['function_strategies'].get(func_name, {})
                
                # 记录该函数的测试策略
                if func_strategy:
                    logger.info(f"   {func_name}: {func_strategy.get('total_count', 3)} 个测试用例 "
                               f"(正常:{func_strategy.get('normal_cases', 1)}, "
                               f"边界:{func_strategy.get('edge_cases', 1)}, "
                               f"异常:{func_strategy.get('error_cases', 1)})")
                
                test_code = self.generate_test(function, language, test_framework, func_strategy)
                test_codes.append(test_code)
            except Exception as e:
                logger.warning(f"为函数 {function.get('name', 'unknown')} 生成测试失败: {e}")
        
        if not test_codes:
            raise Exception("没有成功生成任何测试代码")
        
        # 合并所有测试代码
        return self._merge_test_codes(test_codes, file_analysis, test_framework)
    
    def _merge_test_codes(self, test_codes: List[str], file_analysis: Dict, test_framework: str) -> str:
        """
        智能合并多个 C 测试代码
        
        Args:
            test_codes: 各个函数的测试代码列表
            file_analysis: 文件分析信息
            test_framework: 测试框架
            
        Returns:
            合并后的完整测试文件
        """
        if not test_codes:
            return ""
        
        # 提取文件路径信息
        file_path = file_analysis.get('file_path', '')
        source_file = Path(file_path).stem if file_path else 'test'
        
        # 构建头部
        if test_framework == "cunit":
            header = f"""#include <CUnit/CUnit.h>
#include <CUnit/Basic.h>
#include "{source_file}.h"

// 自动生成的 CUnit 单元测试
// 使用智能测试用例策略，根据代码复杂度优化测试覆盖

"""
        else:  # unity
            header = f"""#include "unity.h"
#include "{source_file}.h"

// 自动生成的 Unity 单元测试

"""
        
        # 合并所有测试代码
        merged_tests = []
        for test_code in test_codes:
            cleaned = test_code
            if '#include' in cleaned:
                lines = cleaned.split('\n')
                cleaned = '\n'.join([line for line in lines if not line.strip().startswith('#include')])
            merged_tests.append(cleaned.strip())
        
        return header + '\n\n'.join(merged_tests)
    
    def generate_test(
        self,
        function_info: Dict,
        language: str = "c",
        test_framework: str = "cunit",
        test_strategy: Dict = None
    ) -> str:
        """
        为C函数生成测试（支持智能测试用例策略）
        
        Args:
            function_info: 函数信息
            language: 语言
            test_framework: 测试框架
            test_strategy: 智能测试用例策略
        """
        prompt = self._build_prompt(function_info, test_framework, test_strategy)
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的C语言测试工程师，擅长编写单元测试。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                test_code = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                test_code = response.content[0].text
            
            test_code = self._extract_code_block(test_code)
            
            logger.info(f"✅ 为函数 {function_info['name']} 生成测试成功")
            return test_code
        
        except Exception as e:
            logger.error(f"生成测试失败: {e}")
            raise
    
    def fix_test(
        self,
        original_test: str,
        test_output: str,
        file_analysis: Dict,
        language: str = "c",
        test_framework: str = "cunit"
    ) -> str:
        """根据测试失败信息修复C测试代码"""
        source_file = Path(file_analysis.get('file_path', '')).name
        
        prompt = f"""以下C语言测试代码执行失败，请分析失败原因并修复。

## 原始测试代码
```c
{original_test}
```

## 测试失败输出
```
{test_output}
```

## 测试目标
源文件: {source_file}

## 修复要求
1. 分析失败原因（断言错误、内存问题、指针问题等）
2. 修复测试代码中的问题
3. 保持{test_framework}测试框架风格
4. 确保修复后的测试能够通过

请只返回修复后的完整测试代码。
"""
        
        try:
            if self.ai_provider in ["openai", "baishan"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的C语言测试工程师，擅长分析和修复测试代码。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2500
                )
                fixed_test = self._extract_message_content(response.choices[0].message)
            
            elif self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2500,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                fixed_test = response.content[0].text
            
            fixed_test = self._extract_code_block(fixed_test)
            source_file = Path(file_analysis.get('file_path', '')).name
            logger.info(f"✅ C测试修复成功: {source_file}")
            return fixed_test
        
        except Exception as e:
            logger.error(f"C测试修复失败: {e}")
            raise
    
    def _build_prompt(self, function_info: Dict, test_framework: str, test_strategy: Dict = None) -> str:
        """
        构建智能测试提示词（使用增强的 Prompt 模板）
        
        Args:
            function_info: 函数信息
            test_framework: 测试框架
            test_strategy: 智能测试用例策略
        """
        from .prompt_templates import PromptTemplates
        
        func_name = function_info.get('name', 'unknown')
        func_body = function_info.get('body', '')
        params = function_info.get('params', [])
        return_type = function_info.get('return_type', 'void')
        
        # 如果有测试策略，使用增强的 prompt
        if test_strategy:
            return PromptTemplates.c_unit_test_with_strategy(
                func_name=func_name,
                func_body=func_body,
                params=params,
                return_type=return_type,
                test_framework=test_framework,
                total_tests=test_strategy.get('total_count', 3),
                normal_cases=test_strategy.get('normal_cases', 1),
                edge_cases=test_strategy.get('edge_cases', 1),
                error_cases=test_strategy.get('error_cases', 1),
                executable_lines=function_info.get('executable_lines', 0),
                complexity=function_info.get('complexity', 1)
            )
        else:
            # 回退到简单 prompt
            return PromptTemplates.c_unit_test(func_name, func_body, test_framework)
    
    def _extract_code_block(self, text: str) -> str:
        """从AI响应中提取代码块，清除所有markdown标识"""
        import re
        
        # 处理带语言标识的代码块: ```c, ```markdown 等
        # 匹配模式: ```<language>\n<code>\n```
        pattern = r'```(?:c|markdown|text)?\s*\n(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 处理简单的代码块标记（没有语言标识）
        if '```' in text:
            # 找到第一个```后的内容
            start_idx = text.find('```')
            remaining = text[start_idx + 3:]
            
            # 跳过第一行的语言标识（如果有）
            first_newline = remaining.find('\n')
            if first_newline != -1:
                remaining = remaining[first_newline + 1:]
            
            # 找到结束的```
            end_idx = remaining.find('```')
            if end_idx != -1:
                return remaining[:end_idx].strip()
        
        # 如果没有代码块标记，返回整个文本
        return text.strip()
    
    def validate_syntax(self, test_code: str, temp_file_path: Path = None) -> Dict:
        """
        验证C测试代码语法（简化版）
        
        注意：完整的C语法检查需要编译环境，这里只做基础检查
        
        Args:
            test_code: C测试代码
            temp_file_path: 临时文件路径
            
        Returns:
            验证结果: {'valid': bool, 'errors': List[str], 'formatted_code': str}
        """
        errors = []
        
        # 基础语法检查：括号匹配、基本结构
        if test_code.count('{') != test_code.count('}'):
            errors.append("语法错误: 大括号不匹配")
        
        if test_code.count('(') != test_code.count(')'):
            errors.append("语法错误: 小括号不匹配")
        
        # 检查是否包含必要的头文件
        if '#include' not in test_code:
            errors.append("警告: 缺少 #include 头文件")
        
        if errors:
            logger.warning(f"❌ C语法校验失败: {errors}")
            return {'valid': False, 'errors': errors, 'formatted_code': test_code}
        
        logger.debug("✅ C基础语法校验通过")
        return {'valid': True, 'errors': [], 'formatted_code': test_code}


def get_test_generator(language: str, ai_provider: str = "openai", repo_path: str = None) -> TestGenerator:
    """工厂函数：获取对应语言的测试生成器"""
    generators = {
        'golang': GolangTestGenerator,
        'cpp': CppTestGenerator,
        'c': CTestGenerator
    }
    
    generator_class = generators.get(language)
    if not generator_class:
        raise ValueError(f"不支持的语言: {language}")
    
    return generator_class(ai_provider, repo_path)

