# JVM MCP Server

基于Arthas的JVM监控MCP服务器实现，提供了一个给ai监控和分析Java进程的mcp。

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
## linux shell
curl -LsSf https://astral.sh/uv/install.sh | sh
## 或者 使用 pip 安装
pip install uv
## 或者 使用pipx安装，前提是已有pipx
pipx install uv 
## windows powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

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
# 同步项目依赖
uv sync
```

### 4. 配置环境变量（可选，用于远程连接）

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
创建`.env`文件并添加以上环境变量


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

使用配置文件
```json 
{
    "mcpServers": {
      "jvm-mcp-server": {
        "command": "uv",
        "args": [
          "--directory",
          "/path/to/jvm-mcp-server",
          "run",
          "--env-file",
          "/path/to/jvm-mcp-server/.env",
          "jvm-mcp-server"
        ]
      }
    }
}
```
不使用配置文件，将读取系统环境变量的值，如果没有将监听本地线程
```json 
{
    "mcpServers": {
      "jvm-mcp-server": {
        "command": "uv",
        "args": [
          "--directory",
          "/path/to/jvm-mcp-server",
          "run",
          "jvm-mcp-server"
        ]
      }
    }
}
```

## 可用工具

[可用工具列表](./doc/available_tools.md)


## 注意事项

1. 确保运行环境中已安装Java
2. 首次运行时会自动下载Arthas工具（arthas将被下载的家目录下，可以提前下载（命名为arthas-boot.jar））
3. 需要目标Java进程的访问权限
4. 远程模式需要SSH访问权限和适当的用户权限
5. 建议在开发环境中使用，生产环境使用需谨慎评估

## 问题反馈

如遇到问题，请提交Issue或Pull Request。

## 许可证

[MIT License](./LICENSE) 
