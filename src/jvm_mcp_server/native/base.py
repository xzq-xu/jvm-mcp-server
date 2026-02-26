"""JVM MCP Server Native 基础命令执行框架"""

import logging
import subprocess
import paramiko
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
            }

class CommandExecutor(ABC):
    """命令执行器基类"""

    @abstractmethod
    def run(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """执行命令

        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）

        Returns:
            CommandResult: 命令执行结果
        """
        pass

class NativeCommandExecutor(CommandExecutor):
    """
    支持本地、远程（SSH）和Kubernetes（kubectl exec）命令执行的通用执行器。
    Universal executor supporting local, remote (SSH), and Kubernetes (kubectl exec) execution.

    执行优先级 / Execution priority: Kubernetes > SSH > Local
    """

    def __init__(
            self,
            # SSH参数 / SSH parameters
            ssh_host: Optional[str] = None,
            ssh_port: int = 22,
            ssh_user: Optional[str] = None,
            ssh_password: Optional[str] = None,
            ssh_key: Optional[str] = None,
            # Kubernetes参数 / Kubernetes parameters
            kube_context: Optional[str] = None,
            kube_namespace: Optional[str] = None,
            kube_pod: Optional[str] = None,
            kube_container: Optional[str] = None):
        # SSH配置
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_key = ssh_key
        # Kubernetes配置
        self.kube_context = kube_context
        self.kube_namespace = kube_namespace
        self.kube_pod = kube_pod
        self.kube_container = kube_container

    def _build_kubectl_command(self, command: str) -> str:
        """构建kubectl exec命令 / Build kubectl exec command

        Args:
            command: 要在pod中执行的命令 / Command to execute in pod

        Returns:
            str: 完整的kubectl exec命令 / Complete kubectl exec command
        """
        kubectl_parts = ['kubectl']

        if self.kube_context:
            kubectl_parts.extend(['--context', self.kube_context])

        if self.kube_namespace:
            kubectl_parts.extend(['--namespace', self.kube_namespace])

        kubectl_parts.extend(['exec', self.kube_pod])

        if self.kube_container:
            kubectl_parts.extend(['--container', self.kube_container])

        kubectl_parts.extend(['--', 'sh', '-c', command])

        return kubectl_parts

    def run(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        start = datetime.now()

        # 优先级1: Kubernetes执行 / Priority 1: Kubernetes execution
        if self.kube_pod:
            try:
                kubectl_cmd = self._build_kubectl_command(command)
                logger.debug(f"Executing kubectl command: {' '.join(kubectl_cmd)}")

                completed = subprocess.run(
                    kubectl_cmd,
                    capture_output=True,
                    timeout=timeout,
                    text=True
                )
                success = (completed.returncode == 0)
                return CommandResult(
                    success,
                    completed.stdout,
                    completed.stderr if completed.stderr else None,
                    (datetime.now()-start).total_seconds(),
                    datetime.now())
            except subprocess.TimeoutExpired:
                return CommandResult(False, '', f'kubectl exec timeout after {timeout}s',
                                     (datetime.now()-start).total_seconds(), datetime.now())
            except Exception as e:
                return CommandResult(False, '', str(e), (datetime.now()-start).total_seconds(), datetime.now())

        # 优先级2: SSH远程执行 / Priority 2: SSH remote execution
        elif self.ssh_host:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if self.ssh_key:
                    ssh.connect(
                        self.ssh_host,
                        port=self.ssh_port,
                        username=self.ssh_user,
                        key_filename=self.ssh_key,
                        timeout=timeout)
                else:
                    ssh.connect(
                        self.ssh_host,
                        port=self.ssh_port,
                        username=self.ssh_user,
                        password=self.ssh_password,
                        timeout=timeout)
                stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
                output = stdout.read().decode(errors='ignore')
                error = stderr.read().decode(errors='ignore')
                ssh.close()
                success = (not error.strip())
                return CommandResult(success, output, error if error.strip() else None,
                                     (datetime.now()-start).total_seconds(), datetime.now())
            except Exception as e:
                return CommandResult(False, '', str(e), (datetime.now()-start).total_seconds(), datetime.now())

        # 优先级3: 本地执行 / Priority 3: Local execution
        else:
            try:
                completed = subprocess.run(command, shell=True, capture_output=True, timeout=timeout, text=True)
                success = (completed.returncode == 0)
                return CommandResult(
                    success,
                    completed.stdout,
                    completed.stderr if completed.stderr else None,
                    (datetime.now()-start).total_seconds(),
                    datetime.now())
            except Exception as e:
                return CommandResult(False, '', str(e), (datetime.now()-start).total_seconds(), datetime.now())

class OutputFormatter(ABC):
    """输出格式化器基类"""

    @abstractmethod
    def format(self, result: CommandResult) -> Dict[str, Any]:
        """格式化命令执行结果

        Args:
            result: 命令执行结果

        Returns:
            Dict[str, Any]: 格式化后的结果
        """
        pass

class BaseCommand(ABC):
    """基础命令类"""

    def __init__(self, executor: CommandExecutor, formatter: OutputFormatter):
        """初始化

        Args:
            executor: 命令执行器
            formatter: 输出格式化器
        """
        self.executor = executor
        self.formatter = formatter
        self.timeout = None  # 默认无超时

    def set_timeout(self, timeout: int):
        """设置命令执行超时时间

        Args:
            timeout: 超时时间（秒）
        """
        self.timeout = timeout

    @abstractmethod
    def get_command(self, *args, **kwargs) -> str:
        """获取要执行的命令

        Returns:
            str: 命令字符串
        """
        pass

    def pre_execute(self, *args, **kwargs):
        """命令执行前的钩子"""
        pass

    def post_execute(self, result: CommandResult, *args, **kwargs):
        """命令执行后的钩子"""
        pass

    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """执行命令

        Returns:
            Dict[str, Any]: 格式化后的执行结果
        """
        try:
            self.pre_execute(*args, **kwargs)

            command = self.get_command(*args, **kwargs)
            result = self.executor.run(command, timeout=self.timeout)

            self.post_execute(result, *args, **kwargs)

            if not result.success:
                logger.error(f"Command execution failed: {result.error}")
            # 无论成功与否都调用 formatter
            return self.formatter.format(result)

        except Exception as e:
            logger.exception("Command execution failed with exception")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
                }

class CommandFactory:
    """命令工厂类"""

    def __init__(self):
        self._executors = {}
        self._formatters = {}

    def register_executor(self, name: str, executor: CommandExecutor):
        """注册命令执行器"""
        self._executors[name] = executor

    def register_formatter(self, name: str, formatter: OutputFormatter):
        """注册输出格式化器"""
        self._formatters[name] = formatter

    def get_executor(self, name: str) -> CommandExecutor:
        """获取命令执行器"""
        if name not in self._executors:
            raise ValueError(f"Executor '{name}' not found")
        return self._executors[name]

    def get_formatter(self, name: str) -> OutputFormatter:
        """获取输出格式化器"""
        if name not in self._formatters:
            raise ValueError(f"Formatter '{name}' not found")
        return self._formatters[name]

    def create_command(self, command_class, executor_name: str, formatter_name: str):
        """创建命令实例"""
        executor = self.get_executor(executor_name)
        formatter = self.get_formatter(formatter_name)
        return command_class(executor, formatter)
 