import unittest
import os
import logging
from jvm_mcp_server.arthas import ArthasClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestArthasClient(unittest.TestCase):
    """Arthas客户端测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 获取环境变量中的远程连接信息
        cls.ssh_host = os.getenv('ARTHAS_SSH_HOST')
        cls.ssh_port = int(os.getenv('ARTHAS_SSH_PORT', '22'))
        cls.ssh_password = os.getenv('ARTHAS_SSH_PASSWORD')
        
        # 创建本地客户端实例
        cls.local_client = ArthasClient()
        
        # 如果有远程连接信息，创建远程客户端实例
        if cls.ssh_host:
            cls.remote_client = ArthasClient(
                ssh_host=cls.ssh_host,
                ssh_port=cls.ssh_port,
                ssh_password=cls.ssh_password
            )
        else:
            logger.warning("未配置远程连接信息，跳过远程测试")
            cls.remote_client = None

    def setUp(self):
        """每个测试用例开始前执行"""
        # 获取一个可用的Java进程ID
        self.local_pid = self._get_first_java_pid(self.local_client)
        if self.remote_client:
            self.remote_pid = self._get_first_java_pid(self.remote_client)
    
    def _get_first_java_pid(self, client: ArthasClient) -> int:
        """获取第一个可用的Java进程ID"""
        processes = client.list_java_processes()
        for line in processes.splitlines():
            if line and 'jps' not in line.lower():  # 排除jps进程本身
                return int(line.split()[0])
        raise Exception("未找到可用的Java进程")

    def test_local_basic_commands(self):
        """测试本地基本命令"""
        logger.info("=== 测试本地基本命令 ===")
        
        # 测试获取版本信息
        version = self.local_client.get_version(self.local_pid)
        self.assertIsNotNone(version)
        logger.info(f"本地版本信息: {version}")
        
        # 测试获取JVM信息
        jvm_info = self.local_client.get_jvm_info(self.local_pid)
        self.assertIsNotNone(jvm_info)
        logger.info(f"本地JVM信息: {jvm_info}")
        
        # 测试获取线程信息
        thread_info = self.local_client.get_thread_info(self.local_pid)
        self.assertIsNotNone(thread_info)
        logger.info(f"本地线程信息: {thread_info}")
        
        # 测试获取内存信息
        memory_info = self.local_client.get_memory_info(self.local_pid)
        self.assertIsNotNone(memory_info)
        logger.info(f"本地内存信息: {memory_info}")

    def test_local_advanced_commands(self):
        """测试本地高级命令"""
        logger.info("=== 测试本地高级命令 ===")
        
        # 测试获取类信息
        class_info = self.local_client.get_class_info(self.local_pid, "java.lang.String")
        self.assertIsNotNone(class_info)
        logger.info(f"本地类信息: {class_info}")
        
        # 测试获取方法信息
        method_info = self.local_client.search_method(self.local_pid, "java.lang.String", "substring")
        self.assertIsNotNone(method_info)
        logger.info(f"本地方法信息: {method_info}")
        
        # 测试反编译
        decompile = self.local_client.decompile_class(self.local_pid, "java.lang.String", "substring")
        self.assertIsNotNone(decompile)
        logger.info(f"本地反编译信息: {decompile}")

    @unittest.skipIf(not os.getenv('ARTHAS_SSH_HOST'), "未配置远程连接信息")
    def test_remote_basic_commands(self):
        """测试远程基本命令"""
        logger.info("=== 测试远程基本命令 ===")
        
        # 测试获取版本信息
        version = self.remote_client.get_version(self.remote_pid)
        self.assertIsNotNone(version)
        logger.info(f"远程版本信息: {version}")
        
        # 测试获取JVM信息
        jvm_info = self.remote_client.get_jvm_info(self.remote_pid)
        self.assertIsNotNone(jvm_info)
        logger.info(f"远程JVM信息: {jvm_info}")
        
        # 测试获取线程信息
        thread_info = self.remote_client.get_thread_info(self.remote_pid)
        self.assertIsNotNone(thread_info)
        logger.info(f"远程线程信息: {thread_info}")
        
        # 测试获取内存信息
        memory_info = self.remote_client.get_memory_info(self.remote_pid)
        self.assertIsNotNone(memory_info)
        logger.info(f"远程内存信息: {memory_info}")

    @unittest.skipIf(not os.getenv('ARTHAS_SSH_HOST'), "未配置远程连接信息")
    def test_remote_advanced_commands(self):
        """测试远程高级命令"""
        logger.info("=== 测试远程高级命令 ===")
        
        # 测试获取类信息
        class_info = self.remote_client.get_class_info(self.remote_pid, "java.lang.String")
        self.assertIsNotNone(class_info)
        logger.info(f"远程类信息: {class_info}")
        
        # 测试获取方法信息
        method_info = self.remote_client.search_method(self.remote_pid, "java.lang.String", "substring")
        self.assertIsNotNone(method_info)
        logger.info(f"远程方法信息: {method_info}")
        
        # 测试反编译
        decompile = self.remote_client.decompile_class(self.remote_pid, "java.lang.String", "substring")
        self.assertIsNotNone(decompile)
        logger.info(f"远程反编译信息: {decompile}")

    def test_process_listing(self):
        """测试进程列表获取"""
        logger.info("=== 测试进程列表获取 ===")
        
        # 测试本地进程列表
        local_processes = self.local_client.list_java_processes()
        self.assertIsNotNone(local_processes)
        logger.info(f"本地进程列表: {local_processes}")
        
        # 测试远程进程列表（如果配置了远程连接）
        if self.remote_client:
            remote_processes = self.remote_client.list_java_processes()
            self.assertIsNotNone(remote_processes)
            logger.info(f"远程进程列表: {remote_processes}")

    def tearDown(self):
        """每个测试用例结束后执行"""
        if hasattr(self, 'local_client'):
            self.local_client._disconnect()
        if hasattr(self, 'remote_client') and self.remote_client:
            self.remote_client._disconnect()

if __name__ == '__main__':
    unittest.main() 