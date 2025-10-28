"""测试用例数量策略模块

根据代码复杂度（可执行代码行数、圈复杂度）计算建议的测试用例数量
"""

from typing import Dict, List
from loguru import logger


class TestCaseStrategy:
    """测试用例数量策略"""
    
    def __init__(self):
        """初始化策略参数"""
        # 基础测试用例数量（最少）
        self.min_test_cases = 2
        
        # 最大测试用例数量（避免生成过多）
        self.max_test_cases = 15
        
        # 基于可执行代码行数的系数
        self.lines_per_test = 10  # 每10行代码生成1个额外测试用例
        
        # 基于圈复杂度的系数
        self.complexity_multiplier = 0.5  # 每个复杂度点增加0.5个测试用例
    
    def calculate_test_case_count(self, function_info: Dict) -> Dict:
        """
        计算建议的测试用例数量
        
        Args:
            function_info: 函数分析信息，包含:
                - name: 函数名
                - executable_lines: 可执行代码行数
                - complexity: 圈复杂度
                - type: 函数类型（function/method）
                
        Returns:
            测试用例策略字典:
                - total_count: 建议的总测试用例数
                - normal_cases: 正常场景测试用例数
                - edge_cases: 边界条件测试用例数
                - error_cases: 异常场景测试用例数
                - rationale: 计算依据说明
        """
        func_name = function_info.get('name', 'unknown')
        executable_lines = function_info.get('executable_lines', 0)
        complexity = function_info.get('complexity', 1)
        
        # 基础测试用例数（正常场景）
        base_cases = self.min_test_cases
        
        # 根据可执行代码行数增加测试用例
        lines_factor = max(0, executable_lines // self.lines_per_test)
        
        # 根据圈复杂度增加测试用例
        complexity_factor = int((complexity - 1) * self.complexity_multiplier)
        
        # 计算总测试用例数
        total_count = base_cases + lines_factor + complexity_factor
        
        # 限制在合理范围内
        total_count = max(self.min_test_cases, min(total_count, self.max_test_cases))
        
        # 分配测试用例类型
        # 40% 正常场景，30% 边界条件，30% 异常场景
        normal_cases = max(1, int(total_count * 0.4))
        edge_cases = max(1, int(total_count * 0.3))
        error_cases = max(1, int(total_count * 0.3))
        
        # 确保总数匹配
        actual_total = normal_cases + edge_cases + error_cases
        if actual_total < total_count:
            # 补充到正常场景
            normal_cases += (total_count - actual_total)
        
        # 构建计算依据说明
        rationale = self._build_rationale(
            func_name,
            executable_lines,
            complexity,
            lines_factor,
            complexity_factor,
            total_count
        )
        
        result = {
            'total_count': total_count,
            'normal_cases': normal_cases,
            'edge_cases': edge_cases,
            'error_cases': error_cases,
            'rationale': rationale,
            'metrics': {
                'executable_lines': executable_lines,
                'complexity': complexity,
                'lines_factor': lines_factor,
                'complexity_factor': complexity_factor
            }
        }
        
        logger.debug(f"📊 {func_name}: 建议生成 {total_count} 个测试用例 "
                    f"(正常:{normal_cases}, 边界:{edge_cases}, 异常:{error_cases})")
        
        return result
    
    def calculate_for_file(self, file_analysis: Dict) -> Dict:
        """
        为整个文件的所有函数计算测试用例策略
        
        Args:
            file_analysis: 文件分析结果，包含 functions 列表
            
        Returns:
            文件级测试用例策略:
                - total_test_cases: 文件总测试用例数
                - function_strategies: 各函数的测试用例策略字典
                - summary: 汇总信息
        """
        functions = file_analysis.get('functions', [])
        
        if not functions:
            return {
                'total_test_cases': 0,
                'function_strategies': {},
                'summary': '文件中没有找到函数'
            }
        
        function_strategies = {}
        total_test_cases = 0
        total_normal = 0
        total_edge = 0
        total_error = 0
        
        for func_info in functions:
            func_name = func_info.get('name', 'unknown')
            strategy = self.calculate_test_case_count(func_info)
            function_strategies[func_name] = strategy
            
            total_test_cases += strategy['total_count']
            total_normal += strategy['normal_cases']
            total_edge += strategy['edge_cases']
            total_error += strategy['error_cases']
        
        summary = (
            f"文件包含 {len(functions)} 个函数，建议生成 {total_test_cases} 个测试用例 "
            f"(正常:{total_normal}, 边界:{total_edge}, 异常:{total_error})"
        )
        
        logger.info(f"📋 {summary}")
        
        return {
            'total_test_cases': total_test_cases,
            'function_strategies': function_strategies,
            'function_count': len(functions),
            'summary': summary,
            'breakdown': {
                'normal_cases': total_normal,
                'edge_cases': total_edge,
                'error_cases': total_error
            }
        }
    
    def _build_rationale(
        self,
        func_name: str,
        executable_lines: int,
        complexity: int,
        lines_factor: int,
        complexity_factor: int,
        total_count: int
    ) -> str:
        """构建测试用例数量的计算依据说明"""
        
        parts = [
            f"函数 {func_name}:",
            f"- 可执行代码行数: {executable_lines} 行",
            f"- 圈复杂度: {complexity}",
            f"- 基于代码行数增加: {lines_factor} 个用例",
            f"- 基于复杂度增加: {complexity_factor} 个用例",
            f"- 建议总测试用例数: {total_count}"
        ]
        
        return '\n'.join(parts)
    
    def get_test_case_descriptions(self, strategy: Dict, function_info: Dict) -> List[str]:
        """
        生成测试用例的具体描述（用于AI生成提示）
        
        Args:
            strategy: 测试用例策略
            function_info: 函数信息
            
        Returns:
            测试用例描述列表
        """
        descriptions = []
        
        func_name = function_info.get('name', 'unknown')
        normal_count = strategy['normal_cases']
        edge_count = strategy['edge_cases']
        error_count = strategy['error_cases']
        
        # 正常场景测试用例
        for i in range(normal_count):
            if i == 0:
                descriptions.append(f"正常场景: 使用标准有效输入测试 {func_name}")
            elif i == 1 and normal_count > 1:
                descriptions.append(f"正常场景: 使用另一组典型输入测试 {func_name}")
            else:
                descriptions.append(f"正常场景 {i+1}: 测试 {func_name} 的不同正常情况")
        
        # 边界条件测试用例
        for i in range(edge_count):
            if i == 0:
                descriptions.append(f"边界条件: 测试 {func_name} 的最小值/空值情况")
            elif i == 1 and edge_count > 1:
                descriptions.append(f"边界条件: 测试 {func_name} 的最大值/临界值情况")
            else:
                descriptions.append(f"边界条件 {i+1}: 测试 {func_name} 的其他边界场景")
        
        # 异常场景测试用例
        for i in range(error_count):
            if i == 0:
                descriptions.append(f"异常场景: 测试 {func_name} 处理无效输入")
            elif i == 1 and error_count > 1:
                descriptions.append(f"异常场景: 测试 {func_name} 处理错误状态")
            else:
                descriptions.append(f"异常场景 {i+1}: 测试 {func_name} 的其他异常情况")
        
        return descriptions


# 全局策略实例
_global_strategy = None


def get_test_case_strategy() -> TestCaseStrategy:
    """获取全局测试用例策略实例（单例模式）"""
    global _global_strategy
    if _global_strategy is None:
        _global_strategy = TestCaseStrategy()
    return _global_strategy

