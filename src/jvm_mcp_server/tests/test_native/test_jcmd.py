"""Jcmd命令测试"""

from datetime import datetime
from unittest.mock import Mock
import pytest
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.jcmd import JcmdCommand, JcmdFormatter

class TestJcmdCommand:
    """Jcmd命令测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.formatter = Mock(spec=JcmdFormatter)
        self.executor = Mock(spec=NativeCommandExecutor)
        self.command = JcmdCommand(self.executor, self.formatter)

    def test_get_command_no_subcommand(self):
        """测试无子命令的命令生成"""
        result = self.command.get_command(pid="1234")
        assert result == "jcmd 1234"

    def test_get_command_with_subcommand(self):
        """测试带子命令的命令生成"""
        result = self.command.get_command(pid="1234", subcommand="Thread.print")
        assert result == "jcmd 1234 Thread.print"

    def test_execute_thread_print_success(self):
        """测试成功执行线程打印命令"""
        timestamp = datetime.now()
        mock_output = """
        1234:
        "main" #1 prio=5 os_prio=31 tid=0x00007f8b7b800000 nid=0x3e03 waiting on condition [0x000070000b1e9000]
           java.lang.Thread.State: TIMED_WAITING (sleeping)
                at java.lang.Thread.sleep(java.base@11.0.12/Native Method)
                at com.example.Main.main(Main.java:10)
        
        "GC task thread#0 (ParallelGC)" os_prio=31 tid=0x00007f8b7b801800 nid=0x2403 runnable
        
        "VM Periodic Task Thread" os_prio=31 tid=0x00007f8b7b802800 nid=0x4c03 waiting on condition
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
        
        result = self.command.execute(pid="1234", subcommand="Thread.print")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jcmd 1234 Thread.print", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_gc_histogram_success(self):
        """测试成功执行GC直方图命令"""
        timestamp = datetime.now()
        mock_output = """
        1234:
         num     #instances         #bytes  class name (module)
        -------------------------------------------------------
           1:         38225        5242880  [B (java.base@11.0.12)
           2:         12200        1024768  java.lang.String (java.base@11.0.12)
           3:          5000         120000  java.util.HashMap$Node (java.base@11.0.12)
        
        Total        55425        6387648
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
        
        result = self.command.execute(pid="1234", subcommand="GC.class_histogram")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jcmd 1234 GC.class_histogram", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_help_success(self):
        """测试成功执行帮助命令"""
        timestamp = datetime.now()
        mock_output = """
        1234:
        The following commands are available:
        JFR.stop
        JFR.start
        JFR.dump
        JFR.check
        VM.native_memory
        VM.check_commercial_features
        VM.unlock_commercial_features
        Thread.print
        GC.class_histogram
        GC.heap_dump
        GC.run
        GC.run_finalization
        VM.uptime
        VM.flags
        VM.system_properties
        VM.command_line
        VM.version
        help
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
        
        result = self.command.execute(pid="1234", subcommand="help")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jcmd 1234 help", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_failure_process_not_found(self):
        """测试执行失败 - 进程未找到"""
        timestamp = datetime.now()
        error_msg = "Error: Process 1234 not found."
        
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
        self.executor.run.assert_called_once_with("jcmd 1234", timeout=30)
        self.formatter.format.assert_called_once()

    def test_execute_failure_invalid_subcommand(self):
        """测试执行失败 - 无效的子命令"""
        timestamp = datetime.now()
        error_msg = "Error: Unknown diagnostic command 'invalid.command'"
        
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
        
        result = self.command.execute(pid="1234", subcommand="invalid.command")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jcmd 1234 invalid.command", timeout=30)
        self.formatter.format.assert_called_once()

if __name__ == '__main__':
    pytest.main()
 