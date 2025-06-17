"""Jmap命令测试"""

import os
from datetime import datetime
from unittest.mock import Mock, patch
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.jmap import (
    JmapCommand, JmapOperation,
    JmapHeapFormatter, JmapHistoFormatter, JmapDumpFormatter
    )
import pytest

class TestJmapCommand:
    """Jmap命令测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.heap_formatter = Mock(spec=JmapHeapFormatter)
        self.histo_formatter = Mock(spec=JmapHistoFormatter)
        self.dump_formatter = Mock(spec=JmapDumpFormatter)
        self.executor = Mock(spec=NativeCommandExecutor)

    def test_get_command_heap(self):
        """测试heap命令生成"""
        command = JmapCommand(self.executor, self.heap_formatter)
        result = command.get_command(pid="1234", operation=JmapOperation.HEAP)
        assert result == "jmap -heap 1234"

    def test_get_command_histo(self):
        """测试histo命令生成"""
        command = JmapCommand(self.executor, self.histo_formatter)
        result = command.get_command(pid="1234", operation=JmapOperation.HISTO)
        assert result == "jmap -histo 1234"

    def test_get_command_histo_live(self):
        """测试histo命令生成（仅存活对象）"""
        command = JmapCommand(self.executor, self.histo_formatter)
        result = command.get_command(pid="1234", operation=JmapOperation.HISTO, live_only=True)
        assert result == "jmap -histo -live 1234"

    def test_get_command_dump(self):
        """测试dump命令生成"""
        command = JmapCommand(self.executor, self.dump_formatter)
        result = command.get_command(pid="1234", operation=JmapOperation.DUMP, dump_file="heap.bin")
        assert result == "jmap -dump:format=b,file=heap.bin 1234"

    def test_get_command_dump_live(self):
        """测试dump命令生成（仅存活对象）"""
        command = JmapCommand(self.executor, self.dump_formatter)
        result = command.get_command(pid="1234", operation=JmapOperation.DUMP, dump_file="heap.bin", live_only=True)
        assert result == "jmap -dump:format=b:live,file=heap.bin 1234"

    def test_get_command_dump_no_file(self):
        """测试dump命令生成（无文件名）"""
        command = JmapCommand(self.executor, self.dump_formatter)
        with pytest.raises(ValueError, match="dump_file is required for dump operation"):
            command.get_command(pid="1234", operation=JmapOperation.DUMP)

    def test_execute_success(self):
        """测试成功执行"""
        command = JmapCommand(self.executor, self.heap_formatter)
        timestamp = datetime.now()
        
        self.executor.run.return_value = CommandResult(
            success=True,
            output="Test output",
            error=None,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        expected_result = {
            "success": True,
            "output": "Test output",
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.heap_formatter.format.return_value = expected_result
        
        result = command.execute(pid="1234")
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.heap_formatter.format.assert_called_once()

    def test_execute_failure(self):
        """测试执行失败"""
        command = JmapCommand(self.executor, self.heap_formatter)
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
        
        self.heap_formatter.format.return_value = expected_result
        
        result = command.execute(pid="1234")
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.heap_formatter.format.assert_called_once()

    def test_heap_formatter_success(self):
        """测试heap格式化器成功"""
        command = JmapCommand(self.executor, self.heap_formatter)
        timestamp = datetime.now()
        
        mock_output = """
        using parallel threads in the new generation.
        using thread-local object allocation.
        Concurrent Mark-Sweep GC

        Heap Configuration:
           MinHeapFreeRatio         = 40
           MaxHeapFreeRatio         = 70
           MaxHeapSize             = 2147483648 (2048.0MB)
           NewSize                 = 268435456 (256.0MB)
           MaxNewSize             = 268435456 (256.0MB)
           OldSize                = 1879048192 (1792.0MB)
           NewRatio               = 2
           SurvivorRatio          = 8
           MetaspaceSize          = 21807104 (20.796875MB)
           CompressedClassSpaceSize = 1073741824 (1024.0MB)
           MaxMetaspaceSize      = 17592186044415 MB
           G1HeapRegionSize      = 0 (0.0MB)

        Heap Usage:
        New Generation (Eden + 1 Survivor Space):
           capacity = 241631232 (230.4375MB)
           used     = 77776272 (74.17323303222656MB)
           free     = 163854960 (156.26426696777344MB)
           32.188455772236985% used
        Eden Space:
           capacity = 214827008 (204.875MB)
           used     = 77776272 (74.17323303222656MB)
           free     = 137050736 (130.70176696777344MB)
           36.20447744750976% used
        From Space:
           capacity = 26804224 (25.5625MB)
           used     = 0 (0.0MB)
           free     = 26804224 (25.5625MB)
           0.0% used
        To Space:
           capacity = 26804224 (25.5625MB)
           used     = 0 (0.0MB)
           free     = 26804224 (25.5625MB)
           0.0% used
        concurrent mark-sweep generation:
           capacity = 1879048192 (1792.0MB)
           used     = 0 (0.0MB)
           free     = 1879048192 (1792.0MB)
           0.0% used

        28929 interned Strings occupying 2678432 bytes.
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
        
        self.heap_formatter.format.return_value = expected_result
        
        result = command.execute(pid="1234", operation=JmapOperation.HEAP)
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.heap_formatter.format.assert_called_once()

    def test_histo_formatter_success(self):
        """测试histo格式化器成功"""
        command = JmapCommand(self.executor, self.histo_formatter)
        timestamp = datetime.now()
        
        mock_output = """
         num     #instances         #bytes  class name
        ----------------------------------------------
           1:         38225        5242880  [B
           2:         12200        1024768  java.lang.String
           3:          5000         120000  java.util.HashMap
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
            "histogram": [
                {"instances": 38225, "bytes": 5242880, "class_name": "[B"},
                {"instances": 12200, "bytes": 1024768, "class_name": "java.lang.String"},
                {"instances": 5000, "bytes": 120000, "class_name": "java.util.HashMap"}
            ],
            "total": {"instances": 55425, "bytes": 6387648},
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.histo_formatter.format.return_value = expected_result
        
        result = command.execute(pid="1234", operation=JmapOperation.HISTO)
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.histo_formatter.format.assert_called_once()

    def test_dump_formatter_success(self):
        """测试dump格式化器成功"""
        command = JmapCommand(self.executor, self.dump_formatter)
        timestamp = datetime.now()
        dump_file = "heap.bin"
        file_size = 1024
        
        mock_output = f"""
        Dumping heap to {dump_file} ...
        Heap dump file created
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
            "dump_file": dump_file,
            "file_size": file_size,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.dump_formatter.format.return_value = expected_result
        
        result = command.execute(pid="1234", operation=JmapOperation.DUMP, dump_file=dump_file)
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.dump_formatter.format.assert_called_once()

    def test_formatters_failure(self):
        """测试格式化器失败"""
        command = JmapCommand(self.executor, self.heap_formatter)
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
        
        self.heap_formatter.format.return_value = expected_result
        
        result = command.execute(pid="1234")
        assert result == expected_result
        self.executor.run.assert_called_once()
        self.heap_formatter.format.assert_called_once()

if __name__ == '__main__':
    pytest.main()
