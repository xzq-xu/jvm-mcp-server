"""JStack命令测试"""

from unittest.mock import Mock
import pytest
from datetime import datetime
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.jstack import JstackCommand, JstackFormatter

class TestJstackCommand:
    """Jstack命令测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.formatter = Mock(spec=JstackFormatter)
        self.executor = Mock(spec=NativeCommandExecutor)
        self.command = JstackCommand(self.executor, self.formatter)

    def test_get_command(self):
        """测试命令生成"""
        result = self.command.get_command(pid="1234")
        assert result == "jstack -l 1234"

    def test_execute_success(self):
        """测试成功执行"""
        timestamp = datetime.now()
        mock_output = """
        "main" #1 prio=5 os_prio=31 cpu=64.58ms elapsed=1.32s tid=0x00007f9a8d00e000 nid=0x2c03 waiting on condition  [0x000070000c5c1000]
           java.lang.Thread.State: TIMED_WAITING (sleeping)
                at java.lang.Thread.sleep(java.base@11.0.12/Native Method)
                at com.example.Main.main(Main.java:10)
           Locked synchronizers: count = 1
                - <0x00000007956c4f80> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)

        "Thread-1" #11 prio=5 os_prio=31 cpu=0.34ms elapsed=1.29s tid=0x00007f9a8d081000 nid=0x5603 waiting for monitor entry  [0x000070000c8e4000]
           java.lang.Thread.State: BLOCKED (on object monitor)
                at com.example.Worker.process(Worker.java:24)
                - waiting to lock <0x00000007956c4f90> (a java.lang.Object)
                at com.example.Main$1.run(Main.java:20)
           Locked synchronizers: count = 0
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
            "threads": [
                {
                    "name": "main",
                    "state": "TIMED_WAITING (sleeping)",
                    "stack_trace": [
                        "at java.lang.Thread.sleep(java.base@11.0.12/Native Method)",
                        "at com.example.Main.main(Main.java:10)"
                    ],
                    "locks": [
                        "- <0x00000007956c4f80> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)"
                    ]
                },
                {
                    "name": "Thread-1",
                    "state": "BLOCKED (on object monitor)",
                    "stack_trace": [
                        "at com.example.Worker.process(Worker.java:24)",
                        "at com.example.Main$1.run(Main.java:20)"
                    ],
                    "locks": [
                        "- waiting to lock <0x00000007956c4f90> (a java.lang.Object)"
                    ]
                }
            ],
            "thread_count": 2,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute(pid="1234")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jstack -l 1234", timeout=30)
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
        self.executor.run.assert_called_once_with("jstack -l 1234", timeout=30)
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
            "threads": [],
            "thread_count": 0,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute(pid="1234")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jstack -l 1234", timeout=30)
        self.formatter.format.assert_called_once()

    def test_malformed_output(self):
        """测试格式错误的输出"""
        timestamp = datetime.now()
        mock_output = """
        Invalid thread dump format
        "Thread-1" invalid format
        Random text
        java.lang.Thread.State: RUNNABLE
        at some.method()
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
            "threads": [
                {
                    "name": "Thread-1",
                    "state": "RUNNABLE",
                    "stack_trace": ["at some.method()"],
                    "locks": []
                }
            ],
            "thread_count": 1,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.formatter.format.return_value = expected_result
        
        result = self.command.execute(pid="1234")
        assert result == expected_result
        self.executor.run.assert_called_once_with("jstack -l 1234", timeout=30)
        self.formatter.format.assert_called_once()

if __name__ == '__main__':
    pytest.main()
 