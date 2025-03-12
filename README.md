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
- 支持类和方法的反编译
- 支持方法调用监控
- 支持日志级别动态调整
- 支持AI驱动的JVM性能分析

## 系统要求

- Python 3.10+
- Java Runtime Environment (JRE) 8+
- 网络连接（用于下载Arthas）
- 如果使用远程模式，需要目标服务器的SSH访问权限

## 安装与环境配置

### 1. 安装uv工具

```bash
# 使用x-cmd安装uv
eval "$(curl https://get.x-cmd.com)"
x env use uv
```

### 2. 克隆项目

```bash
git clone https://github.com/xzq-xu/jvm-mcp-server.git
cd jvm-mcp-server
```

### 3. 使用uv初始化项目环境

```bash
# 创建虚拟环境
uv venv

# 安装项目依赖
uv install
# 或者
uv sync
```

### 4. 配置环境变量（可选，用于远程连接）

创建`.env`文件并添加以下配置：

```bash
# Linux/Mac
ARTHAS_SSH_HOST=user@remote-host
ARTHAS_SSH_PORT=22  # 可选，默认22
ARTHAS_SSH_PASSWORD=your-password  # 如果使用密码认证

# Windows PowerShell
$env:ARTHAS_SSH_HOST="user@remote-host"
$env:ARTHAS_SSH_PORT="22"  # 可选，默认22
$env:ARTHAS_SSH_PASSWORD="your-password"  # 如果使用密码认证
```

## 快速开始

1. 使用uv启动服务器：

```bash
# 本地模式启动
uv run jvm-mcp-server

# 使用环境变量文件启动（如果有配置远程连接）
uv run --env-file .env jvm-mcp-server

# 在指定目录下启动（如果需要）
uv --directory /path/to/project run --env-file .env jvm-mcp-server
```

2. 在Python代码中使用：

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

## 可用工具

### list_java_processes()
列出所有运行中的Java进程。
- 返回值：包含进程信息的字典列表，每个字典包含：
  - pid: 进程ID
  - name: 进程名称
  - args: 进程参数

### get_version(pid: int)
获取Arthas版本信息。
- 参数：
  - pid: Java进程ID
- 返回值：包含版本信息的字典

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

### get_stack_trace_by_method(pid: int, class_pattern: str, method_pattern: str)
获取方法的调用路径。
- 参数：
  - pid: Java进程ID
  - class_pattern: 类名表达式
  - method_pattern: 方法名表达式
- 返回值：包含方法调用路径的字典

### decompile_class(pid: int, class_pattern: str, method_pattern: str = None)
反编译指定类的源码。
- 参数：
  - pid: Java进程ID
  - class_pattern: 类名表达式
  - method_pattern: 可选的方法名，如果指定则只反编译特定方法
- 返回值：包含反编译源码的字典

### search_method(pid: int, class_pattern: str, method_pattern: str = None)
查看类的方法信息。
- 参数：
  - pid: Java进程ID
  - class_pattern: 类名表达式
  - method_pattern: 可选的方法名表达式
- 返回值：包含方法信息的字典

### watch_method(pid: int, class_pattern: str, method_pattern: str, watch_params: bool = True, watch_return: bool = True, condition: str = None, max_times: int = 10)
监控方法的调用情况。
- 参数：
  - pid: Java进程ID
  - class_pattern: 类名表达式
  - method_pattern: 方法名表达式
  - watch_params: 是否监控参数
  - watch_return: 是否监控返回值
  - condition: 条件表达式
  - max_times: 最大监控次数
- 返回值：包含方法监控信息的字典

### get_logger_info(pid: int, name: str = None)
获取logger信息。
- 参数：
  - pid: Java进程ID
  - name: logger名称
- 返回值：包含logger信息的字典

### set_logger_level(pid: int, name: str, level: str)
设置logger级别。
- 参数：
  - pid: Java进程ID
  - name: logger名称
  - level: 日志级别(trace, debug, info, warn, error)
- 返回值：包含操作结果的字典

### get_dashboard(pid: int)
获取系统实时数据面板。
- 参数：
  - pid: Java进程ID
- 返回值：包含系统实时数据的字典

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