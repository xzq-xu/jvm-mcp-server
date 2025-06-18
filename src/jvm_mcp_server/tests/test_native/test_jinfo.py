"""Jinfo命令测试"""

from datetime import datetime
from unittest.mock import Mock
import pytest
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.jinfo import JinfoCommand, JinfoOption, JinfoFormatter

class TestJinfoCommand:
    """Jinfo命令测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.formatter = Mock(spec=JinfoFormatter)
        self.executor = Mock(spec=NativeCommandExecutor)
        self.command = JinfoCommand(self.executor, self.formatter)

    def test_get_command_flags(self):
        """测试获取JVM启动参数命令"""
        result = self.command.get_command(pid="1234", option=JinfoOption.FLAGS)
        assert result == "jinfo -flags 1234"

    def test_get_command_sysprops(self):
        """测试获取系统属性命令"""
        result = self.command.get_command(pid="1234", option=JinfoOption.SYSPROPS)
        assert result == "jinfo -sysprops 1234"

    def test_get_command_all(self):
        """测试获取全部信息命令"""
        result = self.command.get_command(pid="1234", option=JinfoOption.ALL)
        assert result == "jinfo 1234"

    def test_get_command_default(self):
        """测试默认命令（全部信息）"""
        result = self.command.get_command(pid="1234")
        assert result == "jinfo 1234"

    def test_execute_flags_success(self):
        """测试成功执行JVM启动参数查询"""
        timestamp = datetime.now()
        mock_output = """
        VM Flags:
        -XX:CICompilerCount=4 -XX:InitialHeapSize=268435456 -XX:MaxHeapSize=4294967296
        -XX:MaxNewSize=1431306240 -XX:MinHeapDeltaBytes=524288 -XX:NewSize=89128960
        -XX:OldSize=179306496 -XX:+UseCompressedClassPointers -XX:+UseCompressedOops
        -XX:+UseParallelGC
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
        
        result = self.command.execute(pid="1234", option=JinfoOption.FLAGS)
        assert result == expected_result
        self.executor.run.assert_called_once_with("jinfo -flags 1234", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_sysprops_success(self):
        """测试成功执行系统属性查询"""
        timestamp = datetime.now()
        mock_output = """
        Java System Properties:
        java.runtime.name = Java(TM) SE Runtime Environment
        java.vm.version = 11.0.12+8-LTS-237
        java.runtime.version = 11.0.12+8-LTS-237
        java.home = /Library/Java/JavaVirtualMachines/jdk-11.0.12.jdk/Contents/Home
        java.class.path = target/classes
        java.library.path = /usr/local/lib:/usr/lib
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
        
        result = self.command.execute(pid="1234", option=JinfoOption.SYSPROPS)
        assert result == expected_result
        self.executor.run.assert_called_once_with("jinfo -sysprops 1234", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_all_success(self):
        """测试成功执行全部信息查询"""
        timestamp = datetime.now()
        mock_output = """
        Java System Properties:
        java.runtime.name = Java(TM) SE Runtime Environment
        java.vm.version = 11.0.12+8-LTS-237
        
        VM Flags:
        -XX:CICompilerCount=4 -XX:InitialHeapSize=268435456 -XX:MaxHeapSize=4294967296
        -XX:+UseParallelGC
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
        
        result = self.command.execute(pid="1234", option=JinfoOption.ALL)
        assert result == expected_result
        self.executor.run.assert_called_once_with("jinfo 1234", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_failure(self):
        """测试执行失败"""
        timestamp = datetime.now()
        error_msg = "Unable to open socket file: target process not found"
        
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
        self.executor.run.assert_called_once_with("jinfo 1234", timeout=30)
        self.formatter.format.assert_called_once()

if __name__ == '__main__':
    pytest.main()
 