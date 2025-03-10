"""JVM MCP Server入口点"""

from .server import JvmMcpServer

def main():
    """主函数"""
    server = JvmMcpServer()
    server.run()

if __name__ == "__main__":
    main() 