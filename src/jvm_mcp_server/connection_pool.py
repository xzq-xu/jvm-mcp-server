"""Arthas连接池管理模块"""

import threading
import time
import logging
import os
from typing import Dict, Optional, List, TYPE_CHECKING, Any
from queue import Queue, Empty
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .arthas import ArthasClient

@dataclass
class PooledConnection:
    """连接池中的连接对象"""
    client: Any  # 使用Any类型避免循环导入
    pid: int
    created_at: float
    last_used_at: float
    is_busy: bool = False
    health_check_count: int = 0
    failed_count: int = 0

class ArthasConnectionPool:
    """Arthas连接池管理类"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, 
                 max_size: int = 5,
                 min_size: int = 1,
                 connection_timeout: int = 5,
                 idle_timeout: int = 300,
                 max_lifetime: int = 3600,
                 health_check_interval: int = 60):
        """
        初始化连接池
        
        Args:
            max_size: 最大连接数
            min_size: 最小连接数
            connection_timeout: 获取连接超时时间(秒)
            idle_timeout: 空闲连接超时时间(秒)
            max_lifetime: 连接最大生命周期(秒)
            health_check_interval: 健康检查间隔(秒)
        """
        if not hasattr(self, '_initialized'):
            self.max_size = max_size
            self.min_size = min_size
            self.connection_timeout = connection_timeout
            self.idle_timeout = idle_timeout
            self.max_lifetime = max_lifetime
            self.health_check_interval = health_check_interval
            
            self._connections: Dict[int, List[PooledConnection]] = {}
            self._available: Dict[int, Queue[PooledConnection]] = {}
            
            # 从环境变量读取SSH连接参数
            self.ssh_host = os.getenv('ARTHAS_SSH_HOST')
            self.ssh_port = int(os.getenv('ARTHAS_SSH_PORT', '22'))
            self.ssh_password = os.getenv('ARTHAS_SSH_PASSWORD')
            
            # 启动健康检查线程
            self._stop_health_check = threading.Event()
            self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self._health_check_thread.start()
            
            self._initialized = True
            logger.info(f"Arthas连接池已初始化，最大连接数: {max_size}")
            
    def get_connection(self, pid: int) -> Optional[PooledConnection]:
        """
        获取一个连接
        
        Args:
            pid: 目标进程ID
            
        Returns:
            PooledConnection: 池化的连接对象
            
        Raises:
            TimeoutError: 超时未获取到连接
            Exception: 其他错误
        """
        start_time = time.time()
        logger.info(f"开始获取连接 pid={pid}")
        
        # 初始化连接池和队列（如果不存在）
        with self._lock:
            if pid not in self._connections:
                logger.info(f"为进程 {pid} 初始化连接池")
                self._connections[pid] = []
                self._available[pid] = Queue()
        
        while time.time() - start_time < self.connection_timeout:
            try:
                # 尝试从可用连接队列中获取连接
                if pid in self._available and not self._available[pid].empty():
                    conn = self._available[pid].get_nowait()
                    logger.debug(f"从连接池获取到连接 pid={pid}")
                    
                    # 验证连接是否有效
                    if self._is_connection_valid(conn):
                        conn.is_busy = True
                        conn.last_used_at = time.time()
                        logger.info(f"复用有效连接 pid={pid}")
                        return conn
                    else:
                        # 移除无效连接
                        logger.warning(f"移除无效连接 pid={pid}")
                        self._remove_connection(conn)
                
                # 检查是否可以创建新连接
                with self._lock:
                    current_connections = len(self._connections.get(pid, []))
                    if current_connections < self.max_size:
                        try:
                            logger.info(f"创建新连接 pid={pid}, 当前连接数={current_connections}")
                            new_conn = self._create_connection(pid)
                            if new_conn:
                                self._connections[pid].append(new_conn)
                                new_conn.is_busy = True
                                return new_conn
                        except Exception as e:
                            logger.error(f"创建新连接失败: {e}")
                            time.sleep(0.5)  # 添加短暂延迟避免快速重试
                    else:
                        logger.warning(f"连接池已满 pid={pid}, 当前连接数={current_connections}")
                
            except Empty:
                pass
            except Exception as e:
                logger.error(f"获取连接时发生错误: {e}")
            
            # 等待一段时间后重试
            time.sleep(0.1)
        
        error_msg = f"获取连接超时 pid={pid}, 等待时间={self.connection_timeout}秒"
        logger.error(error_msg)
        raise TimeoutError(error_msg)
    
    def return_connection(self, connection: PooledConnection):
        """归还连接到连接池"""
        with self._lock:
            if not self._is_connection_valid(connection):
                self._remove_connection(connection)
                return
                
            connection.is_busy = False
            connection.last_used_at = time.time()
            self._available[connection.pid].put(connection)
            logger.debug(f"归还连接 pid={connection.pid}")
    
    def _create_connection(self, pid: int) -> PooledConnection:
        """创建新的连接"""
        # 延迟导入 ArthasClient，避免循环导入
        from .arthas import ArthasClient
        client = ArthasClient(
            ssh_host=self.ssh_host,
            ssh_port=self.ssh_port,
            ssh_password=self.ssh_password
        )
        try:
            # 连接到目标进程
            client._attach_to_process(pid)
            now = time.time()
            conn = PooledConnection(
                client=client,
                pid=pid,
                created_at=now,
                last_used_at=now
            )
            logger.info(f"成功创建新连接 pid={pid}")
            return conn
        except Exception as e:
            logger.error(f"创建连接失败 pid={pid}: {e}")
            try:
                client._disconnect()
            except:
                pass
            raise
    
    def _is_connection_valid(self, conn: PooledConnection) -> bool:
        """检查连接是否有效"""
        now = time.time()
        
        # 检查连接是否过期
        if now - conn.created_at > self.max_lifetime:
            logger.info(f"连接已过期 pid={conn.pid}")
            return False
            
        # 检查空闲时间
        if not conn.is_busy and now - conn.last_used_at > self.idle_timeout:
            logger.info(f"连接空闲超时 pid={conn.pid}")
            return False
            
        # 检查失败次数
        if conn.failed_count > 3:
            logger.info(f"连接失败次数过多 pid={conn.pid}")
            return False
            
        return True
    
    def _remove_connection(self, conn: PooledConnection):
        """移除无效连接"""
        with self._lock:
            if conn.pid in self._connections and conn in self._connections[conn.pid]:
                self._connections[conn.pid].remove(conn)
                logger.info(f"移除失效连接 pid={conn.pid}")
                
            try:
                conn.client._disconnect()
            except Exception as e:
                logger.error(f"断开连接时发生错误: {e}")
    
    def _health_check_loop(self):
        """健康检查循环"""
        while not self._stop_health_check.is_set():
            try:
                self._check_all_connections()
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
            finally:
                # 使用Event的wait而不是time.sleep，这样可以更快地响应停止信号
                self._stop_health_check.wait(self.health_check_interval)
    
    def _check_all_connections(self):
        """检查所有连接的健康状态"""
        with self._lock:
            for pid, connections in self._connections.items():
                for conn in connections[:]:  # 使用切片创建副本以避免修改迭代器
                    if not conn.is_busy:  # 只检查非忙碌的连接
                        if not self._is_connection_valid(conn):
                            self._remove_connection(conn)
                        else:
                            try:
                                # 发送简单的测试命令
                                conn.client._execute_command(conn.pid, "version")
                                conn.health_check_count += 1
                                conn.failed_count = 0  # 重置失败计数
                            except Exception as e:
                                logger.warning(f"连接健康检查失败 pid={pid}: {e}")
                                conn.failed_count += 1
                                if conn.failed_count > 3:
                                    self._remove_connection(conn)
    
    def shutdown(self):
        """关闭连接池"""
        logger.info("正在关闭连接池...")
        self._stop_health_check.set()
        self._health_check_thread.join()
        
        with self._lock:
            for pid, connections in self._connections.items():
                for conn in connections:
                    try:
                        conn.client._disconnect()
                    except:
                        pass
            self._connections.clear()
            self._available.clear()
        
        logger.info("连接池已关闭") 