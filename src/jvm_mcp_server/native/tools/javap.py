"""Javap命令实现"""

import re
import subprocess
from typing import Dict, Any, List, Optional
from ..base import BaseCommand, CommandResult, OutputFormatter

class JavapCommand(BaseCommand):
    """Javap命令实现"""

    def __init__(self, executor, formatter):
        super().__init__(executor, formatter)
        self.timeout = 30  # 设置默认超时时间为30秒

    def get_command(self, class_name: str, show_detail: bool = False, 
                   show_fields: bool = False, show_line_numbers: bool = False,
                   show_method_signatures: bool = False, classpath: Optional[str] = None) -> str:
        """获取javap命令

        Args:
            class_name: 类名
            show_detail: 是否显示详细信息 (-v)
            show_fields: 是否显示字段信息 (-p)
            show_line_numbers: 是否显示行号 (-l)
            show_method_signatures: 是否显示方法签名 (-s)
            classpath: 类路径

        Returns:
            str: javap命令字符串
        """
        # 验证类名参数
        if not class_name or not class_name.strip():
            raise ValueError("Class name is required")
        
        # 构建命令参数
        args = ["javap"]
        
        if classpath:
            args.extend(["-cp", classpath])
        
        if show_detail:
            args.append("-v")
        
        if show_fields:
            args.append("-p")
            
        if show_line_numbers:
            args.append("-l")
            
        if show_method_signatures:
            args.append("-s")
        
        args.append(class_name.strip())
        
        return " ".join(args)

    def execute(self, class_name: str, **kwargs) -> Dict[str, Any]:
        """执行javap命令

        Args:
            class_name: 类名
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            command = self.get_command(class_name, **kwargs)
            result = self.executor.run(command, timeout=self.timeout)
            return self.formatter.format(result)
        except Exception as e:
            # 创建失败结果
            from datetime import datetime
            failed_result = CommandResult(
                success=False,
                output="",
                error=str(e),
                execution_time=0.0,
                timestamp=datetime.now()
            )
            return self.formatter.format(failed_result)

class JavapFormatter(OutputFormatter):
    """Javap输出格式化器"""

    def format(self, result: CommandResult) -> Dict[str, Any]:
        """格式化javap输出

        Args:
            result: 命令执行结果

        Returns:
            Dict[str, Any]: 格式化后的结果
        """
        if not result.success:
            return {
                "success": False,
                "error": result.error,
                "timestamp": result.timestamp.isoformat()
            }

        # 解析javap输出
        class_info = self._parse_javap_output(result.output)
        
        return {
            "success": True,
            "class_info": class_info,
            "raw_output": result.output,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
        }

    def _parse_javap_output(self, output: str) -> Dict[str, Any]:
        """解析javap输出

        Args:
            output: javap原始输出

        Returns:
            Dict[str, Any]: 解析后的类信息
        """
        lines = output.splitlines()
        if not lines:
            return {}

        class_info = {
            "class_name": "",
            "modifiers": [],
            "superclass": "",
            "interfaces": [],
            "fields": [],
            "methods": [],
            "inner_classes": [],
            "annotations": []
        }

        # 解析类声明行
        class_declaration = self._find_class_declaration(lines)
        if class_declaration:
            class_info.update(class_declaration)

        # 解析字段
        class_info["fields"] = self._parse_fields(lines)
        
        # 解析方法
        class_info["methods"] = self._parse_methods(lines)
        
        # 解析内部类
        class_info["inner_classes"] = self._parse_inner_classes(lines)

        return class_info

    def _find_class_declaration(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """查找并解析类声明行

        Args:
            lines: 输出行列表

        Returns:
            Optional[Dict[str, Any]]: 类声明信息
        """
        for line in lines:
            line = line.strip()
            # 匹配类声明模式
            class_patterns = [
                r'(?:public\s+)?(?:final\s+)?(?:abstract\s+)?class\s+(\S+)',
                r'(?:public\s+)?(?:abstract\s+)?interface\s+(\S+)',
                r'(?:public\s+)?enum\s+(\S+)'
            ]
            
            for pattern in class_patterns:
                match = re.search(pattern, line)
                if match:
                    class_name = match.group(1)
                    
                    # 提取修饰符
                    modifiers = []
                    if 'public' in line:
                        modifiers.append('public')
                    if 'final' in line:
                        modifiers.append('final')
                    if 'abstract' in line:
                        modifiers.append('abstract')
                    if 'interface' in line:
                        modifiers.append('interface')
                    if 'enum' in line:
                        modifiers.append('enum')

                    # 提取父类和接口
                    superclass = ""
                    interfaces = []
                    
                    if 'extends' in line:
                        extends_match = re.search(r'extends\s+(\S+)', line)
                        if extends_match:
                            superclass = extends_match.group(1)
                    
                    if 'implements' in line:
                        implements_match = re.search(r'implements\s+(.+?)(?:\s*\{|$)', line)
                        if implements_match:
                            interfaces_str = implements_match.group(1)
                            interfaces = [iface.strip() for iface in interfaces_str.split(',')]

                    return {
                        "class_name": class_name,
                        "modifiers": modifiers,
                        "superclass": superclass,
                        "interfaces": interfaces
                    }
        
        return None

    def _parse_fields(self, lines: List[str]) -> List[Dict[str, Any]]:
        """解析字段信息

        Args:
            lines: 输出行列表

        Returns:
            List[Dict[str, Any]]: 字段信息列表
        """
        fields = []
        in_fields_section = False
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('//') or line.startswith('/*'):
                continue
                
            # 字段模式匹配 (简化版)
            field_pattern = r'^\s*(?:(public|private|protected)\s+)?(?:(static|final)\s+)*(\w+(?:\[\])*)\s+(\w+);?'
            match = re.match(field_pattern, line)
            
            if match:
                visibility = match.group(1) or "package"
                modifiers = []
                if 'static' in line:
                    modifiers.append('static')
                if 'final' in line:
                    modifiers.append('final')
                    
                field_type = match.group(3)
                field_name = match.group(4)
                
                fields.append({
                    "name": field_name,
                    "type": field_type,
                    "visibility": visibility,
                    "modifiers": modifiers
                })
        
        return fields

    def _parse_methods(self, lines: List[str]) -> List[Dict[str, Any]]:
        """解析方法信息

        Args:
            lines: 输出行列表

        Returns:
            List[Dict[str, Any]]: 方法信息列表
        """
        methods = []
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('//') or line.startswith('/*'):
                continue
            
            # 方法模式匹配 (简化版)
            method_pattern = r'^\s*(?:(public|private|protected)\s+)?(?:(static|final|abstract)\s+)*(\w+(?:\[\])*)\s+(\w+)\s*\(([^)]*)\)'
            match = re.match(method_pattern, line)
            
            if match:
                visibility = match.group(1) or "package"
                modifiers = []
                if 'static' in line:
                    modifiers.append('static')
                if 'final' in line:
                    modifiers.append('final')
                if 'abstract' in line:
                    modifiers.append('abstract')
                    
                return_type = match.group(3)
                method_name = match.group(4)
                params_str = match.group(5)
                
                # 解析参数
                parameters = []
                if params_str.strip():
                    for param in params_str.split(','):
                        param = param.strip()
                        if param:
                            param_parts = param.split()
                            if len(param_parts) >= 2:
                                param_type = ' '.join(param_parts[:-1])
                                param_name = param_parts[-1]
                                parameters.append({
                                    "type": param_type,
                                    "name": param_name
                                })
                
                methods.append({
                    "name": method_name,
                    "return_type": return_type,
                    "visibility": visibility,
                    "modifiers": modifiers,
                    "parameters": parameters
                })
        
        return methods

    def _parse_inner_classes(self, lines: List[str]) -> List[str]:
        """解析内部类信息

        Args:
            lines: 输出行列表

        Returns:
            List[str]: 内部类名列表
        """
        inner_classes = []
        
        for line in lines:
            line = line.strip()
            
            # 匹配内部类声明
            inner_class_pattern = r'(?:public\s+)?(?:static\s+)?(?:final\s+)?class\s+(\w+)\s*{'
            match = re.search(inner_class_pattern, line)
            
            if match and not line.startswith('class '):  # 排除主类声明
                inner_classes.append(match.group(1))
        
        return inner_classes
