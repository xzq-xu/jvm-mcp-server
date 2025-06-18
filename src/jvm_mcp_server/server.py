"""JVM MCP Server实现"""

import json
import time
import os
import re
from typing import List, Dict, Optional, Union

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
            name (str): 服务器名称
        
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

    def _validate_and_convert_id(self, value: Union[int, str, None], param_name: str = "ID") -> Optional[int]:
        """
        验证并转换ID参数，支持int和str类型的数字参数
        
        Args:
            value: 要转换的值，可以是int、str或None
            param_name: 参数名称，用于错误信息
            
        Returns:
            转换后的整数值，如果输入为None则返回None
            
        Raises:
            ValueError: 如果无法转换为有效的整数
        """
        if value is None:
            return None
            
        if isinstance(value, int):
            return value
            
        if isinstance(value, str):
            # 去除前后空白字符
            value = value.strip()
            if not value:
                return None
                
            try:
                # 支持十六进制格式（如0x2c03）和十进制格式
                if value.lower().startswith('0x'):
                    return int(value, 16)
                else:
                    return int(value)
            except ValueError:
                raise ValueError(f"Invalid {param_name}: '{value}' cannot be converted to integer")
        
        raise ValueError(f"Invalid {param_name} type: expected int, str or None, got {type(value)}")

    def _setup_tools(self):
        """设置MCP工具"""
        @self.mcp.tool()
        def list_java_processes() -> List[Dict[str, str]]:
            """列出所有Java进程

            Returns:
                List[Dict[str, str]]: 包含Java进程信息的列表，每个进程包含以下字段：
                    - pid (str): 进程ID
                    - name (str): 进程名称
                    - args (str): 进程参数
            """
            cmd = JpsCommand(self.executor, JpsFormatter())
            result = cmd.execute()
            processes = []
            if result.get('success'):
                for proc in result['processes']:
                    processes.append(proc)
            return processes

        @self.mcp.tool()
        def get_thread_info(pid: str = "") -> Dict:
            """获取指定进程的线程信息

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）。
                    支持十进制和十六进制格式。
                    空字符串将返回错误信息。

            Returns:
                Dict: 包含线程信息的字典，包含以下字段：
                    - threads (List[Dict]): 线程信息列表
                    - thread_count (int): 线程数量
                    - raw_output (str): 原始输出
                    - timestamp (float): 时间戳
                    - success (bool): 是否成功
                    - error (Optional[str]): 错误信息
            """
            try:
                validated_pid = self._validate_and_convert_id(pid if pid else None, "process ID")
                if validated_pid is None:
                    return {
                        "threads": [],
                        "thread_count": 0,
                        "raw_output": "",
                        "timestamp": time.time(),
                        "success": False,
                        "error": "Invalid process ID"
                    }
            except ValueError as e:
                return {
                    "threads": [],
                    "thread_count": 0,
                    "raw_output": "",
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                }
            
            cmd = JstackCommand(self.executor, JstackFormatter())
            result = cmd.execute(str(validated_pid))
            
            if not result.get('success', False):
                return {
                    "threads": [],
                    "thread_count": 0,
                    "raw_output": result.get('output', ''),
                    "timestamp": time.time(),
                    "success": False,
                    "error": result.get('error', 'Failed to execute jstack command')
                }
            
            threads = result.get('threads', [])
            
            # 返回格式化后的结果，包含 threads 字段
            return {
                "threads": threads,
                "thread_count": len(threads),
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": True,
                "error": None
            }

        @self.mcp.tool()
        def get_jvm_info(pid: str = "") -> Dict:
            """获取JVM基础信息

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）。
                    支持十进制和十六进制格式。
                    空字符串将返回错误信息。

            Returns:
                Dict: 包含JVM信息的字典，包含以下字段：
                    - raw_output (str): 原始输出
                    - timestamp (float): 时间戳
                    - success (bool): 是否成功
                    - error (Optional[str]): 错误信息
            """
            try:
                validated_pid = self._validate_and_convert_id(pid if pid else None, "process ID")
                if validated_pid is None:
                    return {
                        "raw_output": "",
                        "timestamp": time.time(),
                        "success": False,
                        "error": "Invalid process ID"
                    }
            except ValueError as e:
                return {
                    "raw_output": "",
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                }
            
            cmd = JinfoCommand(self.executor, JinfoFormatter())
            result = cmd.execute(str(validated_pid))
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
            }

        @self.mcp.tool()
        def get_memory_info(pid: str = "") -> Dict:
            """获取内存使用情况

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）。
                    支持十进制和十六进制格式。
                    空字符串将返回错误信息。

            Returns:
                Dict: 包含内存信息的字典，包含以下字段：
                    - raw_output (str): 原始输出
                    - timestamp (float): 时间戳
                    - success (bool): 是否成功
                    - error (Optional[str]): 错误信息
            """    
            try:
                validated_pid = self._validate_and_convert_id(pid if pid else None, "process ID")
                if validated_pid is None:
                    return {
                        "raw_output": "",
                        "timestamp": time.time(),
                        "success": False,
                        "error": "Invalid process ID"
                    }
            except ValueError as e:
                return {
                    "raw_output": "",
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                }
            
            cmd = JmapCommand(self.executor, JmapHeapFormatter())
            result = cmd.execute(str(validated_pid))
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
            }

        @self.mcp.tool()
        def get_stack_trace(pid: str = "", 
                            thread_id: str = "", 
                            top_n: str = "5", 
                            find_blocking: bool = False, 
                            interval: str = "", 
                            show_all: bool = False) -> Dict:
            """获取线程堆栈信息
            
            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                thread_id (str): 线程ID，使用字符串形式。支持十六进制（如："0x2c03"）
                top_n (str): 显示前N个线程，使用字符串形式（如："5"），默认值为"5"
                find_blocking (bool): 是否只查找阻塞线程（BLOCKED状态或等待锁的线程）
                interval (str): 采样间隔，使用字符串形式（如："1000"表示1秒）
                show_all (bool): 是否显示所有信息

            Returns:
                Dict: 包含线程堆栈信息的字典，包含以下字段：
                    - threads (List[Dict]): 线程信息列表
                    - thread_count (int): 线程数量
                    - raw_output (str): 原始输出
                    - timestamp (float): 时间戳
                    - success (bool): 是否成功
                    - error (Optional[str]): 错误信息
            """
            
            try:
                validated_pid = self._validate_and_convert_id(pid if pid else None, "process ID")
                if validated_pid is None:
                    return {
                        "raw_output": "",
                        "timestamp": time.time(),
                        "success": False,
                        "error": "Invalid process ID"
                    }
                
                validated_thread_id = self._validate_and_convert_id(thread_id if thread_id else None, "thread ID")
                validated_top_n = self._validate_and_convert_id(top_n if top_n else None, "top_n")
                # 设置默认值
                if validated_top_n is None:
                    validated_top_n = 5
                    
            except ValueError as e:
                return {
                    "raw_output": "",
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                }
            
            cmd = JstackCommand(self.executor, JstackFormatter())
            result = cmd.execute(str(validated_pid))
            
            if not result.get('success', False):
                return {
                    "threads": [],
                    "thread_count": 0,
                    "raw_output": result.get('output', ''),
                    "timestamp": time.time(),
                    "success": False,
                    "error": result.get('error', 'Failed to execute jstack command')
                }
            
            threads = result.get('threads', [])
            
            # 处理 find_blocking：筛选阻塞线程
            if find_blocking:
                blocking_threads = []
                for thread in threads:
                    state = thread.get('state', '').upper()
                    locks = thread.get('locks', [])
                    
                    # 检查是否为阻塞状态
                    is_blocked = (
                        'BLOCKED' in state or
                        any('waiting to lock' in lock.lower() for lock in locks) or
                        any('parking to wait' in lock.lower() for lock in locks)
                    )
                    
                    if is_blocked:
                        blocking_threads.append(thread)
                
                threads = blocking_threads
            
            # 处理 thread_id：筛选指定线程
            if validated_thread_id is not None:
                target_threads = []
                # 支持十进制和十六进制
                target_nid_hex = hex(validated_thread_id) if isinstance(validated_thread_id, int) else str(validated_thread_id)
                target_nid_dec = str(validated_thread_id)
                
                for thread in threads:
                    thread_nid = thread.get('nid', '')
                    thread_tid = thread.get('thread_id')
                    
                    # 匹配nid（十六进制）或thread_id（十进制）
                    if (thread_nid == target_nid_hex or 
                        thread_nid == target_nid_dec or
                        thread_tid == validated_thread_id):
                        target_threads.append(thread)
                
                threads = target_threads
            
            # 处理 top_n：取前N个线程
            if validated_top_n is not None and validated_top_n > 0:
                threads = threads[:validated_top_n]
            
            # 返回格式化后的结果，包含 threads 字段
            return {
                "threads": threads,
                "thread_count": len(threads),
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": True,
                "error": None
            }

        @self.mcp.tool()
        def get_class_info(pid: str = "", 
                          class_pattern: str = "",
                          show_detail: bool = False,
                          show_field: bool = False,
                          use_regex: bool = False,
                          depth: str = "",
                          classloader_hash: Optional[str] = None,
                          classloader_class: Optional[str] = None,
                          max_matches: str = "") -> Dict:
            """获取类信息 - 使用jmap -histo和javap命令获取完整的类信息
            
            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                class_pattern (str): 类名表达式匹配
                show_detail (bool): 是否显示详细信息，默认false
                show_field (bool): 是否显示成员变量信息(需要show_detail=True)，默认false
                use_regex (bool): 是否使用正则表达式匹配，默认false
                depth (str): 属性遍历深度（暂未使用）
                classloader_hash (Optional[str]): 指定class的ClassLoader的hashcode（暂未使用）
                classloader_class (Optional[str]): 指定执行表达式的ClassLoader的class name（暂未使用）
                max_matches (str): 匹配类的最大数量，使用字符串形式（如："50"）

            Returns:
                Dict: 包含类信息的字典
            """
            # 验证 pid 参数
            validated_pid = self._validate_and_convert_id(pid if pid else None, "Process ID")
            if validated_pid is None:
                return {"success": False, "error": "有效的进程ID是必须的"}
            
            # 验证 max_matches 参数
            validated_max_matches = None
            if max_matches:
                validated_max_matches = self._validate_and_convert_id(max_matches, "Max matches")
                if validated_max_matches is None or validated_max_matches <= 0:
                    return {"success": False, "error": "max_matches必须是正整数"}
            
            try:
                # 创建 ClassInfoCoordinator 实例
                from .native.base import NativeCommandExecutor
                from .native.tools import ClassInfoCoordinator
                
                executor = NativeCommandExecutor()
                coordinator = ClassInfoCoordinator(executor)
                
                # 调用协调器获取类信息
                result = coordinator.get_class_info_parallel(
                    pid=str(validated_pid),
                    class_pattern=class_pattern,
                    show_detail=show_detail,
                    show_field=show_field,
                    use_regex=use_regex,
                    max_matches=validated_max_matches
                )
                
                return result
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"获取类信息时发生错误: {str(e)}",
                    "classes": [],
                    "total_matches": 0,
                    "limited_by_max": False
                }

        @self.mcp.tool()
        def get_jvm_status(pid: str = "") -> Dict:
            """获取JVM整体状态报告
            
            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）。
                    如果不指定则自动选择第一个Java进程
            
            Returns:
                Dict: 包含JVM状态信息的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}


        @self.mcp.tool()
        def get_stack_trace_by_method(pid: str = "", 
                                      class_pattern: str = "", 
                                      method_pattern: str = "", condition: Optional[str] = None,
                                      use_regex: bool = False,
                                      max_matches: str = "",
                                      max_times: str = "") -> Dict:
            """获取方法的调用路径
            
            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                class_pattern (str): 类名表达式匹配
                method_pattern (str): 方法名表达式匹配
                condition (Optional[str]): 条件表达式，例如：'params[0]<0' 或 '#cost>10'
                use_regex (bool): 是否开启正则表达式匹配，默认为通配符匹配
                max_matches (str): Class最大匹配数量，使用字符串形式（如："50"）
                max_times (str): 执行次数限制，使用字符串形式

            Returns:
                Dict: 包含方法调用路径信息的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def decompile_class(pid: str = "", 
                           class_pattern: str = "", 
                           method_pattern: Optional[str] = None) -> Dict:
            """反编译指定类的源码

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                class_pattern (str): 类名表达式匹配
                method_pattern (Optional[str]): 可选的方法名表达式

            Returns:
                Dict: 包含反编译源码的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def search_method(pid: str = "", 
                         class_pattern: str = "", 
                         method_pattern: Optional[str] = None, show_detail: bool = False,
                         use_regex: bool = False, classloader_hash: Optional[str] = None,
                         classloader_class: Optional[str] = None,
                         max_matches: str = "") -> Dict:
            """查看类的方法信息
            
            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                class_pattern (str): 类名表达式匹配
                method_pattern (Optional[str]): 可选的方法名表达式
                show_detail (bool): 是否展示每个方法的详细信息
                use_regex (bool): 是否开启正则表达式匹配，默认为通配符匹配
                classloader_hash (Optional[str]): 指定class的ClassLoader的hashcode
                classloader_class (Optional[str]): 指定执行表达式的ClassLoader的class name
                max_matches (str): 匹配类的最大数量，使用字符串形式（如："100"）

            Returns:
                Dict: 包含方法信息的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def watch_method(pid: str = "", 
                        class_pattern: str = "", 
                        method_pattern: str = "", watch_params: bool = True, 
                        watch_return: bool = True, condition: Optional[str] = None, 
                        max_times: str = "10") -> Dict:
            """监控方法的调用情况

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                class_pattern (str): 类名表达式匹配
                method_pattern (str): 方法名表达式匹配
                watch_params (bool): 是否监控方法参数
                watch_return (bool): 是否监控方法返回值
                condition (Optional[str]): 条件表达式
                max_times (str): 最大监控次数，使用字符串形式（如："10"）

            Returns:
                Dict: 包含方法监控信息的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def get_logger_info(pid: str = "", 
                           name: Optional[str] = None) -> Dict:
            """获取logger信息

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                name (Optional[str]): logger名称，如果不指定则获取所有logger信息

            Returns:
                Dict: 包含logger信息的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def set_logger_level(pid: str = "", 
                            name: str = "", level: str = "") -> Dict:
            """设置logger级别

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                name (str): logger名称
                level (str): 日志级别

            Returns:
                Dict: 设置结果的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def get_dashboard(pid: str = "") -> Dict:
            """获取系统实时数据面板

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）

            Returns:
                Dict: 包含系统实时数据的字典（暂未实现）
            """
            return {"success": False, "error": "未实现/不支持"}

        @self.mcp.tool()
        def get_jcmd_output(pid: str = "", 
                           subcommand: Optional[str] = None) -> Dict:
            """执行 jcmd 子命令

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                subcommand (Optional[str]): jcmd子命令，如果不指定则执行help命令

            Returns:
                Dict: 包含jcmd执行结果的字典，包含以下字段：
                    - raw_output (str): 原始输出
                    - timestamp (float): 时间戳
                    - success (bool): 是否成功
                    - error (Optional[str]): 错误信息
            """
            try:
                validated_pid = self._validate_and_convert_id(pid if pid else None, "process ID")
                if validated_pid is None:
                    return {
                        "raw_output": "",
                        "timestamp": time.time(),
                        "success": False,
                        "error": "Invalid process ID"
                    }
            except ValueError as e:
                return {
                    "raw_output": "",
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                }
            
            cmd = JcmdCommand(self.executor, JcmdFormatter())
            result = cmd.execute(str(validated_pid), subcommand=subcommand)
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
            }

        @self.mcp.tool()
        def get_jstat_output(pid: str = "", 
                            option: Optional[str] = None, 
                            interval: str = "", 
                            count: str = "") -> Dict:
            """执行 jstat 监控命令

            Args:
                pid (str): 进程ID，使用字符串形式（如："12345"）
                option (Optional[str]): jstat选项，如gc、class、compiler等
                interval (str): 采样间隔（毫秒），使用字符串形式（如："1000"表示1秒）
                count (str): 采样次数，使用字符串形式（如："10"）

            Returns:
                Dict: 包含jstat执行结果的字典，包含以下字段：
                    - raw_output (str): 原始输出
                    - timestamp (float): 时间戳
                    - success (bool): 是否成功
                    - error (Optional[str]): 错误信息
            """
            try:
                validated_pid = self._validate_and_convert_id(pid if pid else None, "process ID")
                if validated_pid is None:
                    return {
                        "raw_output": "",
                        "timestamp": time.time(),
                        "success": False,
                        "error": "Invalid process ID"
                    }
                
                validated_interval = self._validate_and_convert_id(interval if interval else None, "interval")
                validated_count = self._validate_and_convert_id(count if count else None, "count")
                
            except ValueError as e:
                return {
                    "raw_output": "",
                    "timestamp": time.time(),
                    "success": False,
                    "error": str(e)
                }
            
            cmd = JstatCommand(self.executor, JstatFormatter())
            result = cmd.execute(str(validated_pid), option=option, interval=validated_interval, count=validated_count)
            return {
                "raw_output": result.get('output', ''),
                "timestamp": time.time(),
                "success": result.get('success', False),
                "error": result.get('error')
            }

    def run(self):
        """运行服务器"""
        print(f"Starting {self.name}...")
        self.mcp.run() 
