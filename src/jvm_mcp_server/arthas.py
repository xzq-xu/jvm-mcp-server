"""Arthas客户端实现"""

import subprocess
import os
import time
import telnetlib
import socket
from typing import Optional, Dict

class ArthasClient:
    """Arthas客户端封装类"""
    def __init__(self, telnet_port: int = 3658):
        self.arthas_boot_path = "arthas-boot.jar"
        self.telnet_port = telnet_port
        self.telnet = None
        self.attached_pid = None
        self._download_arthas()
        
    def _download_arthas(self):
        """下载Arthas启动器"""
        if not os.path.exists(self.arthas_boot_path):
            subprocess.run(
                ["curl", "-o", self.arthas_boot_path, "https://arthas.aliyun.com/arthas-boot.jar"],
                check=True
            )

    def _attach_to_process(self, pid: int):
        """连接到指定的Java进程"""
        if self.attached_pid == pid and self.telnet and self._check_connection():
            return
        
        # 如果已经连接到其他进程，先断开
        self._disconnect()
        
        # 启动Arthas并连接到目标进程
        subprocess.Popen(
            ["java", "-jar", self.arthas_boot_path, 
             "--target-ip", "127.0.0.1",
             "--telnet-port", str(self.telnet_port),
             "--arthas-port", str(self.telnet_port + 1),
             str(pid)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待Arthas启动
        time.sleep(5)
        
        # 建立telnet连接
        try:
            self.telnet = telnetlib.Telnet("127.0.0.1", self.telnet_port, timeout=10)
            self.attached_pid = pid
            # 等待提示符
            self.telnet.read_until(b"$", timeout=10)
        except (socket.error, EOFError) as e:
            print(f"连接Arthas失败: {e}")
            self._disconnect()
            raise

    def _check_connection(self) -> bool:
        """检查telnet连接是否有效"""
        if not self.telnet:
            return False
        try:
            self.telnet.write(b"\n")
            self.telnet.read_until(b"$", timeout=1)
            return True
        except (socket.error, EOFError):
            return False

    def _disconnect(self):
        """断开与Arthas的连接"""
        if self.telnet:
            try:
                self.telnet.write(b"stop\n")
                self.telnet.close()
            except (socket.error, EOFError):
                pass
            finally:
                self.telnet = None
                self.attached_pid = None

    def _execute_command(self, pid: int, command: str) -> str:
        """执行Arthas命令"""
        try:
            self._attach_to_process(pid)
            
            # 发送命令
            self.telnet.write(command.encode() + b"\n")
            
            # 读取响应直到下一个提示符
            response = self.telnet.read_until(b"$", timeout=10)
            
            # 处理响应
            result = response.decode('utf-8')
            # 移除命令回显和提示符
            lines = result.split('\n')
            return '\n'.join(lines[1:-1])  # 去掉第一行（命令回显）和最后一行（提示符）
            
        except (socket.error, EOFError) as e:
            print(f"执行命令失败: {e}")
            self._disconnect()
            raise

    def __del__(self):
        """析构函数，确保断开连接"""
        self._disconnect()

    def get_thread_info(self, pid: int) -> str:
        """获取线程信息"""
        return self._execute_command(pid, "thread")

    def get_jvm_info(self, pid: int) -> str:
        """获取JVM信息"""
        return self._execute_command(pid, "jvm")

    def get_memory_info(self, pid: int) -> str:
        """获取内存信息"""
        return self._execute_command(pid, "memory")

    def get_stack_trace(self, pid: int, thread_name: str) -> str:
        """获取线程堆栈"""
        return self._execute_command(pid, f"thread {thread_name}")

    def get_class_info(self, pid: int, class_pattern: str) -> str:
        """获取类信息"""
        return self._execute_command(pid, f"sc {class_pattern}")

    def list_java_processes(self) -> str:
        """列出Java进程"""
        result = subprocess.run(["jps", "-l", "-v"], capture_output=True, text=True)
        return result.stdout 