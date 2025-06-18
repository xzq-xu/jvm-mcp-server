"""Javap命令测试"""

from datetime import datetime
from unittest.mock import Mock
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.javap import JavapCommand, JavapFormatter
import pytest

class TestJavapCommand:
    """Javap命令测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.formatter = Mock(spec=JavapFormatter)
        self.executor = Mock(spec=NativeCommandExecutor)

    def test_get_command_basic(self):
        """测试基础命令生成"""
        command = JavapCommand(self.executor, self.formatter)
        result = command.get_command(class_name="java.lang.String")
        assert result == "javap java.lang.String"

    def test_get_command_with_detail(self):
        """测试详细信息命令生成"""
        command = JavapCommand(self.executor, self.formatter)
        result = command.get_command(class_name="java.lang.String", show_detail=True)
        assert result == "javap -v java.lang.String"

    def test_get_command_with_fields(self):
        """测试显示字段命令生成"""
        command = JavapCommand(self.executor, self.formatter)
        result = command.get_command(class_name="java.lang.String", show_fields=True)
        assert result == "javap -p java.lang.String"

    def test_get_command_with_signatures(self):
        """测试显示方法签名命令生成"""
        command = JavapCommand(self.executor, self.formatter)
        result = command.get_command(class_name="java.lang.String", show_method_signatures=True)
        assert result == "javap -s java.lang.String"

    def test_get_command_with_line_numbers(self):
        """测试显示行号命令生成"""
        command = JavapCommand(self.executor, self.formatter)
        result = command.get_command(class_name="java.lang.String", show_line_numbers=True)
        assert result == "javap -l java.lang.String"

    def test_get_command_with_classpath(self):
        """测试带classpath的命令生成"""
        command = JavapCommand(self.executor, self.formatter)
        result = command.get_command(
            class_name="com.example.MyClass", 
            classpath="/path/to/classes"
        )
        assert result == "javap -cp /path/to/classes com.example.MyClass"

    def test_get_command_combined_options(self):
        """测试组合选项命令生成"""
        command = JavapCommand(self.executor, self.formatter)
        result = command.get_command(
            class_name="java.lang.String",
            show_detail=True,
            show_fields=True,
            show_line_numbers=True,
            classpath="/usr/lib/java"
        )
        assert result == "javap -cp /usr/lib/java -v -p -l java.lang.String"

    def test_get_command_invalid_class_name(self):
        """测试无效类名参数"""
        command = JavapCommand(self.executor, self.formatter)
        
        # 空类名
        with pytest.raises(ValueError, match="Class name is required"):
            command.get_command(class_name="")
        
        # None类名 - 使用类型忽略注释
        with pytest.raises(ValueError, match="Class name is required"):
            command.get_command(class_name=None)  # type: ignore

    def test_execute_success(self):
        """测试成功执行"""
        command = JavapCommand(self.executor, self.formatter)
        timestamp = datetime.now()
        
        mock_output = """
public class java.lang.String implements java.io.Serializable, java.lang.Comparable<java.lang.String>, java.lang.CharSequence {
  private final char[] value;
  private int hash;
  
