"""Jcmd命令实现"""

from typing import Dict, Any, Optional
from ..base import BaseCommand, CommandResult, OutputFormatter

class JcmdCommand(BaseCommand):
    """Jcmd命令实现"""

    def __init__(self, executor, formatter):
        super().__init__(executor, formatter)
        self.timeout = 30

    def get_command(self, pid: str, subcommand: Optional[str] = None, *args, **kwargs) -> str:
        if subcommand:
            return f'jcmd {pid} {subcommand}'
        else:
            return f'jcmd {pid}'

class JcmdFormatter(OutputFormatter):
    """Jcmd输出格式化器（仅文本输出）"""

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
