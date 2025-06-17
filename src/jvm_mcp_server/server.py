"""JVM MCP Server实现"""

import json
import time
import os
import re
from typing import List, Dict, Optional

from mcp.server.fastmcp import FastMCP
from .native.base import NativeCommandExecutor
from .native.tools.jps import JpsCommand, JpsFormatter
from .native.tools.jstack import JstackCommand, JstackFormatter
from .native.tools.jinfo import JinfoCommand, JinfoFormatter
from .native.tools.jmap import JmapCommand, JmapHeapFormatter
from .native.tools.jcmd import JcmdCommand, JcmdFormatter
from .native.tools.jstat import JstatCommand, JstatFormatter

class JvmMcpServer:
    """JVM MCP服务器（基于native命令）"""

    def __init__(self, name: str = "native-jvm-monitor"):
        """
        初始化JVM MCP服务器
        Args:
            name: 服务器名称

        Environment Variables:
            SSH_HOST: SSH连接地址，格式为 user@host，不存在则表示本地连接
            SSH_PORT: SSH端口，默认22
            SSH_USER: SSH用户名，不存在则使用密钥认证
            SSH_PASSWORD: SSH密码，不存在则使用密钥认证
            SSH_KEY: SSH密钥路径，不存在则使用密码认证
        """
        self.name = name
        self.mcp = FastMCP(name)
        # 读取SSH参数
        ssh_host_env = os.getenv('SSH_HOST')
        ssh_port = int(os.getenv('SSH_PORT', '22'))
        ssh_password = os.getenv('SSH_PASSWORD')
        ssh_key = os.getenv('SSH_KEY')
        ssh_host = None
        ssh_user = None
        if ssh_host_env:
            # 支持 root@host 格式
            m = re.match(r'([^@]+)@(.+)', ssh_host_env)
            if m:
                ssh_user = m.group(1)
                ssh_host = m.group(2)
            else:
                ssh_host = ssh_host_env
        if ssh_host and ssh_user:
            self.executor = NativeCommandExecutor(
                ssh_host=ssh_host,
                ssh_port=ssh_port,
                ssh_user=ssh_user,
                ssh_password=ssh_password,
                ssh_key=ssh_key
                )
        else:
            self.executor = NativeCommandExecutor()
        self._setup_tools()

    def _setup_tools(self):
        """设置MCP工具"""
        @self.mcp.tool()
        def list_java_processes() -> List[Dict[str, str]]:
            """列出所有Java进程"""
            cmd = JpsCommand(self.executor, JpsFormatter())
            result = cmd.execute()
            processes = []
            if result.get('success'):
                for proc in result['processes']:
                    processes.append(proc)
            return processes

        @self.mcp.tool()
        def get_thread_info(pid: Optional[int] = None) -> Dict:
            """获取指定进程的线程信息"""
            cmd = JstackCommand(self.executor, JstackFormatter())
            result = cmd.execute(str(pid) if pid is not None else "")
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
                }

        @self.mcp.tool()
        def get_jvm_info(pid: Optional[int] = None) -> Dict:
            """获取JVM基础信息"""
            cmd = JinfoCommand(self.executor, JinfoFormatter())
            result = cmd.execute(str(pid) if pid is not None else "")
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
                }

        @self.mcp.tool()
        def get_memory_info(pid: Optional[int] = None) -> Dict:
            """获取内存使用情况"""
            cmd = JmapCommand(self.executor, JmapHeapFormatter())
            result = cmd.execute(str(pid) if pid is not None else "")
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
                }

        @self.mcp.tool()
        def get_stack_trace(pid: Optional[int] = None, thread_id: Optional[int] = None, top_n: Optional[int] = None,
                            find_blocking: bool = False, interval: Optional[int] = None,
                            show_all: bool = False) -> Dict:
            """获取线程堆栈信息（仅支持全部线程）"""
            cmd = JstackCommand(self.executor, JstackFormatter())
            result = cmd.execute(str(pid) if pid is not None else "")
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
                }

        # @self.mcp.tool()
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
            return {"success": False, "error": "未实现/不支持"}

        # @self.mcp.tool()
        def get_jvm_status(pid: int) -> Dict:
            """获取JVM整体状态报告

            Args:
                pid: 可选的进程ID，如果不指定则自动选择第一个非arthas的Java进程

            Returns:
                包含JVM状态信息的字典
            """
            return {"success": False, "error": "未实现/不支持"}


        # @self.mcp.tool()
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
            return {"success": False, "error": "未实现/不支持"}

        # @self.mcp.tool()
        def decompile_class(pid: int, class_pattern: str, method_pattern: str = None) -> Dict:
            """反编译指定类的源码"""
            return {"success": False, "error": "未实现/不支持"}

        # @self.mcp.tool()
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
            return {"success": False, "error": "未实现/不支持"}

        # @self.mcp.tool()
        def watch_method(pid: int, class_pattern: str, method_pattern: str,
                         watch_params: bool = True, watch_return: bool = True,
                         condition: str = None, max_times: int = 10) -> Dict:
            """监控方法的调用情况"""
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def get_logger_info(pid: int, name: str = None) -> Dict:
            """获取logger信息"""
            return {"success": False, "error": "未实现/不支持"}

        # @self.mcp.tool()
        def set_logger_level(pid: int, name: str, level: str) -> Dict:
            """设置logger级别"""
            return {"success": False, "error": "未实现/不支持"}

        # @self.mcp.tool()
        def get_dashboard(pid: int) -> Dict:
            """获取系统实时数据面板"""
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def get_jcmd_output(pid: int, subcommand: str = None) -> Dict:
            """执行 jcmd 子命令"""
            cmd = JcmdCommand(self.executor, JcmdFormatter())
            result = cmd.execute(str(pid), subcommand=subcommand)
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
                }

        @self.mcp.tool()
        def get_jstat_output(pid: int, option: str = None, interval: int = None, count: int = None) -> Dict:
            """执行 jstat 监控命令"""
            cmd = JstatCommand(self.executor, JstatFormatter())
            result = cmd.execute(str(pid), option=option, interval=interval, count=count)
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
                }

    def run(self):
        """运行服务器"""
        print(f"Starting {self.name}...")
        self.mcp.run("sse")
