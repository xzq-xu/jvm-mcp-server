"""Jmap命令实现"""

import os
import subprocess
import re
from enum import Enum
from typing import Dict, Any, List, Optional
from ..base import BaseCommand, CommandResult, OutputFormatter

class JmapOperation(Enum):
    """Jmap操作类型"""
    HEAP = "heap"  # 堆内存概要
    HISTO = "histo"  # 堆内存直方图
    DUMP = "dump"  # 堆内存转储

class JmapCommand(BaseCommand):
    """Jmap命令实现"""

    def __init__(self, executor, formatter):
        super().__init__(executor, formatter)
        self.timeout = 60  # 设置默认超时时间为60秒
        self._jdk_version = None  # 缓存 JDK 版本

    def _get_jdk_version(self) -> int:
        """获取 JDK 主版本号"""
        if self._jdk_version is not None:
            return self._jdk_version
        
        try:
            # 检查是否为远程执行器
            from ..base import NativeCommandExecutor
            if isinstance(self.executor, NativeCommandExecutor) and self.executor.ssh_host:
                # 远程执行 java -version
                result = self.executor.run('java -version', timeout=10)
                version_output = result.error if result.error else result.output
            else:
                # 本地执行
                result = subprocess.run(['java', '-version'], 
                                      capture_output=True, text=True, timeout=10)
                version_output = result.stderr  # java -version 输出到 stderr
            
            # 解析版本号，支持多种格式
            # 格式1: "openjdk version "11.0.12" 2021-07-20"
            # 格式2: "java version "1.8.0_291""
            # 格式3: "openjdk version "17.0.15" 2025-04-15 LTS"
            version_patterns = [
                r'version "1\.(\d+)',  # 匹配 "1.8.0_291"，优先放前面
                r'version "(\d+)',  # 匹配 "11.0.12" 或 "17.0.15"
            ]
            
            for pattern in version_patterns:
                version_match = re.search(pattern, version_output)
                if version_match:
                    version_str = version_match.group(1)
                    if pattern == r'version "1\.(\d+)':
                        # 对于 "1.8" 格式，返回 8
                        self._jdk_version = int(version_str)
                    else:
                        # 对于 "11" 或 "17" 格式，直接返回
                        self._jdk_version = int(version_str)
                    break
            else:
                # 如果无法解析，假设是低版本
                self._jdk_version = 8
                
        except Exception as e:
            # 如果无法获取版本，假设是低版本
            self._jdk_version = 8
        
        return self._jdk_version

    def _is_modern_jdk(self) -> bool:
        """判断是否为现代 JDK (9+)"""
        return self._get_jdk_version() >= 9

    def _test_jhsdb_availability(self) -> bool:
        """测试 jhsdb 命令是否可用"""
        try:
            from ..base import NativeCommandExecutor
            if isinstance(self.executor, NativeCommandExecutor) and self.executor.ssh_host:
                # 远程测试
                result = self.executor.run('jhsdb --help', timeout=5)
                return result.success
            else:
                # 本地测试
                result = subprocess.run(['jhsdb', '--help'], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
        except Exception:
            return False

    def get_command(self, pid: str, operation: JmapOperation = JmapOperation.HEAP,
                    dump_file: Optional[str] = None, live_only: bool = False,
                    *args, **kwargs) -> str:
        """获取jmap命令

        Args:
            pid: 进程ID
            operation: 操作类型
            dump_file: 转储文件路径（仅在dump操作时需要）
            live_only: 是否只统计存活对象

        Returns:
            str: jmap命令字符串
        """
        # 验证 pid 参数
        if not pid or not pid.strip():
            raise ValueError("Process ID is required")
        
        try:
            int(pid)  # 验证 pid 是否为有效数字
        except ValueError:
            raise ValueError(f"Invalid process ID: {pid}")
        
        if operation == JmapOperation.HEAP:
            # 对于现代 JDK，优先尝试 jhsdb，如果不可用则回退到传统 jmap
            if self._is_modern_jdk() and self._test_jhsdb_availability():
                return f'jhsdb jmap --heap --pid {pid}'
            else:
                return f'jmap -heap {pid}'
        elif operation == JmapOperation.HISTO:
            live_flag = " -live" if live_only else ""
            return f'jmap -histo{live_flag} {pid}'
        elif operation == JmapOperation.DUMP:
            if not dump_file:
                raise ValueError("dump_file is required for dump operation")
            live_flag = ":live" if live_only else ""
            return f'jmap -dump:format=b{live_flag},file={dump_file} {pid}'
        else:
            raise ValueError(f"Unsupported operation: {operation}")

class JmapHeapFormatter(OutputFormatter):
    """Jmap堆内存概要格式化器（仅文本输出）"""

    def format(self, result: CommandResult) -> Dict[str, Any]:
        if not result.success:
            return {
                "success": False,
                "error": result.error,
                "timestamp": result.timestamp.isoformat()
                }
        return {
            "success": True,
            "output": result.output,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
            }

class JmapHistoFormatter(OutputFormatter):
    """Jmap堆内存直方图格式化器"""

    def format(self, result: CommandResult) -> Dict[str, Any]:
        """格式化堆内存直方图输出

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

        histogram: List[Dict[str, Any]] = []
        total = {"instances": 0, "bytes": 0}

        for line in result.output.splitlines():
            line = line.strip()
            if not line or line.startswith('Total') or line.startswith('Num'):
                continue

            # 解析直方图行
            # 格式：序号 实例数 字节数 类名
            parts = line.split()
            if len(parts) >= 4:
                try:
                    instances = int(parts[1])
                    bytes_used = int(parts[2])
                    class_name = ' '.join(parts[3:])

                    histogram.append({
                        "instances": instances,
                        "bytes": bytes_used,
                        "class_name": class_name
                        })

                    total["instances"] += instances
                    total["bytes"] += bytes_used
                except (ValueError, IndexError):
                    continue

        return {
            "success": True,
            "histogram": histogram,
            "total": total,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
            }

class JmapDumpFormatter(OutputFormatter):
    """Jmap堆内存转储格式化器"""

    def format(self, result: CommandResult) -> Dict[str, Any]:
        """格式化堆内存转储输出

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

        # 检查转储文件是否成功创建
        dump_file = None
        for line in result.output.splitlines():
            if "Dumping heap to" in line:
                dump_file = line.split("Dumping heap to")[-1].strip().split()[0]  # 获取第一个词作为文件路径
                break

        return {
            "success": True,
            "dump_file": dump_file,
            "file_size": os.path.getsize(dump_file) if dump_file and os.path.exists(dump_file) else None,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
            }
 