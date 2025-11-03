"""JPS命令实现"""

from typing import Dict, Any, List
from ..base import BaseCommand, CommandResult, OutputFormatter

class JpsCommand(BaseCommand):
    """JPS命令实现"""

    def get_command(self, *args, **kwargs) -> str:
        """获取jps命令

        Returns:
            str: jps命令字符串
        """
        # 使用 -l 显示完整的包名，-v 显示JVM参数
        return 'jps -l -v'

class JpsFormatter(OutputFormatter):
    """JPS输出格式化器"""

    def format(self, result: CommandResult) -> Dict[str, Any]:
        """格式化jps命令输出

        Args:
            result: 命令执行结果

        Returns:
            Dict[str, Any]: 格式化后的结果，包含进程列表
        """
        processes: List[Dict[str, str]] = []

        for line in result.output.splitlines():
            if line.strip():
                # jps输出格式：<pid> <class> <jvm args>
                parts = line.split(None, 2)
                # 确保至少有 pid 和 class 两个部分
                if len(parts) >= 2 and parts[0].isdigit():
                    process = {
                        "pid": parts[0],
                        "name": parts[1],
                        "args": parts[2] if len(parts) > 2 else ""
                        }
                    processes.append(process)

        return {
            "success": result.success,
            "processes": processes,
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
            }
