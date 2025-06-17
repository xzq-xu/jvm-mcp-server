"""Jstat命令实现"""

from typing import Dict, Any, Optional
from ..base import BaseCommand, CommandResult, OutputFormatter

class JstatCommand(BaseCommand):
    """Jstat命令实现"""

    def __init__(self, executor, formatter):
        super().__init__(executor, formatter)
        self.timeout = 30

    def get_command(
            self,
            pid: str,
            option: Optional[str] = None,
            interval: Optional[int] = None,
            count: Optional[int] = None,
            *args,
            **kwargs) -> str:
        # option: gc, gccapacity, class, compiler, util, ...
        cmd = f'jstat'
        if option:
            cmd += f' -{option}'
        cmd += f' {pid}'
        if interval is not None:
            cmd += f' {interval}'
            if count is not None:
                cmd += f' {count}'
        return cmd

class JstatFormatter(OutputFormatter):
    """Jstat输出格式化器（仅文本输出）"""

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
