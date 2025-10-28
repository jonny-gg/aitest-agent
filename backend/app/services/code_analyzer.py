"""代码分析服务"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
import tree_sitter_languages
from tree_sitter import Language, Parser


class CodeAnalyzer:
    """代码分析器基类"""
    
    def __init__(self, language: str):
        self.language = language
        self.parser = Parser()
    
    def analyze_file(self, file_path: str) -> Dict:
        """分析单个文件"""
        raise NotImplementedError
    
    def analyze_directory(self, dir_path: str) -> List[Dict]:
        """分析整个目录"""
        raise NotImplementedError


class GolangAnalyzer(CodeAnalyzer):
    """Golang代码分析器"""
    
    def __init__(self):
        super().__init__("golang")
        # 使用tree-sitter-languages库
        language = tree_sitter_languages.get_language('go')
        self.parser.set_language(language)
    
    def analyze_file(self, file_path: str) -> Dict:
        """
        分析Go文件
        
        Returns:
            {
                'file_path': str,
                'functions': List[Dict],
                'structs': List[Dict],
                'interfaces': List[Dict]
            }
        """
        try:
            with open(file_path, 'rb') as f:
                code = f.read()
            
            tree = self.parser.parse(code)
            root_node = tree.root_node
            
            functions = []
            structs = []
            interfaces = []
            
            # 遍历AST节点
            for node in root_node.children:
                if node.type == 'function_declaration':
                    func_info = self._extract_function(node, code)
                    functions.append(func_info)
                elif node.type == 'method_declaration':
                    method_info = self._extract_method(node, code)
                    functions.append(method_info)
                elif node.type == 'type_declaration':
                    # 可能是struct或interface
                    type_info = self._extract_type(node, code)
                    if type_info['kind'] == 'struct':
                        structs.append(type_info)
                    elif type_info['kind'] == 'interface':
                        interfaces.append(type_info)
            
            return {
                'file_path': file_path,
                'package': self._extract_package(root_node, code),
                'functions': functions,
                'structs': structs,
                'interfaces': interfaces
            }
        
        except Exception as e:
            logger.error(f"分析Go文件失败 {file_path}: {e}")
            return {
                'file_path': file_path,
                'functions': [],
                'structs': [],
                'interfaces': []
            }
    
    def _extract_package(self, root_node, code: bytes) -> str:
        """提取package名称"""
        for node in root_node.children:
            if node.type == 'package_clause':
                package_name = node.child_by_field_name('name')
                if package_name:
                    return code[package_name.start_byte:package_name.end_byte].decode()
        return ""
    
    def _extract_function(self, node, code: bytes) -> Dict:
        """提取函数信息"""
        name_node = node.child_by_field_name('name')
        name = code[name_node.start_byte:name_node.end_byte].decode() if name_node else ""
        
        params = []
        params_node = node.child_by_field_name('parameters')
        if params_node:
            for param in params_node.children:
                if param.type == 'parameter_declaration':
                    params.append(code[param.start_byte:param.end_byte].decode())
        
        return_type = ""
        result_node = node.child_by_field_name('result')
        if result_node:
            return_type = code[result_node.start_byte:result_node.end_byte].decode()
        
        body_node = node.child_by_field_name('body')
        body = code[body_node.start_byte:body_node.end_byte].decode() if body_node else ""
        
        return {
            'name': name,
            'type': 'function',
            'params': params,
            'return_type': return_type,
            'body': body,
            'start_line': node.start_point[0],
            'end_line': node.end_point[0],
            'complexity': self._calculate_complexity(body),
            'executable_lines': self._count_executable_lines(body)
        }
    
    def _extract_method(self, node, code: bytes) -> Dict:
        """提取方法信息"""
        func_info = self._extract_function(node, code)
        func_info['type'] = 'method'
        
        # 提取接收者
        receiver_node = node.child_by_field_name('receiver')
        if receiver_node:
            func_info['receiver'] = code[receiver_node.start_byte:receiver_node.end_byte].decode()
        
        return func_info
    
    def _extract_type(self, node, code: bytes) -> Dict:
        """提取类型定义（struct/interface）"""
        spec_node = node.child_by_field_name('spec')
        if not spec_node:
            return {'kind': 'unknown'}
        
        name_node = spec_node.child_by_field_name('name')
        name = code[name_node.start_byte:name_node.end_byte].decode() if name_node else ""
        
        type_node = spec_node.child_by_field_name('type')
        if not type_node:
            return {'kind': 'unknown'}
        
        if type_node.type == 'struct_type':
            return {
                'kind': 'struct',
                'name': name,
                'fields': self._extract_struct_fields(type_node, code)
            }
        elif type_node.type == 'interface_type':
            return {
                'kind': 'interface',
                'name': name,
                'methods': self._extract_interface_methods(type_node, code)
            }
        
        return {'kind': 'unknown'}
    
    def _extract_struct_fields(self, node, code: bytes) -> List[str]:
        """提取struct字段"""
        fields = []
        for child in node.children:
            if child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'field_declaration':
                        fields.append(code[field.start_byte:field.end_byte].decode())
        return fields
    
    def _extract_interface_methods(self, node, code: bytes) -> List[str]:
        """提取interface方法"""
        methods = []
        for child in node.children:
            if child.type == 'interface_type':
                for method in child.children:
                    if method.type == 'method_spec':
                        methods.append(code[method.start_byte:method.end_byte].decode())
        return methods
    
    def _calculate_complexity(self, code: str) -> int:
        """计算圈复杂度（简化版）"""
        # 简单统计分支语句数量
        complexity = 1
        keywords = ['if', 'for', 'case', 'switch', '&&', '||']
        for keyword in keywords:
            complexity += code.count(keyword)
        return complexity
    
    def _count_executable_lines(self, code: str) -> int:
        """
        计算可执行代码行数（排除注释、空行、仅包含括号的行）
        
        Args:
            code: 函数体代码
            
        Returns:
            可执行代码行数
        """
        if not code:
            return 0
        
        lines = code.split('\n')
        executable_count = 0
        
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                continue
            
            # 处理块注释
            if '/*' in stripped:
                in_block_comment = True
            if in_block_comment:
                if '*/' in stripped:
                    in_block_comment = False
                continue
            
            # 跳过单行注释
            if stripped.startswith('//'):
                continue
            
            # 跳过仅包含括号的行
            if stripped in ['{', '}', '{}', '};']:
                continue
            
            # 跳过 package 和 import 语句
            if stripped.startswith('package ') or stripped.startswith('import '):
                continue
            
            # 计为可执行代码行
            executable_count += 1
        
        return executable_count
    
    def analyze_directory(self, dir_path: str) -> List[Dict]:
        """分析Go项目目录"""
        results = []
        dir_path = Path(dir_path)
        
        # 递归查找所有.go文件
        for go_file in dir_path.rglob('*.go'):
            # 跳过测试文件和vendor目录
            if '_test.go' in go_file.name or 'vendor' in go_file.parts:
                continue
            
            result = self.analyze_file(str(go_file))
            if result['functions']:  # 只保留有函数的文件
                results.append(result)
        
        logger.info(f"✅ 分析完成: 找到 {len(results)} 个文件")
        return results


class CppAnalyzer(CodeAnalyzer):
    """C++代码分析器"""
    
    def __init__(self):
        super().__init__("cpp")
        language = tree_sitter_languages.get_language('cpp')
        self.parser.set_language(language)
    
    def analyze_file(self, file_path: str) -> Dict:
        """分析C++文件"""
        try:
            with open(file_path, 'rb') as f:
                code = f.read()
            
            tree = self.parser.parse(code)
            root_node = tree.root_node
            
            functions = []
            classes = []
            
            for node in root_node.children:
                if node.type == 'function_definition':
                    func_info = self._extract_function(node, code)
                    functions.append(func_info)
                elif node.type == 'class_specifier':
                    class_info = self._extract_class(node, code)
                    classes.append(class_info)
            
            return {
                'file_path': file_path,
                'functions': functions,
                'classes': classes
            }
        
        except Exception as e:
            logger.error(f"分析C++文件失败 {file_path}: {e}")
            return {'file_path': file_path, 'functions': [], 'classes': []}
    
    def _extract_function(self, node, code: bytes) -> Dict:
        """提取C++函数信息"""
        declarator = node.child_by_field_name('declarator')
        if not declarator:
            return {}
        
        # 提取函数名（可能在不同层级）
        name = self._get_function_name(declarator, code)
        
        body_node = node.child_by_field_name('body')
        body = code[body_node.start_byte:body_node.end_byte].decode() if body_node else ""
        
        return {
            'name': name,
            'type': 'function',
            'body': body,
            'start_line': node.start_point[0],
            'end_line': node.end_point[0],
            'complexity': self._calculate_complexity(body),
            'executable_lines': self._count_executable_lines(body)
        }
    
    def _get_function_name(self, node, code: bytes) -> str:
        """递归获取函数名"""
        if node.type == 'identifier':
            return code[node.start_byte:node.end_byte].decode()
        for child in node.children:
            name = self._get_function_name(child, code)
            if name:
                return name
        return ""
    
    def _extract_class(self, node, code: bytes) -> Dict:
        """提取C++类信息"""
        name_node = node.child_by_field_name('name')
        name = code[name_node.start_byte:name_node.end_byte].decode() if name_node else ""
        
        return {
            'name': name,
            'type': 'class'
        }
    
    def _calculate_complexity(self, code: str) -> int:
        """计算圈复杂度"""
        complexity = 1
        keywords = ['if', 'for', 'while', 'case', '&&', '||', 'catch']
        for keyword in keywords:
            complexity += code.count(keyword)
        return complexity
    
    def _count_executable_lines(self, code: str) -> int:
        """计算可执行代码行数（C++版本）"""
        if not code:
            return 0
        
        lines = code.split('\n')
        executable_count = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # 处理块注释
            if '/*' in stripped:
                in_block_comment = True
            if in_block_comment:
                if '*/' in stripped:
                    in_block_comment = False
                continue
            
            # 跳过单行注释
            if stripped.startswith('//'):
                continue
            
            # 跳过仅包含括号的行
            if stripped in ['{', '}', '{}', '};']:
                continue
            
            # 跳过预处理指令
            if stripped.startswith('#'):
                continue
            
            executable_count += 1
        
        return executable_count
    
    def analyze_directory(self, dir_path: str) -> List[Dict]:
        """分析C++项目目录"""
        results = []
        dir_path = Path(dir_path)
        
        for cpp_file in dir_path.rglob('*.cpp'):
            result = self.analyze_file(str(cpp_file))
            if result['functions'] or result['classes']:
                results.append(result)
        
        for cc_file in dir_path.rglob('*.cc'):
            result = self.analyze_file(str(cc_file))
            if result['functions'] or result['classes']:
                results.append(result)
        
        logger.info(f"✅ 分析完成: 找到 {len(results)} 个文件")
        return results


class CAnalyzer(CodeAnalyzer):
    """C代码分析器"""
    
    def __init__(self):
        super().__init__("c")
        language = tree_sitter_languages.get_language('c')
        self.parser.set_language(language)
    
    def analyze_file(self, file_path: str) -> Dict:
        """分析C文件"""
        try:
            with open(file_path, 'rb') as f:
                code = f.read()
            
            tree = self.parser.parse(code)
            root_node = tree.root_node
            
            functions = []
            
            for node in root_node.children:
                if node.type == 'function_definition':
                    func_info = self._extract_function(node, code)
                    functions.append(func_info)
            
            return {
                'file_path': file_path,
                'functions': functions
            }
        
        except Exception as e:
            logger.error(f"分析C文件失败 {file_path}: {e}")
            return {'file_path': file_path, 'functions': []}
    
    def _extract_function(self, node, code: bytes) -> Dict:
        """提取C函数信息"""
        declarator = node.child_by_field_name('declarator')
        if not declarator:
            return {}
        
        name = self._get_function_name(declarator, code)
        
        body_node = node.child_by_field_name('body')
        body = code[body_node.start_byte:body_node.end_byte].decode() if body_node else ""
        
        return {
            'name': name,
            'type': 'function',
            'body': body,
            'start_line': node.start_point[0],
            'end_line': node.end_point[0],
            'complexity': self._calculate_complexity(body),
            'executable_lines': self._count_executable_lines(body)
        }
    
    def _get_function_name(self, node, code: bytes) -> str:
        """递归获取函数名"""
        if node.type == 'identifier':
            return code[node.start_byte:node.end_byte].decode()
        for child in node.children:
            name = self._get_function_name(child, code)
            if name:
                return name
        return ""
    
    def _calculate_complexity(self, code: str) -> int:
        """计算圈复杂度"""
        complexity = 1
        keywords = ['if', 'for', 'while', 'case', '&&', '||']
        for keyword in keywords:
            complexity += code.count(keyword)
        return complexity
    
    def _count_executable_lines(self, code: str) -> int:
        """计算可执行代码行数（C版本）"""
        if not code:
            return 0
        
        lines = code.split('\n')
        executable_count = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # 处理块注释
            if '/*' in stripped:
                in_block_comment = True
            if in_block_comment:
                if '*/' in stripped:
                    in_block_comment = False
                continue
            
            # 跳过单行注释
            if stripped.startswith('//'):
                continue
            
            # 跳过仅包含括号的行
            if stripped in ['{', '}', '{}', '};']:
                continue
            
            # 跳过预处理指令
            if stripped.startswith('#'):
                continue
            
            executable_count += 1
        
        return executable_count
    
    def analyze_directory(self, dir_path: str) -> List[Dict]:
        """分析C项目目录"""
        results = []
        dir_path = Path(dir_path)
        
        for c_file in dir_path.rglob('*.c'):
            # 跳过测试文件
            if 'test' in c_file.name.lower():
                continue
            
            result = self.analyze_file(str(c_file))
            if result['functions']:
                results.append(result)
        
        logger.info(f"✅ 分析完成: 找到 {len(results)} 个文件")
        return results


def get_analyzer(language: str) -> CodeAnalyzer:
    """工厂函数：获取对应语言的分析器"""
    analyzers = {
        'golang': GolangAnalyzer,
        'cpp': CppAnalyzer,
        'c': CAnalyzer
    }
    
    analyzer_class = analyzers.get(language)
    if not analyzer_class:
        raise ValueError(f"不支持的语言: {language}")
    
    return analyzer_class()

