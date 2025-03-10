from mcp.server.fastmcp import FastMCP
import subprocess
import json
import time
import os
import telnetlib
import socket
from typing import List, Dict, Optional



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


# 创建MCP服务器实例
MCP_SERVER_NAME = "arthas-jvm-monitor"
mcp = FastMCP(MCP_SERVER_NAME)
arthas_client = ArthasClient()

@mcp.tool()
def list_java_processes() -> List[Dict[str, str]]:
    """列出所有Java进程"""
    result = subprocess.run(["jps", "-l", "-v"], capture_output=True, text=True)
    processes = []
    for line in result.stdout.splitlines():
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                processes.append({
                    "pid": parts[0],
                    "name": parts[1],
                    "args": " ".join(parts[2:]) if len(parts) > 2 else ""
                })
    return processes

@mcp.tool()
def get_thread_info(pid: int) -> Dict:
    """获取指定进程的线程信息"""
    output = arthas_client._execute_command(pid, "thread")
    # 解析输出并返回结构化数据
    return {
        "raw_output": output,
        "timestamp": time.time()
    }

@mcp.tool()
def get_jvm_info(pid: int) -> Dict:
    """获取JVM基础信息"""
    output = arthas_client._execute_command(pid, "jvm")
    return {
        "raw_output": output,
        "timestamp": time.time()
    }

@mcp.tool()
def get_memory_info(pid: int) -> Dict:
    """获取内存使用情况"""
    output = arthas_client._execute_command(pid, "memory")
    return {
        "raw_output": output,
        "timestamp": time.time()
    }

@mcp.tool()
def get_stack_trace(pid: int, thread_name: str) -> Dict:
    """获取指定线程的堆栈信息"""
    command = f"thread {thread_name}"
    output = arthas_client._execute_command(pid, command)
    return {
        "raw_output": output,
        "timestamp": time.time()
    }

@mcp.tool()
def get_class_info(pid: int, class_pattern: str) -> Dict:
    """获取类信息"""
    command = f"sc {class_pattern}"
    output = arthas_client._execute_command(pid, command)
    return {
        "raw_output": output,
        "timestamp": time.time()
    }

@mcp.tool()
def get_jvm_status(pid: Optional[int] = None) -> Dict:
    """获取JVM整体状态报告
    
    Args:
        pid: 可选的进程ID，如果不指定则自动选择第一个非arthas的Java进程
    
    Returns:
        包含JVM状态信息的字典
    """
    if pid is None:
        # 如果没有指定PID，获取第一个非arthas的Java进程
        processes = list_java_processes()
        for process in processes:
            if "arthas" not in process["name"].lower():
                pid = int(process["pid"])
                break
        if pid is None:
            return {"error": "No valid Java process found"}

    thread_info = get_thread_info(pid)
    jvm_info = get_jvm_info(pid)
    memory_info = get_memory_info(pid)
    
    return {
        "pid": pid,
        "thread_info": thread_info,
        "jvm_info": jvm_info,
        "memory_info": memory_info,
        "timestamp": time.time()
    }

# @mcp.prompt()
def jvm_analysis_prompt() -> str:
    """创建JVM分析提示"""
    # 获取默认JVM进程的状态
    status = get_jvm_status()
    status_json = json.dumps(status, indent=2)
    
    return f"""你是一位经验丰富的Java性能调优专家，请基于以下JVM状态数据进行分析：

{status_json}

请考虑以下方面：
1. JVM整体健康状况
2. 内存使用情况和潜在的内存问题
3. 线程状态和可能的死锁
4. 性能优化建议
5. 需要关注的警告信息

请提供详细的分析报告和具体的优化建议。
"""

if __name__ == "__main__":
    print(f"Starting {MCP_SERVER_NAME}...")
    mcp.run() 