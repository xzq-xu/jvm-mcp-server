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