  public java.lang.String();
  public java.lang.String(java.lang.String);
  public int length();
  public char charAt(int);
}
        """
        
        self.executor.run.return_value = CommandResult(
            success=True,
            output=mock_output,
            error=None,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        expected_result = {
            "success": True,
            "class_info": {
                "class_name": "java.lang.String",
                "modifiers": ["public"],
                "superclass": "",
                "interfaces": ["java.io.Serializable", "java.lang.Comparable<java.lang.String>", "java.lang.CharSequence"],
                "fields": [
                    {"name": "value", "type": "char[]", "visibility": "private", "modifiers": ["final"]},
                    {"name": "hash", "type": "int", "visibility": "private", "modifiers": []}
                ],
                "methods": [
                    {"name": "String", "return_type": "", "visibility": "public", "modifiers": [], "parameters": []},
                    {"name": "String", "return_type": "", "visibility": "public", "modifiers": [], "parameters": [{"type": "java.lang.String", "name": "s"}]},
                    {"name": "length", "return_type": "int", "visibility": "public", "modifiers": [], "parameters": []},
                    {"name": "charAt", "return_type": "char", "visibility": "public", "modifiers": [], "parameters": [{"type": "int", "name": "index"}]}
                ],
                "inner_classes": [],
                "annotations": []
            },
            "raw_output": mock_output,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = command.execute(class_name="java.lang.String")
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.formatter.format.assert_called_once()

    def test_execute_failure(self):
        """测试执行失败"""
        command = JavapCommand(self.executor, self.formatter)
        timestamp = datetime.now()
        
        error_msg = "Class not found: com.nonexistent.Class"
        self.executor.run.return_value = CommandResult(
            success=False,
            output="",
            error=error_msg,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        expected_result = {
            "success": False,
            "error": error_msg,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = command.execute(class_name="com.nonexistent.Class")
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.formatter.format.assert_called_once()


class TestJavapFormatter:
    """Javap格式化器测试"""

    def test_format_success(self):
        """测试格式化成功输出"""
        formatter = JavapFormatter()
        timestamp = datetime.now()
        
        mock_output = """public class java.lang.String implements java.io.Serializable, java.lang.Comparable<java.lang.String> {
  private final char[] value;
  private int hash;
  
  public java.lang.String();
  public int length();
}"""
        
        result = CommandResult(
            success=True,
            output=mock_output,
            error=None,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        formatted = formatter.format(result)
        
        assert formatted["success"] is True
        assert "class_info" in formatted
        assert formatted["raw_output"] == mock_output
        assert formatted["execution_time"] == 0.1
        assert formatted["timestamp"] == timestamp.isoformat()

    def test_format_failure(self):
        """测试格式化失败输出"""
        formatter = JavapFormatter()
        timestamp = datetime.now()
        error_msg = "Class not found"
        
        result = CommandResult(
            success=False,
            output="",
            error=error_msg,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        formatted = formatter.format(result)
        
        assert formatted["success"] is False
        assert formatted["error"] == error_msg
        assert formatted["timestamp"] == timestamp.isoformat()
        assert "class_info" not in formatted

    def test_parse_class_declaration(self):
        """测试解析类声明"""
        formatter = JavapFormatter()
        
        # 测试普通类
        lines = ["public final class java.lang.String extends java.lang.Object implements java.io.Serializable {"]
        declaration = formatter._find_class_declaration(lines)
        
        assert declaration is not None
        assert declaration["class_name"] == "java.lang.String"
        assert "public" in declaration["modifiers"]
        assert "final" in declaration["modifiers"]
        assert declaration["superclass"] == "java.lang.Object"
        assert "java.io.Serializable" in declaration["interfaces"]

    def test_parse_interface_declaration(self):
        """测试解析接口声明"""
        formatter = JavapFormatter()
        
        lines = ["public interface java.util.List<E> extends java.util.Collection<E> {"]
        declaration = formatter._find_class_declaration(lines)
        
        assert declaration is not None
        assert declaration["class_name"] == "java.util.List<E>"
        assert "public" in declaration["modifiers"]
        assert "interface" in declaration["modifiers"]

    def test_parse_fields(self):
        """测试解析字段"""
        formatter = JavapFormatter()
        
        lines = [
            "  private final char[] value;",
            "  private int hash;",
            "  public static final String EMPTY;"
        ]
        
        fields = formatter._parse_fields(lines)
        
        assert len(fields) >= 2  # 至少解析出2个字段
        # 检查第一个字段
        value_field = next((f for f in fields if f["name"] == "value"), None)
        if value_field:
            assert value_field["type"] == "char[]"
            assert value_field["visibility"] == "private"
            assert "final" in value_field["modifiers"]

    def test_parse_methods(self):
        """测试解析方法"""
        formatter = JavapFormatter()
        
        lines = [
            "  public java.lang.String();",
            "  public int length();",
            "  public char charAt(int index);",
            "  private static void helper(String s, int count);"
        ]
        
        methods = formatter._parse_methods(lines)
        
        assert len(methods) >= 2  # 至少解析出2个方法
        # 检查length方法
        length_method = next((m for m in methods if m["name"] == "length"), None)
        if length_method:
            assert length_method["return_type"] == "int"
            assert length_method["visibility"] == "public"
            assert length_method["parameters"] == []

if __name__ == '__main__':
    pytest.main() 