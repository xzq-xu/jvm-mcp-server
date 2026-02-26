"""Jinfo命令实现"""

from enum import Enum
from typing import Dict, Any, Optional
from ..base import BaseCommand, CommandResult, OutputFormatter

class JinfoOption(Enum):
    FLAGS = "flags"      # JVM 启动参数
    SYSPROPS = "sysprops"  # 系统属性
    ALL = "all"          # 全部信息

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
            # 检测常见错误类型
            error_msg = result.error or ""
            
            # 权限拒绝错误
            if "Permission denied" in error_msg or "Unable to open socket file" in error_msg:
                return {
                    "success": False,
                    "error": f"权限不足: {error_msg}。请确保运行用户与目标Java进程具有相同用户ID，或使用sudo权限运行。",
                    "hint": "解决方案: 1) 使用sudo运行; 2) 以与目标Java进程相同的用户运行; 3) 为JDK添加experimental attach权限",
                    "timestamp": result.timestamp.isoformat()
                }
            # 连接被拒绝/进程不存在
            if "No such process" in error_msg or "Unable to find process" in error_msg:
                return {
                    "success": False,
                    "error": f"进程不存在或已经退出: {error_msg}",
                    "timestamp": result.timestamp.isoformat()
                }
            return {
                "success": False,
                "error": error_msg,
                "timestamp": result.timestamp.isoformat()
            }
        return {
            "success": True,
            "output": result.output,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
        }
    """Jinfo输出格式化器（仅文本输出）"""

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
