"""JVM MCP Server测试"""

import unittest
from unittest.mock import patch
from jvm_mcp_server.server import _run_jps_command, JvmMcpServer

class TestJvmMcpServer(unittest.TestCase):
    """JVM MCP Server测试类"""

    @patch('subprocess.run')
    def test_run_jps_command(self, mock_run):
        """测试jps命令执行"""
        # 模拟jps命令输出
        mock_run.return_value.stdout = """
1234 org.example.MainClass -Xmx1g
5678 jdk.jcmd.JCmd
"""
        mock_run.return_value.returncode = 0

        # 执行命令
        output = _run_jps_command()

        # 验证命令调用
        mock_run.assert_called_once_with(
            ['jps', '-l', '-v'],
            capture_output=True,
            text=True,
            check=True
            )

        # 验证输出
        self.assertIn('1234', output)
        self.assertIn('org.example.MainClass', output)
        self.assertIn('-Xmx1g', output)

    @patch('jvm_mcp_server.server._run_jps_command')
    def test_list_java_processes(self, mock_run_jps):
        """测试list_java_processes工具"""
        # 模拟jps命令输出
        mock_run_jps.return_value = """
1234 org.example.MainClass -Xmx1g
5678 jdk.jcmd.JCmd
"""

        # 创建服务器实例
        server = JvmMcpServer()

        # 获取Java进程列表
        processes = server.mcp.tools['list_java_processes']()

        # 验证结果
        self.assertEqual(len(processes), 2)

        # 验证第一个进程信息
        self.assertEqual(processes[0]['pid'], '1234')
        self.assertEqual(processes[0]['name'], 'org.example.MainClass')
        self.assertEqual(processes[0]['args'], '-Xmx1g')

        # 验证第二个进程信息
        self.assertEqual(processes[1]['pid'], '5678')
        self.assertEqual(processes[1]['name'], 'jdk.jcmd.JCmd')
        self.assertEqual(processes[1]['args'], '')


if __name__ == '__main__':
    unittest.main()
