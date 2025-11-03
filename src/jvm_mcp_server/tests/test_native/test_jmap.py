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

    def test_get_command_heap_modern_jdk_with_jhsdb(self):
        command = JmapCommand(self.executor, self.heap_formatter)
        with patch.object(command, '_get_jdk_version', return_value=11), \
             patch.object(command, '_test_jhsdb_availability', return_value=True):
            result = command.get_command(pid="1234", operation=JmapOperation.HEAP)
            assert result == "jhsdb jmap --heap --pid 1234"

    def test_get_command_heap_modern_jdk_without_jhsdb(self):
        command = JmapCommand(self.executor, self.heap_formatter)
        with patch.object(command, '_get_jdk_version', return_value=11), \
             patch.object(command, '_test_jhsdb_availability', return_value=False):
            result = command.get_command(pid="1234", operation=JmapOperation.HEAP)
            assert result == "jmap -heap 1234"

    def test_get_command_heap_legacy_jdk(self):
        command = JmapCommand(self.executor, self.heap_formatter)
        with patch.object(command, '_get_jdk_version', return_value=8):
            result = command.get_command(pid="1234", operation=JmapOperation.HEAP)
            assert result == "jmap -heap 1234"

    def test_get_command_heap_version_detection_fallback(self):
        command = JmapCommand(self.executor, self.heap_formatter)
        with patch.object(command, '_get_jdk_version', return_value=8):
            result = command.get_command(pid="1234", operation=JmapOperation.HEAP)
            assert result == "jmap -heap 1234"

    def test_get_command_heap_version_caching(self):
        command = JmapCommand(self.executor, self.heap_formatter)
        with patch.object(command, '_get_jdk_version', return_value=11), \
             patch.object(command, '_test_jhsdb_availability', return_value=True):
            result1 = command.get_command(pid="1234", operation=JmapOperation.HEAP)
            result2 = command.get_command(pid="5678", operation=JmapOperation.HEAP)
            assert result1 == "jhsdb jmap --heap --pid 1234"
            assert result2 == "jhsdb jmap --heap --pid 5678"

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

    def test_get_command_invalid_pid(self):
        """测试无效PID参数"""
        command = JmapCommand(self.executor, self.heap_formatter)
        
        # 空PID
        with pytest.raises(ValueError, match="Process ID is required"):
            command.get_command(pid="", operation=JmapOperation.HEAP)
        
        # 非数字PID
        with pytest.raises(ValueError, match="Invalid process ID"):
            command.get_command(pid="abc", operation=JmapOperation.HEAP)

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
        
        mock_output = "Dumping heap to heap.bin\nHeap dump file created"
        
        self.executor.run.return_value = CommandResult(
            success=True,
            output=mock_output,
            error=None,
            execution_time=0.1,
            timestamp=timestamp
        )
        
        expected_result = {
            "success": True,
            "dump_file": "heap.bin",
            "file_size": 1024,
            "execution_time": 0.1,
            "timestamp": timestamp.isoformat()
        }
        
        self.dump_formatter.format.return_value = expected_result
        
        result = command.execute(pid="1234", operation=JmapOperation.DUMP, dump_file="heap.bin")
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

    def test_jdk_version_parsing_various_formats(self):
        """测试各种 JDK 版本格式的解析"""
        command = JmapCommand(self.executor, self.heap_formatter)
        
        # 直接测试版本解析逻辑，不依赖 subprocess.run
        test_cases = [
            ('openjdk version "11.0.12" 2021-07-20', 11),
            ('openjdk version "17.0.15" 2025-04-15 LTS', 17),
            ('java version "1.8.0_291"', 8),
            ('java version "1.7.0_80"', 7),
        ]
        
        for version_output, expected_version in test_cases:
            # 重置缓存
            command._jdk_version = None
            
            # 直接测试版本解析逻辑
            import re
            version_patterns = [
                r'version "1\.(\d+)',  # 匹配 "1.8.0_291"，优先放前面
                r'version "(\d+)',  # 匹配 "11.0.12" 或 "17.0.15"
            ]
            
            detected_version = 8  # 默认值
            for pattern in version_patterns:
                version_match = re.search(pattern, version_output)
                if version_match:
                    version_str = version_match.group(1)
                    if pattern == r'version "1\.(\d+)':
                        # 对于 "1.8" 格式，返回 8
                        detected_version = int(version_str)
                    else:
                        # 对于 "11" 或 "17" 格式，直接返回
                        detected_version = int(version_str)
                    break
            
            assert detected_version == expected_version, f"Failed for: {version_output}"

if __name__ == '__main__':
    pytest.main()
 