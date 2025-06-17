"""Jmap命令实现"""

import os
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
        if operation == JmapOperation.HEAP:
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
