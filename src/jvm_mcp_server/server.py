"""JVM MCP Server实现"""

import json
import time
import os
from typing import List, Dict, Optional

from mcp.server.fastmcp import FastMCP
from .arthas import ArthasClient

class JvmMcpServer:
    """JVM MCP服务器"""
    def __init__(self, name: str = "arthas-jvm-monitor"):
        """
        初始化JVM MCP服务器
        Args:
            name: 服务器名称
        
        Environment Variables:
            ARTHAS_SSH_HOST: SSH连接地址，格式为 user@host，不存在则表示本地连接
            ARTHAS_SSH_PORT: SSH端口，默认22
            ARTHAS_SSH_PASSWORD: SSH密码，不存在则使用密钥认证
        """
        self.name = name
        self.mcp = FastMCP(name)
        
        # 从环境变量读取SSH连接参数
        ssh_host = os.getenv('ARTHAS_SSH_HOST')
        ssh_port = int(os.getenv('ARTHAS_SSH_PORT', '22'))
        ssh_password = os.getenv('ARTHAS_SSH_PASSWORD')
        
        self.arthas = ArthasClient(
            ssh_host=ssh_host,
            ssh_port=ssh_port,
            ssh_password=ssh_password
        )
        self._setup_tools()

    def _setup_tools(self):
        """设置MCP工具"""
        @self.mcp.tool()
        def list_java_processes() -> List[Dict[str, str]]:
            """列出所有Java进程"""
            output = self.arthas.list_java_processes()
            processes = []
            for line in output.splitlines():
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append({
                            "pid": parts[0],
                            "name": parts[1],
                            "args": " ".join(parts[2:]) if len(parts) > 2 else ""
                        })
            return processes

        @self.mcp.tool()
        def get_thread_info(pid: int) -> Dict:
            """获取指定进程的线程信息"""
            output = self.arthas.get_thread_info(pid)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_jvm_info(pid: int) -> Dict:
            """获取JVM基础信息"""
            output = self.arthas.get_jvm_info(pid)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_memory_info(pid: int) -> Dict:
            """获取内存使用情况"""
            output = self.arthas.get_memory_info(pid)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_stack_trace(pid: int, thread_id: int = None, top_n: int = None,
                          find_blocking: bool = False, interval: int = None,
                          show_all: bool = False) -> Dict:
            """获取线程堆栈信息
            
            Args:
                pid: 进程ID
                thread_id: 线程ID，如果指定则只显示该线程的堆栈
                top_n: 显示最忙的前N个线程
                find_blocking: 是否查找阻塞其他线程的线程
                interval: CPU使用率统计的采样间隔(毫秒)，默认200ms
                show_all: 是否显示所有线程
            """
            output = self.arthas.get_stack_trace(
                pid=pid,
                thread_id=thread_id,
                top_n=top_n,
                find_blocking=find_blocking,
                interval=interval,
                show_all=show_all
            )
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_class_info(pid: int, class_pattern: str,
                          show_detail: bool = False,
                          show_field: bool = False,
                          use_regex: bool = False,
                          depth: int = None,
                          classloader_hash: str = None,
                          classloader_class: str = None,
                          max_matches: int = None) -> Dict:
            """获取类信息
            
            Args:
                pid: 进程ID
                class_pattern: 类名表达式匹配
                show_detail: 是否显示详细信息，默认false
                show_field: 是否显示成员变量信息(需要show_detail=True)，默认false
                use_regex: 是否使用正则表达式匹配，默认false
                depth: 指定输出静态变量时属性的遍历深度，默认1
                classloader_hash: 指定class的ClassLoader的hashcode，默认None
                classloader_class: 指定执行表达式的ClassLoader的class name，默认None
                max_matches: 具有详细信息的匹配类的最大数量
            """
            output = self.arthas.get_class_info(
                pid=pid,
                class_pattern=class_pattern,
                show_detail=show_detail,
                show_field=show_field,
                use_regex=use_regex,
                depth=depth,
                classloader_hash=classloader_hash,
                classloader_class=classloader_class,
                max_matches=max_matches
            )
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_jvm_status(pid: int) -> Dict:
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

        @self.mcp.tool()
        def get_version(pid: int) -> Dict:
            """获取Arthas版本信息"""
            output = self.arthas.get_version(pid)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_stack_trace_by_method(pid: int, class_pattern: str, method_pattern: str,
                                    condition: str = None,
                                    use_regex: bool = False,
                                    max_matches: int = None,
                                    max_times: int = None) -> Dict:
            """获取方法的调用路径
            
            Args:
                pid: 进程ID
                class_pattern: 类名表达式匹配
                method_pattern: 方法名表达式匹配
                condition: 条件表达式，例如：'params[0]<0' 或 '#cost>10'
                use_regex: 是否开启正则表达式匹配，默认为通配符匹配
                max_matches: 指定Class最大匹配数量，默认值为50
                max_times: 执行次数限制
            """
            output = self.arthas.get_stack_trace_by_method(
                pid=pid,
                class_pattern=class_pattern,
                method_pattern=method_pattern,
                condition=condition,
                use_regex=use_regex,
                max_matches=max_matches,
                max_times=max_times
            )
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def decompile_class(pid: int, class_pattern: str, method_pattern: str = None) -> Dict:
            """反编译指定类的源码"""
            output = self.arthas.decompile_class(pid, class_pattern, method_pattern)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def search_method(pid: int, class_pattern: str, method_pattern: str = None,
                         show_detail: bool = False,
                         use_regex: bool = False,
                         classloader_hash: str = None,
                         classloader_class: str = None,
                         max_matches: int = None) -> Dict:
            """查看类的方法信息
            
            Args:
                pid: 进程ID
                class_pattern: 类名表达式匹配
                method_pattern: 可选的方法名表达式
                show_detail: 是否展示每个方法的详细信息
                use_regex: 是否开启正则表达式匹配，默认为通配符匹配
                classloader_hash: 指定class的ClassLoader的hashcode
                classloader_class: 指定执行表达式的ClassLoader的class name
                max_matches: 具有详细信息的匹配类的最大数量（默认为100）
            """
            output = self.arthas.search_method(
                pid=pid,
                class_pattern=class_pattern,
                method_pattern=method_pattern,
                show_detail=show_detail,
                use_regex=use_regex,
                classloader_hash=classloader_hash,
                classloader_class=classloader_class,
                max_matches=max_matches
            )
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def watch_method(pid: int, class_pattern: str, method_pattern: str, 
                        watch_params: bool = True, watch_return: bool = True,
                        condition: str = None, max_times: int = 10) -> Dict:
            """监控方法的调用情况"""
            output = self.arthas.watch_method(pid, class_pattern, method_pattern,
                                            watch_params, watch_return,
                                            condition, max_times)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_logger_info(pid: int, name: str = None) -> Dict:
            """获取logger信息"""
            output = self.arthas.get_logger_info(pid, name)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def set_logger_level(pid: int, name: str, level: str) -> Dict:
            """设置logger级别"""
            output = self.arthas.set_logger_level(pid, name, level)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

        @self.mcp.tool()
        def get_dashboard(pid: int) -> Dict:
            """获取系统实时数据面板"""
            output = self.arthas.get_dashboard(pid)
            return {
                "raw_output": output,
                "timestamp": time.time()
            }

    def run(self):
        """运行服务器"""
        print(f"Starting {self.name}...")
        self.mcp.run() 