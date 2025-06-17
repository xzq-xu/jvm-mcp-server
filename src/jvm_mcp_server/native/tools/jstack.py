"""JStack命令实现"""

from typing import Dict, Any, List, Optional
from ..base import BaseCommand, CommandResult, OutputFormatter

class JstackCommand(BaseCommand):
    """JStack命令实现"""

    def __init__(self, executor, formatter):
        super().__init__(executor, formatter)
        self.timeout = 30  # 设置默认超时时间为30秒

    def get_command(self, pid: str, *args, **kwargs) -> str:
        """获取jstack命令

        Args:
            pid: 进程ID

        Returns:
            str: jstack命令字符串
        """
        # -l 选项显示锁信息
        return f'jstack -l {pid}'

class JstackFormatter(OutputFormatter):
    """JStack输出格式化器"""

    def format(self, result: CommandResult) -> Dict[str, Any]:
        """格式化jstack命令输出

        Args:
            result: 命令执行结果

        Returns:
            Dict[str, Any]: 格式化后的结果，包含线程信息
        """
        if not result.success:
            return {
                "success": False,
                "error": result.error,
                "timestamp": result.timestamp.isoformat()
                }

        threads: List[Dict[str, Any]] = []
        current_thread: Optional[Dict[str, Any]] = None
        in_synchronizers = False

        for line in result.output.splitlines():
            line = line.strip()
            if not line:
                continue

            # 新线程的开始
            if line.startswith('"'):
                if current_thread:
                    threads.append(current_thread)

                # 解析线程名和状态
                # 格式: "thread-name" #id [state]
                name_end = line.rfind('"')
                if name_end > 0:
                    thread_name = line[1:name_end]
                    current_thread = {
                        "name": thread_name,
                        "state": "unknown",  # 状态将在下一行更新
                        "stack_trace": [],
                        "locks": []
                        }
                in_synchronizers = False

            # 解析线程状态
            elif line.startswith('java.lang.Thread.State:'):
                if current_thread:
                    current_thread["state"] = line.split(':', 1)[1].strip()
                in_synchronizers = False

            # 同步器信息开始
            elif line.startswith('Locked synchronizers:'):
                in_synchronizers = True
                continue

            # 锁信息
            elif line.startswith('- '):
                if current_thread:
                    if in_synchronizers:
                        if not line.startswith('- None'):  # 跳过 "- None"
                            current_thread["locks"].append(line.strip())
                    elif 'locked' in line or 'waiting to lock' in line or 'parking to wait' in line:
                        current_thread["locks"].append(line.strip())

            # 堆栈信息
            elif line.startswith('at '):
                if current_thread:
                    current_thread["stack_trace"].append(line.strip())
                in_synchronizers = False

        # 添加最后一个线程
        if current_thread:
            threads.append(current_thread)

        return {
            "success": True,
            "threads": threads,
            "thread_count": len(threads),
            "execution_time": result.execution_time,
            "timestamp": result.timestamp.isoformat()
            }
