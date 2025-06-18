"""Jstat命令测试"""

from datetime import datetime
from unittest.mock import Mock
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.jstat import JstatCommand, JstatFormatter
import pytest

class TestJstatCommand:
    """Jstat命令测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.formatter = Mock(spec=JstatFormatter)
        self.executor = Mock(spec=NativeCommandExecutor)
        self.command = JstatCommand(self.executor, self.formatter)

    def test_get_command_no_option(self):
        """测试无选项的命令生成"""
        result = self.command.get_command(pid="1234")
        assert result == "jstat 1234"

    def test_get_command_with_option(self):
        """测试带选项的命令生成"""
        result = self.command.get_command(pid="1234", option="gc")
        assert result == "jstat -gc 1234"

    def test_get_command_with_interval(self):
        """测试带间隔的命令生成"""
        result = self.command.get_command(pid="1234", option="gc", interval=1000)
        assert result == "jstat -gc 1234 1000"

    def test_get_command_with_interval_and_count(self):
        """测试带间隔和次数的命令生成"""
        result = self.command.get_command(pid="1234", option="gc", interval=1000, count=5)
        assert result == "jstat -gc 1234 1000 5"

    def test_execute_success_gc(self):
        """测试成功执行GC统计"""
        timestamp = datetime.now()
        mock_output = """
         S0C    S1C    S0U    S1U      EC       EU        OC         OU       MC     MU    CCSC   CCSU   YGC     YGCT    FGC    FGCT     GCT   
        1024.0 1024.0  0.0    0.0   8192.0   0.0    20480.0    0.0    4480.0 4000.0 384.0  350.0      0    0.000   0      0.000    0.000
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
            "output": mock_output,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute(pid="1234", option="gc")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jstat -gc 1234", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_success_class(self):
        """测试成功执行类加载统计"""
        timestamp = datetime.now()
        mock_output = """
        Loaded  Bytes  Unloaded  Bytes     Time   
         10234  20468        0     0.0       2.35
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
            "output": mock_output,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute(pid="1234", option="class")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jstat -class 1234", timeout=30)
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
            "error": error_msg,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute(pid="1234")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jstat 1234", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_with_interval_and_count(self):
        """测试带间隔和次数的执行"""
        timestamp = datetime.now()
        mock_output = """
         S0C    S1C    S0U    S1U      EC       EU        OC         OU       MC     MU    CCSC   CCSU   YGC     YGCT    FGC    FGCT     GCT   
        1024.0 1024.0  0.0    0.0   8192.0   0.0    20480.0    0.0    4480.0 4000.0 384.0  350.0      0    0.000   0      0.000    0.000
        1024.0 1024.0  0.0    0.0   8192.0  100.0   20480.0   50.0    4480.0 4100.0 384.0  355.0      0    0.000   0      0.000    0.000
        1024.0 1024.0  0.0    0.0   8192.0  200.0   20480.0  100.0    4480.0 4200.0 384.0  360.0      1    0.001   0      0.000    0.001
        """
        
        self.executor.run.return_value = CommandResult(
            success=True,
            output=mock_output,
            error=None,
            execution_time=2.1,
            timestamp=timestamp
        )
        
        expected_result = {
            "success": True,
            "output": mock_output,
            "execution_time": 2.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute(pid="1234", option="gc", interval=1000, count=3)
        assert result == expected_result
        self.executor.run.assert_called_once_with("jstat -gc 1234 1000 3", timeout=30)
        self.formatter.format.assert_called_once()

if __name__ == '__main__':
    pytest.main()
 