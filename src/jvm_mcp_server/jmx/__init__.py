"""JMX 支持模块"""

import os
import subprocess
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class JMXConnection:
    """JMX 连接配置"""
    host: str
    port: int = 9999
    username: Optional[str] = None
    password: Optional[str] = None
    
    @property
    def url(self) -> str:
        """获取 JMX 服务 URL"""
        if self.username and self.password:
            return f"service:jmx:rmi:///jndi/rmi://{self.host}:{self.port}/jmxrmi"
        return f"service:jmx:rmi:///jndi/rmi://{self.host}:{self.port}/jmxrmi"


class JMXClient:
    """JMX 客户端 - 通过 jcmd 间接获取 JMX 数据"""
    
    def __init__(self, host: str = "localhost", port: int = 9999, 
                 pid: Optional[str] = None, ssh_executor=None):
        """
        初始化 JMX 客户端
        
        Args:
            host: 目标主机
            port: JMX 端口
            pid: 进程 ID（如果为 None，则尝试从远程获取）
            ssh_executor: SSH 执行器（用于远程连接）
        """
        self.host = host
        self.port = port
        self.pid = pid
        self.ssh_executor = ssh_executor
    
    def _run_command(self, command: str) -> Dict[str, Any]:
        """运行命令"""
        if self.ssh_executor:
            result = self.ssh_executor.run(command, timeout=30)
        else:
            import subprocess
            completed = subprocess.run(
                command, shell=True, capture_output=True, timeout=30, text=True
            )
            result = type('obj', (object,), {
                'success': completed.returncode == 0,
                'output': completed.stdout,
                'error': completed.stderr if completed.stderr else None
            })()
        return result
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息 - 通过 jcmd GC.heap_info"""
        if not self.pid:
            return {"success": False, "error": "需要指定进程 ID"}
        
        cmd = f"jcmd {self.pid} GC.heap_info"
        result = self._run_command(cmd)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error or "无法获取堆信息",
                "hint": "确保目标 JVM 启用了 JMX 或使用 -XX:+UseGCLogFileRotation"
            }
        
        # 解析 heap info 输出
        return self._parse_heap_info(result.output)
    
    def _parse_heap_info(self, output: str) -> Dict[str, Any]:
        """解析 heap info 输出"""
        lines = output.strip().split('\n')
        data = {
            "success": True,
            "raw_output": output,
            "timestamp": time.time(),
            "segments": []
        }
        
        # 简单的解析 - 尝试提取关键信息
        for line in lines:
            if "eden" in line.lower():
                data["eden"] = line.strip()
            elif "survivor" in line.lower() or "from" in line.lower():
                data["survivor"] = line.strip()
            elif "old" in line.lower():
                data["old_gen"] = line.strip()
            elif "heap" in line.lower():
                data["heap"] = line.strip()
        
        return data
    
    def get_thread_info(self) -> Dict[str, Any]:
        """获取线程信息 - 通过 jcmd Thread.print"""
        if not self.pid:
            return {"success": False, "error": "需要指定进程 ID"}
        
        cmd = f"jcmd {self.pid} Thread.print"
        result = self._run_command(cmd)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error or "无法获取线程信息"
            }
        
        return {
            "success": True,
            "raw_output": result.output,
            "timestamp": time.time()
        }
    
    def get_gc_info(self) -> Dict[str, Any]:
        """获取 GC 信息 - 通过 jcmd GC.class_histogram"""
        if not self.pid:
            return {"success": False, "error": "需要指定进程 ID"}
        
        cmd = f"jcmd {self.pid} GC.class_histogram"
        result = self._run_command(cmd)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error or "无法获取 GC 信息"
            }
        
        return {
            "success": True,
            "raw_output": result.output,
            "timestamp": time.time()
        }
    
    def get_vm_flags(self) -> Dict[str, Any]:
        """获取 VM 标志 - 通过 jcmd VM.flags"""
        if not self.pid:
            return {"success": False, "error": "需要指定进程 ID"}
        
        cmd = f"jcmd {self.pid} VM.flags -all"
        result = self._run_command(cmd)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error or "无法获取 VM 标志"
            }
        
        return {
            "success": True,
            "raw_output": result.output,
            "timestamp": time.time()
        }
    
    def get_system_properties(self) -> Dict[str, Any]:
        """获取系统属性 - 通过 jcmd VM.system_properties"""
        if not self.pid:
            return {"success": False, "error": "需要指定进程 ID"}
        
        cmd = f"jcmd {self.pid} VM.system_properties"
        result = self._run_command(cmd)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error or "无法获取系统属性"
            }
        
        # 解析系统属性
        props = {}
        for line in result.output.split('\n'):
            if '=' in line:
                key, _, value = line.partition('=')
                props[key.strip()] = value.strip()
        
        return {
            "success": True,
            "properties": props,
            "raw_output": result.output,
            "timestamp": time.time()
        }


def create_jmx_client(pid: Optional[str] = None, 
                      ssh_host: Optional[str] = None,
                      ssh_port: int = 22,
                      ssh_user: Optional[str] = None,
                      ssh_password: Optional[str] = None,
                      ssh_key: Optional[str] = None) -> JMXClient:
    """创建 JMX 客户端工厂函数"""
    ssh_executor = None
    
    if ssh_host:
        from ..native.base import NativeCommandExecutor
        ssh_executor = NativeCommandExecutor(
            ssh_host=ssh_host,
            ssh_port=ssh_port,
            ssh_user=ssh_user,
            ssh_password=ssh_password,
            ssh_key=ssh_key
        )
    
    return JMXClient(
        host="localhost" if not ssh_host else ssh_host,
        pid=pid,
        ssh_executor=ssh_executor
    )
