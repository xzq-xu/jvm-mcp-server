"""Jinfo命令实现"""

from enum import Enum
from typing import Dict, Any, Optional
from ..base import BaseCommand, CommandResult, OutputFormatter


class JinfoOption(Enum):
    FLAGS = "flags"      # JVM 启动参数
    SYSPROPS = "sysprops"  # 系统属性
    ALL = "all"          # 全部信息


def _format_error(result: CommandResult) -> Dict[str, Any]:
    """统一的错误格式化处理"""
    error_msg = result.error or ""
    
    # 权限拒绝错误 (包括各种平台的错误消息)
    permission_patterns = [
        "Permission denied",
        "Unable to open socket file",
        "Can't attach",
        "operation not permitted",
        "Operation not permitted",
        "task_for_pid",
        "Unable to attach",
        "DebuggerException",
    ]
    
    if any(pattern in error_msg for pattern in permission_patterns):
        return {
            "success": False,
            "error": f"权限不足: {error_msg[:500]}..." if len(error_msg) > 500 else f"权限不足: {error_msg}",
            "hint": "解决方案: 1) 使用sudo运行; 2) 以与目标Java进程相同的用户运行; 3) macOS上需要关闭SIP或使用lldb附加调试器权限",
            "timestamp": result.timestamp.isoformat()
        }
    # 连接被拒绝/进程不存在
    if "No such process" in error_msg or "Unable to find process" in error_msg:
        return {
            "success": False,
            "error": f"进程不存在或已经退出: {error_msg[:200]}",
            "timestamp": result.timestamp.isoformat()
        }
    return {
        "success": False,
        "error": error_msg[:500] if len(error_msg) > 500 else error_msg,
        "timestamp": result.timestamp.isoformat()
    }


class JinfoCommand(BaseCommand):
    """Jinfo命令实现"""

    def __init__(self, executor, formatter):
        super().__init__(executor, formatter)
        self.timeout = 30

    def get_command(self, pid: str, option: JinfoOption = JinfoOption.ALL, *args, **kwargs) -> str:
        if option == JinfoOption.FLAGS:
            return f'jinfo -flags {pid}'
        elif option == JinfoOption.SYSPROPS:
            return f'jinfo -sysprops {pid}'
        else:
            return f'jinfo {pid}'


class JinfoFormatter(OutputFormatter):
    """Jinfo输出格式化器（仅文本输出）"""

    def format(self, result: CommandResult) -> Dict[str, Any]:
        if not result.success:
            return _format_error(result)
        return {
            "success": True,
            "output": result.output,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
        }
