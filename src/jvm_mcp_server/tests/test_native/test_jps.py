"""JPS命令测试"""

from datetime import datetime
from unittest.mock import Mock, patch
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.jps import JpsCommand, JpsFormatter
import pytest

class TestJpsCommand:
    """Jps命令测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.formatter = Mock(spec=JpsFormatter)
        self.executor = Mock(spec=NativeCommandExecutor)
        self.command = JpsCommand(self.executor, self.formatter)

    def test_get_command(self):
        """测试命令生成"""
        result = self.command.get_command()
        assert result == "jps -l -v"

    def test_execute_success(self):
        """测试成功执行"""
        timestamp = datetime.now()
        mock_output = """
        1234 org.example.MainClass -Xmx1g
        5678 jdk.jcmd.JCmd
        9012 com.example.App -Xms512m -Xmx2g
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
            "processes": [
                {"pid": "1234", "name": "org.example.MainClass", "args": "-Xmx1g"},
                {"pid": "5678", "name": "jdk.jcmd.JCmd", "args": ""},
                {"pid": "9012", "name": "com.example.App", "args": "-Xms512m -Xmx2g"}
            ],
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute()
        assert result == expected_result
        self.executor.run.assert_called_once_with("jps -l -v", timeout=None)
        self.formatter.format.assert_called_once()

    def test_execute_failure(self):
        """测试执行失败"""
        timestamp = datetime.now()
        error_msg = "Test error"
        
        self.executor.run.return_value = CommandResult(
            success=False,
            output="",
            error=error_msg,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        expected_result = {
            "success": False,
            "processes": [],
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute()
        assert result == expected_result
        self.executor.run.assert_called_once_with("jps -l -v", timeout=None)
        self.formatter.format.assert_called_once()

    def test_empty_output(self):
        """测试空输出"""
        timestamp = datetime.now()
        
        self.executor.run.return_value = CommandResult(
            success=True,
            output="",
            error=None,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        expected_result = {
            "success": True,
            "processes": [],
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute()
        assert result == expected_result
        self.executor.run.assert_called_once_with("jps -l -v", timeout=None)
        self.formatter.format.assert_called_once()

    def test_malformed_output(self):
        """测试格式错误的输出"""
        timestamp = datetime.now()
        mock_output = """
        invalid output
        1234
        5678 org.example.App
        not_a_pid some.class
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
            "processes": [
                {"pid": "5678", "name": "org.example.App", "args": ""}
            ],
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute()
        assert result == expected_result
        self.executor.run.assert_called_once_with("jps -l -v", timeout=None)
        self.formatter.format.assert_called_once()

if __name__ == '__main__':
    pytest.main()
 