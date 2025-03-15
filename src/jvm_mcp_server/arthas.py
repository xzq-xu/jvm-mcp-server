"""Arthas客户端实现"""

import subprocess
import os
import time
import telnetlib
import socket
import paramiko
import logging
import re
from typing import Optional, Dict, Union, Any
from .config import ArthasConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




class ArthasClient:
    """Arthas客户端封装类"""
    _connection_pool = None  # 类级别的连接池
    _config = None  # 类级别的配置对象
    
    @classmethod
    def get_connection_pool(cls):
        """获取连接池实例"""
        if cls._connection_pool is None:
            from .connection_pool import ArthasConnectionPool  # 延迟导入
            cls._connection_pool = ArthasConnectionPool()
        return cls._connection_pool
    
    @classmethod
    def get_config(cls) -> ArthasConfig:
        """获取配置实例"""
        if cls._config is None:
            config_file = os.path.join(os.path.dirname(__file__), '../../config/arthas.json')
            cls._config = ArthasConfig.load(config_file)
        return cls._config
    
    def __init__(self, 
                 telnet_port: int = 3658,
                 ssh_host: str = None,
                 ssh_port: int = 22,
                 ssh_password: str = None):
        """
        初始化Arthas客户端
        Args:
            telnet_port: Arthas telnet端口
            ssh_host: SSH连接地址，格式为 user@host，为None时表示本地连接
            ssh_port: SSH端口，默认22
            ssh_password: SSH密码，为None时表示使用密钥认证
        """
        self.arthas_boot_path = "arthas-boot.jar"
        self.telnet_port = telnet_port
        self.telnet = None
        self.ssh = None
        self.attached_pid = None
        self.arthas_started = False  # 新增：标记Arthas是否已启动
        self.local_port = None  # 新增：保存本地转发端口
        
        # SSH连接信息
        self.ssh_host = ssh_host
        if ssh_host and '@' in ssh_host:
            self.ssh_user, self.ssh_host = ssh_host.split('@')
            logger.info(f"SSH连接信息: 用户={self.ssh_user}, 主机={self.ssh_host}, 端口={ssh_port}")
        else:
            self.ssh_user = None
            self.ssh_host = None
            logger.info("使用本地连接模式")
            
        self.ssh_port = ssh_port
        self.ssh_password = ssh_password
        
        # 如果是远程连接，建立SSH连接
        if self.ssh_host:
            try:
                self._setup_ssh_connection()
            except Exception as e:
                logger.error(f"SSH连接失败: {e}")
                raise
        else:
            self._download_arthas()
        
    def _setup_ssh_connection(self):
        """建立SSH连接"""
        try:
            logger.info(f"正在连接到远程服务器: {self.ssh_host}:{self.ssh_port}")
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.ssh_password:
                logger.info("使用密码认证")
                self.ssh.connect(self.ssh_host, self.ssh_port, self.ssh_user, self.ssh_password)
            else:
                logger.info("使用密钥认证")
                self.ssh.connect(self.ssh_host, self.ssh_port, self.ssh_user)
                
            logger.info("SSH连接成功")
            
            # 在远程服务器上下载arthas
            self._download_arthas_remote()
            
        except paramiko.AuthenticationException:
            logger.error("SSH认证失败，请检查用户名和密码")
            if self.ssh:
                self.ssh.close()
            self.ssh = None
            raise
        except paramiko.SSHException as e:
            logger.error(f"SSH连接出错: {e}")
            if self.ssh:
                self.ssh.close()
            self.ssh = None
            raise
        except Exception as e:
            logger.error(f"连接远程服务器失败: {e}")
            if self.ssh:
                self.ssh.close()
            self.ssh = None
            raise
            
    def _download_arthas_remote(self):
        """在远程服务器上下载Arthas"""
        logger.info("正在远程服务器上下载Arthas...")
        
        # 首先检查文件是否已存在
        check_cmd = "[ -f arthas-boot.jar ] && echo 'exists'"
        stdin, stdout, stderr = self.ssh.exec_command(check_cmd)
        if stdout.read().decode('utf-8').strip() == 'exists':
            logger.info("远程服务器上已存在arthas-boot.jar")
            return
            
        # 下载文件
        cmd = "curl -s -o arthas-boot.jar https://arthas.aliyun.com/arthas-boot.jar"
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        
        # 验证文件是否下载成功
        verify_cmd = "[ -f arthas-boot.jar ] && [ -s arthas-boot.jar ] && echo 'success'"
        stdin, stdout, stderr = self.ssh.exec_command(verify_cmd)
        if stdout.read().decode('utf-8').strip() != 'success':
            error_msg = "下载的arthas-boot.jar文件不存在或大小为0"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        logger.info("Arthas下载成功")
            
    def _download_arthas(self):
        """在本地下载Arthas启动器"""
        if not os.path.exists(self.arthas_boot_path):
            logger.info("正在本地下载Arthas...")
            try:
                subprocess.run(
                    ["curl", "-o", self.arthas_boot_path, "https://arthas.aliyun.com/arthas-boot.jar"],
                    check=True
                )
                logger.info("Arthas下载成功")
            except subprocess.CalledProcessError as e:
                logger.error(f"下载Arthas失败: {e}")
                raise

    def _attach_to_process(self, pid: int):
        """连接到指定的Java进程"""
        if self.attached_pid == pid and hasattr(self, 'arthas_channel') and self.arthas_channel:
            logger.debug(f"已经连接到进程 {pid}")
            return
        
        # 如果已经连接到其他进程，先断开
        self._disconnect()
        
        logger.info(f"正在连接到Java进程 {pid}")
        
        if self.ssh_host:
            # 确保SSH连接有效
            self._ensure_ssh_connection()
            
            try:
                # 检查Java进程是否存在
                check_pid_cmd = f"ps -p {pid} > /dev/null 2>&1 && echo 'exists'"
                stdin, stdout, stderr = self.ssh.exec_command(check_pid_cmd)
                if stdout.read().decode('utf-8').strip() != 'exists':
                    error_msg = f"进程 {pid} 不存在"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                # 启动Arthas并保持会话
                cmd = f"java -jar arthas-boot.jar --telnet-port {self.telnet_port} --http-port -1 {pid}"
                logger.debug(f"执行远程命令: {cmd}")
                
                # 使用get_pty=True来模拟终端，并保持会话
                self.arthas_channel = self.ssh.get_transport().open_session()
                self.arthas_channel.get_pty()
                self.arthas_channel.exec_command(cmd)
                
                # 等待Arthas启动，同时检查输出中是否有错误信息
                start_time = time.time()
                success = False
                error_msg = None
                buffer = ""
                
                while time.time() - start_time < 30:  # 最多等待30秒
                    if self.arthas_channel.recv_ready():
                        output = self.arthas_channel.recv(1024).decode('utf-8')
                        buffer += output
                        logger.debug(f"Arthas输出: {output}")
                        
                        if "Can not attach to target process" in buffer:
                            error_msg = "无法附加到目标进程，可能是权限问题"
                            break
                        elif "ERROR" in buffer:
                            error_msg = f"启动Arthas时发生错误: {buffer}"
                            break
                        elif "as.sh" in buffer or "$" in buffer:  # Arthas的命令提示符
                            success = True
                            break
                    time.sleep(0.1)
                
                if not success:
                    if error_msg is None:
                        error_msg = "启动Arthas超时"
                    logger.error(error_msg)
                    self._disconnect()
                    raise Exception(error_msg)
                
                # 等待一段时间确保Arthas完全启动
                time.sleep(2)
                
                logger.info("Arthas启动成功")
                self.attached_pid = pid
                
            except Exception as e:
                logger.error(f"连接过程中发生错误: {e}")
                self._disconnect()
                raise
                
        else:
            # 本地启动Arthas
            logger.info("在本地启动Arthas")
            try:
                # 使用subprocess.Popen启动Arthas
                cmd = [
                    "java", "-jar", self.arthas_boot_path,
                    "--target-ip", "127.0.0.1",
                    "--telnet-port", str(self.telnet_port),
                    "--http-port", "-1",
                    str(pid)
                ]
                logger.debug(f"执行本地命令: {' '.join(cmd)}")
                
                # 使用subprocess.PIPE来捕获输出
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,  # 使用文本模式
                    bufsize=1  # 行缓冲
                )
                
                # 等待Arthas启动并检查输出
                start_time = time.time()
                success = False
                error_msg = None
                
                while time.time() - start_time < 30:  # 最多等待30秒
                    # 检查进程是否还在运行
                    if process.poll() is not None:
                        error_msg = f"Arthas进程意外退出，返回码: {process.returncode}"
                        break
                        
                    # 尝试建立telnet连接
                    try:
                        logger.debug(f"尝试连接到本地端口 {self.telnet_port}")
                        self.telnet = telnetlib.Telnet("127.0.0.1", self.telnet_port, timeout=2)
                        
                        # 等待提示符确认连接成功
                        response = self.telnet.read_until(b"$", timeout=2).decode('utf-8')
                        if "arthas" in response.lower():
                            logger.info(f"成功连接到进程 {pid}")
                            success = True
                            self.attached_pid = pid
                            # 保存进程引用以便后续管理
                            self.arthas_process = process
                            break
                        else:
                            self.telnet.close()
                            self.telnet = None
                    except (socket.error, EOFError, socket.timeout):
                        # 连接失败，继续等待
                        pass
                        
                    # 检查是否有错误输出
                    stderr_data = process.stderr.readline()
                    if stderr_data:
                        error_msg = f"Arthas启动错误: {stderr_data.strip()}"
                        break
                        
                    time.sleep(1)
                
                if not success:
                    # 如果没有成功，确保清理资源
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=5)
                    if error_msg is None:
                        error_msg = "启动Arthas超时"
                    logger.error(error_msg)
                    self._disconnect()
                    raise Exception(error_msg)
                    
            except Exception as e:
                logger.error(f"启动Arthas失败: {e}")
                self._disconnect()
                raise

    def _find_free_port(self) -> int:
        """查找可用的本地端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

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
        if hasattr(self, 'arthas_channel') and self.arthas_channel:
            try:
                # 发送quit命令给Arthas
                self.arthas_channel.send('quit\n'.encode('utf-8'))
                time.sleep(1)  # 等待命令执行
                self.arthas_channel.close()
            except:
                pass
            finally:
                self.arthas_channel = None
                self.attached_pid = None

        if self.telnet:
            try:
                self.telnet.write(b"quit\n")  # 发送quit命令给Arthas
                time.sleep(1)  # 等待命令执行
                self.telnet.close()
            except:
                pass
            finally:
                self.telnet = None
                self.attached_pid = None
        
        # 清理本地Arthas进程
        if hasattr(self, 'arthas_process') and self.arthas_process:
            try:
                if self.arthas_process.poll() is None:  # 如果进程还在运行
                    self.arthas_process.terminate()  # 先尝试正常终止
                    try:
                        self.arthas_process.wait(timeout=5)  # 等待最多5秒
                    except subprocess.TimeoutExpired:
                        self.arthas_process.kill()  # 如果等待超时，强制终止
            except:
                pass
            finally:
                self.arthas_process = None
        
        if self.ssh:
            try:
                self.ssh.close()
                logger.debug("已关闭SSH连接")
            except Exception as e:
                logger.warning(f"关闭SSH连接时出错: {e}")
            finally:
                self.ssh = None

    def _check_ssh_connection(self) -> bool:
        """检查SSH连接是否有效"""
        if not self.ssh:
            return False
        try:
            self.ssh.exec_command('echo 1')
            return True
        except:
            return False
            
    def _ensure_ssh_connection(self):
        """确保SSH连接有效，如果断开则重连"""
        if not self._check_ssh_connection():
            logger.info("SSH连接已断开，尝试重新连接")
            self._setup_ssh_connection()

    def _execute_command(self, pid: int, command: str) -> str:
        """执行Arthas命令"""
        try:
            # 从连接池获取连接
            logger.info(f"从连接池获取连接 pid={pid}, command={command}")
            conn = self.get_connection_pool().get_connection(pid)
            try:
                # 执行命令
                result = conn.client._execute_command_internal(command)
                if isinstance(result, dict) and "raw_output" in result:
                    return result["raw_output"]
                return result
            finally:
                # 归还连接
                self.get_connection_pool().return_connection(conn)
                
        except Exception as e:
            logger.error(f"执行命令时发生错误: {e}")
            raise
            
    def _execute_command_internal(self, command: str) -> str:
        """执行Arthas命令并返回结果"""
        config = self.get_config()
        cmd_config = config.get_command_config(command.split()[0])  # 获取命令的配置
        
        logger.info(f"开始执行命令: {command}")
        max_retries = cmd_config.max_retries if cmd_config else 3
        retry_interval = cmd_config.retry_interval if cmd_config else 1
        timeout = cmd_config.timeout if cmd_config else 10
        max_output_size = 50000  # 设置最大输出大小为50KB
        
        for retry in range(max_retries):
            try:
                if self.ssh_host:
                    logger.debug("使用SSH模式执行命令")
                    if not hasattr(self, 'arthas_channel') or not self.arthas_channel:
                        raise Exception("Arthas会话未建立")
                    
                    # 清空之前的输出
                    while self.arthas_channel.recv_ready():
                        self.arthas_channel.recv(1024)
                    
                    logger.debug(f"发送命令: {command}")
                    self.arthas_channel.send(command + "\n")
                    
                    # 等待并收集输出
                    output = ""
                    start_time = time.time()
                    output_size = 0
                    truncated = False
                    
                    while time.time() - start_time < timeout:
                        if self.arthas_channel.recv_ready():
                            chunk = self.arthas_channel.recv(4096).decode('utf-8')
                            logger.debug(f"接收到数据块: {len(chunk)} 字节")
                            
                            chunk_size = len(chunk.encode('utf-8'))
                            if output_size + chunk_size > max_output_size:
                                logger.warning(f"输出超过大小限制 ({max_output_size} 字节)，进行截断")
                                remaining = max_output_size - output_size
                                if remaining > 0:
                                    output += chunk[:remaining]
                                truncated = True
                                break
                            
                            output += chunk
                            output_size += chunk_size
                            
                            if "$" in chunk:  # 命令提示符表示命令执行完成
                                logger.debug("检测到命令提示符，命令执行完成")
                                break
                        time.sleep(0.1)
                    
                    if time.time() - start_time >= timeout:
                        raise TimeoutError(f"命令执行超时: {command}")
                    
                    # 移除命令回显和提示符
                    lines = output.split("\n")
                    lines = [line for line in lines if line and not line.startswith(command) and "$" not in line]
                    result = "\n".join(lines)
                    
                    if truncated:
                        result += "\n... (输出已截断，超过50KB)"
                    
                    logger.info(f"命令执行成功，输出大小: {len(result)} 字节")
                    return result
                    
                else:
                    logger.debug("使用本地模式执行命令")
                    if not hasattr(self, 'telnet') or not self.telnet:
                        self.telnet = telnetlib.Telnet('127.0.0.1', self.telnet_port, timeout=timeout)
                    
                    # 清空之前的输出
                    self.telnet.read_very_eager()
                    
                    logger.debug(f"发送命令: {command}")
                    self.telnet.write(command.encode() + b"\n")
                    
                    # 等待并收集输出
                    output = ""
                    start_time = time.time()
                    output_size = 0
                    truncated = False
                    
                    while time.time() - start_time < timeout:
                        try:
                            chunk = self.telnet.read_eager().decode('utf-8')
                            if chunk:
                                logger.debug(f"接收到数据块: {len(chunk)} 字节")
                                chunk_size = len(chunk.encode('utf-8'))
                                if output_size + chunk_size > max_output_size:
                                    logger.warning(f"输出超过大小限制 ({max_output_size} 字节)，进行截断")
                                    remaining = max_output_size - output_size
                                    if remaining > 0:
                                        output += chunk[:remaining]
                                    truncated = True
                                    break
                                
                                output += chunk
                                output_size += chunk_size
                                
                                if "$" in chunk:  # 命令提示符表示命令执行完成
                                    logger.debug("检测到命令提示符，命令执行完成")
                                    break
                            else:
                                time.sleep(0.1)
                        except EOFError:
                            logger.error("连接已关闭")
                            break
                    
                    if time.time() - start_time >= timeout:
                        raise TimeoutError(f"命令执行超时: {command}")
                    
                    # 移除命令回显和提示符
                    lines = output.split("\n")
                    lines = [line for line in lines if line and not line.startswith(command) and "$" not in line]
                    result = "\n".join(lines)
                    
                    if truncated:
                        result += "\n... (输出已截断，超过50KB)"
                    
                    logger.info(f"命令执行成功，输出大小: {len(result)} 字节")
                    return result
                    
            except (TimeoutError, socket.timeout) as e:
                logger.warning(f"命令执行超时 (重试 {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    time.sleep(retry_interval)
                    continue
                raise
                
            except Exception as e:
                logger.error(f"命令执行失败: {str(e)}")
                if retry < max_retries - 1:
                    time.sleep(retry_interval)
                    continue
                raise
                
        raise Exception(f"命令执行失败，已重试{max_retries}次: {command}")

    def __del__(self):
        """析构函数，确保断开连接"""
        self._disconnect()

    def _format_thread_info(self, output: str) -> str:
        """格式化线程信息输出
        
        Args:
            output: 原始输出字符串
            
        Returns:
            格式化后的输出字符串
        """
        try:
            # 移除ANSI转义序列
            output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
            
            # 移除空行和命令提示符
            lines = [line.strip() for line in output.split('\n') if line.strip() and not line.strip().endswith('$')]
            
            # 如果输出为空，返回原始输出
            if not lines:
                return output
            
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"格式化线程信息失败: {str(e)}")
            return output  # 如果格式化失败，返回原始输出

    def get_thread_info(self, pid: int) -> Dict[str, Any]:
        """获取指定进程的线程信息
        
        Args:
            pid: 进程ID
            
        Returns:
            包含线程信息的字典
        """
        try:
            output = self._execute_command(pid, "thread -n 20")
            formatted_output = self._format_thread_info(output)
            return {
                "raw_output": formatted_output,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取线程信息失败: {str(e)}")
            raise

    def get_jvm_info(self, pid: int) -> str:
        """获取JVM信息"""
        return self._execute_command(pid, "jvm")

    def get_memory_info(self, pid: int) -> str:
        """获取内存信息"""
        return self._execute_command(pid, "memory")

    def get_stack_trace(
        self, pid: int, thread_id: Optional[int] = None,
        top_n: Optional[int] = None, find_blocking: bool = False,
        interval: Optional[int] = None, show_all: bool = False
    ) -> Dict[str, Any]:
        """获取线程堆栈信息
        
        Args:
            pid: 进程ID
            thread_id: 线程ID
            top_n: 显示最忙的前N个线程
            find_blocking: 是否查找阻塞线程
            interval: CPU使用率统计的采样间隔(毫秒)
            show_all: 是否显示所有线程
            
        Returns:
            包含堆栈信息的字典
        """
        try:
            cmd = ["thread"]
            if thread_id is not None:
                cmd.append(str(thread_id))
            elif top_n is not None:
                cmd.extend(["-n", str(top_n)])
            elif show_all:
                cmd.append("--all")
            else:
                cmd.extend(["-n", "20"])  # 默认显示前20个线程
            
            if find_blocking:
                cmd.append("-b")
            
            if interval is not None:
                cmd.extend(["-i", str(interval)])
            
            output = self._execute_command(pid, " ".join(cmd))
            formatted_output = self._format_thread_info(output)
            return {
                "raw_output": formatted_output,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取堆栈信息失败: {str(e)}")
            raise

    def get_class_info(self, pid: int, class_pattern: str, 
                      show_detail: bool = False, 
                      show_field: bool = False,
                      use_regex: bool = False,
                      depth: int = None,
                      classloader_hash: str = None,
                      classloader_class: str = None,
                      max_matches: int = None) -> str:
        """获取类信息
        
        Args:
            pid: 进程ID
            class_pattern: 类名表达式匹配
            show_detail: 是否显示详细信息
            show_field: 是否显示成员变量信息(需要show_detail=True)
            use_regex: 是否使用正则表达式匹配
            depth: 指定输出静态变量时属性的遍历深度
            classloader_hash: 指定class的ClassLoader的hashcode
            classloader_class: 指定执行表达式的ClassLoader的class name
            max_matches: 具有详细信息的匹配类的最大数量
        """
        command = f"sc"
        
        # 添加参数
        if show_detail:
            command += " -d"
        if show_field and show_detail:  # show_field需要配合-d使用
            command += " -f"
        if use_regex:
            command += " -E"
        if depth is not None:
            command += f" -x {depth}"
        if classloader_hash:
            command += f" -c {classloader_hash}"
        if classloader_class:
            command += f" --classLoaderClass {classloader_class}"
        if max_matches is not None:
            command += f" -n {max_matches}"
            
        # 添加类名匹配模式
        command += f" {class_pattern}"
        
        return self._execute_command(pid, command)

    def list_java_processes(self) -> str:
        """列出Java进程"""
        if self.ssh_host:
            # 确保SSH连接有效
            self._ensure_ssh_connection()
            stdin, stdout, stderr = self.ssh.exec_command("jps -l -v")
            return stdout.read().decode('utf-8')
        else:
            result = subprocess.run(["jps", "-l", "-v"], capture_output=True, text=True)
            return result.stdout 

    def get_version(self, pid: int) -> str:
        """获取Arthas版本信息"""
        return self._execute_command(pid, "version")

    def get_stack_trace_by_method(self, pid: int, class_pattern: str, method_pattern: str,
                               condition: str = None,
                               use_regex: bool = False,
                               max_matches: int = None,
                               max_times: int = None) -> str:
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
        command = f"stack {class_pattern} {method_pattern}"
        
        # 添加参数
        if condition:
            command += f" '{condition}'"
        if use_regex:
            command += " -E"
        if max_matches is not None:
            command += f" -m {max_matches}"
        if max_times is not None:
            command += f" -n {max_times}"
            
        return self._execute_command(pid, command)

    def decompile_class(self, pid: int, class_pattern: str, method_pattern: str = None) -> str:
        """反编译指定类的源码
        
        Args:
            pid: 进程ID
            class_pattern: 类名表达式
            method_pattern: 可选的方法名，如果指定则只反编译特定方法
        """
        command = f"jad {class_pattern}"
        if method_pattern:
            command += f" {method_pattern}"
        return self._execute_command(pid, command)

    def search_method(self, pid: int, class_pattern: str, method_pattern: str = None,
                      show_detail: bool = False,
                      use_regex: bool = False,
                      classloader_hash: str = None,
                      classloader_class: str = None,
                      max_matches: int = None) -> str:
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
        command = f"sm"
        
        # 添加参数
        if show_detail:
            command += " -d"
        if use_regex:
            command += " -E"
        if classloader_hash:
            command += f" -c {classloader_hash}"
        if classloader_class:
            command += f" --classLoaderClass {classloader_class}"
        if max_matches is not None:
            command += f" -n {max_matches}"
            
        # 添加类名和方法名匹配模式
        command += f" {class_pattern}"
        if method_pattern:
            command += f" {method_pattern}"
            
        return self._execute_command(pid, command)

    def watch_method(self, pid: int, class_pattern: str, method_pattern: str, 
                    watch_params: bool = True, watch_return: bool = True, 
                    condition: str = None, max_times: int = 10) -> str:
        """监控方法的调用情况
        
        Args:
            pid: 进程ID
            class_pattern: 类名表达式
            method_pattern: 方法名表达式
            watch_params: 是否监控参数
            watch_return: 是否监控返回值
            condition: 条件表达式
            max_times: 最大监控次数
        """
        command = f"watch {class_pattern} {method_pattern}"
        if watch_params:
            command += " params"
        if watch_return:
            command += " returnObj"
        if condition:
            command += f" '{condition}'"
        command += f" -n {max_times}"
        return self._execute_command(pid, command)

    def get_logger_info(self, pid: int, name: str = None) -> str:
        """获取logger信息
        
        Args:
            pid: 进程ID
            name: logger名称
        """
        command = "logger"
        if name:
            command += f" --name {name}"
        return self._execute_command(pid, command)

    def set_logger_level(self, pid: int, name: str, level: str) -> str:
        """设置logger级别
        
        Args:
            pid: 进程ID
            name: logger名称
            level: 日志级别(trace, debug, info, warn, error)
        """
        return self._execute_command(pid, f"logger --name {name} --level {level}")

    def get_dashboard(self, pid: int) -> str:
        """获取系统实时数据面板"""
        return self._execute_command(pid, "dashboard") 