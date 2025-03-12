"""Arthas客户端实现"""

import subprocess
import os
import time
import telnetlib
import socket
import paramiko
import logging
from typing import Optional, Dict, Union

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArthasClient:
    """Arthas客户端封装类"""
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
                cmd = f"java -jar arthas-boot.jar {pid}"
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
                        elif "$" in buffer:  # Arthas的命令提示符
                            success = True
                            break
                    time.sleep(0.1)
                
                if not success:
                    if error_msg is None:
                        error_msg = "启动Arthas超时"
                    logger.error(error_msg)
                    self._disconnect()
                    raise Exception(error_msg)
                
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
                process = subprocess.Popen(
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
                
                # 检查进程是否有错误
                error = process.stderr.read().decode('utf-8')
                if error:
                    logger.error(f"启动Arthas失败: {error}")
                    raise Exception(f"启动Arthas失败: {error}")
                
                # 建立telnet连接
                logger.debug(f"连接到本地端口 {self.telnet_port}")
                self.telnet = telnetlib.Telnet("127.0.0.1", self.telnet_port, timeout=10)
                self.attached_pid = pid
                
                try:
                    self.telnet.read_until(b"$", timeout=10)
                    logger.info(f"成功连接到进程 {pid}")
                except EOFError:
                    error_msg = "连接到Arthas失败，可能是进程不存在或没有权限"
                    logger.error(error_msg)
                    self._disconnect()
                    raise Exception(error_msg)
                    
            except (socket.error, EOFError) as e:
                logger.error(f"连接Arthas失败: {e}")
                self._disconnect()
                raise
            except Exception as e:
                logger.error(f"连接过程中发生错误: {e}")
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
                self.arthas_channel.send('quit\n')
                time.sleep(1)  # 等待命令执行
                self.arthas_channel.close()
            except:
                pass
            finally:
                self.arthas_channel = None
                self.attached_pid = None
                
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
            # 先尝试直接连接telnet
            if not self.telnet:
                try:
                    logger.info(f"尝试直接连接到端口 {self.telnet_port}")
                    self.telnet = telnetlib.Telnet("localhost", self.telnet_port, timeout=2)
                    # 等待提示符确认连接成功
                    response = self.telnet.read_until(b"$", timeout=2).decode('utf-8')
                    if "arthas" in response.lower():
                        logger.info("成功连接到现有的Arthas会话")
                        self.current_pid = pid
                    else:
                        self._disconnect()
                except Exception as e:
                    logger.debug(f"直接连接失败: {e}")
                    self._disconnect()
                    # 如果直接连接失败，尝试启动新的Arthas会话
                    self._attach_to_process(pid)
            
            if not self.telnet:
                raise Exception("未能连接到Arthas")
            
            # 发送命令
            logger.debug(f"发送命令: {command}")
            self.telnet.write(command.encode('utf-8') + b'\n')
            
            # 读取响应直到下一个提示符
            buffer = ""
            start_time = time.time()
            
            while time.time() - start_time < 10:  # 最多等待10秒
                try:
                    response = self.telnet.read_until(b"$", timeout=1).decode('utf-8')
                    buffer += response
                    if '$' in response:  # 找到命令提示符
                        break
                except EOFError:
                    logger.error("连接已断开")
                    self._disconnect()
                    raise Exception("连接已断开")
                except socket.timeout:
                    continue
            
            # 处理响应
            lines = buffer.split('\n')
            # 移除命令回显和最后的提示符
            result = '\n'.join(line for line in lines[1:-1] if line.strip())
            logger.debug(f"命令执行结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"执行命令时发生错误: {e}")
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

    def get_stack_trace_by_method(self, pid: int, class_pattern: str, method_pattern: str) -> str:
        """获取方法的调用路径
        
        Args:
            pid: 进程ID
            class_pattern: 类名表达式
            method_pattern: 方法名表达式
        """
        return self._execute_command(pid, f"stack {class_pattern} {method_pattern}")

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

    def search_method(self, pid: int, class_pattern: str, method_pattern: str = None) -> str:
        """查看类的方法信息
        
        Args:
            pid: 进程ID
            class_pattern: 类名表达式
            method_pattern: 可选的方法名表达式
        """
        command = f"sm {class_pattern}"
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