# JVM MCP Server Package

基于Arthas的JVM监控MCP服务器实现，提供了一个简单易用的Python接口来监控和分析Java进程。

## 功能特点

- 自动下载和管理Arthas工具
- 支持本地和远程Java进程监控
- 提供Java进程列表查询
- 实时获取JVM线程信息
- 监控JVM内存使用情况
- 获取线程堆栈信息
- 查询类加载信息
- 支持AI驱动的JVM性能分析

## 系统要求

- Python 3.7+
- Java Runtime Environment (JRE) 8+
- 网络连接（用于下载Arthas）
- 如果使用远程模式，需要目标服务器的SSH访问权限

## 安装

```bash
pip install jvm-mcp-server
```

> 本地开发安装

```bash
git clone https://github.com/xzq-xu/jvm-mcp-server.git
cd jvm-mcp-server 
uv pip install -e .
```

## 快速开始

1. 本地模式启动：

```python
from jvm_mcp_server import JvmMcpServer

server = JvmMcpServer()
server.run()
```

2. 远程模式启动（通过SSH连接）：

首先设置环境变量：
```bash
# Linux/Mac
export ARTHAS_SSH_HOST=user@remote-host
export ARTHAS_SSH_PORT=22  # 可选，默认22
export ARTHAS_SSH_PASSWORD=your-password  # 如果使用密码认证

# Windows PowerShell
$env:ARTHAS_SSH_HOST="user@remote-host"
$env:ARTHAS_SSH_PORT="22"  # 可选，默认22
$env:ARTHAS_SSH_PASSWORD="your-password"  # 如果使用密码认证
```

然后启动服务器：
```python
from jvm_mcp_server import JvmMcpServer

server = JvmMcpServer()
server.run()
```

3. 使用MCP工具：

```python
# 获取所有Java进程列表
processes = server.mcp.tools.list_java_processes()

# 获取特定进程的JVM状态
status = server.mcp.tools.get_jvm_status(pid=12345)

# 获取线程信息
thread_info = server.mcp.tools.get_thread_info(pid=12345)
```

> 在cursor中使用
``` bash
uv --directory D:/personal/jvm-mcp-server run --env-file D:/personal/jvm-mcp-server/.env jvm-mcp-server
## --directory D:/personal/jvm-mcp-server 为项目位置 
### --env-file D:/personal/jvm-mcp-server/.env  指定配置文件  


```


## 可用工具

### list_java_processes()
列出所有运行中的Java进程。
- 返回值：包含进程信息的字典列表，每个字典包含：
  - pid: 进程ID
  - name: 进程名称
  - args: 进程参数

### get_thread_info(pid: int)
获取指定进程的线程信息。
- 参数：
  - pid: Java进程ID
- 返回值：包含线程信息的字典

### get_jvm_info(pid: int)
获取JVM基础信息。
- 参数：
  - pid: Java进程ID
- 返回值：包含JVM信息的字典

### get_memory_info(pid: int)
获取内存使用情况。
- 参数：
  - pid: Java进程ID
- 返回值：包含内存使用信息的字典

### get_stack_trace(pid: int, thread_name: str)
获取指定线程的堆栈信息。
- 参数：
  - pid: Java进程ID
  - thread_name: 线程名称
- 返回值：包含堆栈信息的字典

### get_class_info(pid: int, class_pattern: str)
获取类信息。
- 参数：
  - pid: Java进程ID
  - class_pattern: 类名匹配模式
- 返回值：包含类信息的字典

### get_jvm_status(pid: Optional[int] = None)
获取JVM整体状态报告。
- 参数：
  - pid: 可选的进程ID，如果不指定则自动选择第一个非arthas的Java进程
- 返回值：包含完整JVM状态信息的字典

## AI分析功能

服务器内置了AI驱动的JVM性能分析功能，可以自动分析JVM状态并提供优化建议。分析内容包括：

1. JVM整体健康状况
2. 内存使用情况和潜在的内存问题
3. 线程状态和可能的死锁
4. 性能优化建议
5. 需要关注的警告信息

## 注意事项

1. 确保运行环境中已安装Java
2. 首次运行时会自动下载Arthas工具（arthas将被下载的家目录下，可以提前下载（命名为arthas-boot.jar））
3. 需要目标Java进程的访问权限
4. 远程模式需要SSH访问权限和适当的用户权限
5. 建议在开发环境中使用，生产环境使用需谨慎评估

## 问题反馈

如遇到问题，请提交Issue或Pull Request。

## 许可证

MIT License 