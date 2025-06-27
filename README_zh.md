# JVM-MCP-Server

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python 版本">
  <img src="https://img.shields.io/badge/JDK-8+-green.svg" alt="JDK 版本">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="许可证">
</p>

[English](README.md) | [中文](README_zh.md)

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/xzq-xu-jvm-mcp-server-badge.png)](https://mseep.ai/app/xzq-xu-jvm-mcp-server)


基于JDK原生工具的轻量级JVM监控和诊断MCP（多智能体通信协议）服务器实现。为AI智能体提供强大的Java应用监控和分析能力，无需依赖Arthas等第三方工具。

## 功能特点

- **零依赖**：仅使用JDK原生工具（jps、jstack、jmap等）
- **轻量级**：与基于代理的解决方案相比，资源消耗更小
- **高兼容性**：适用于所有Java版本和平台
- **低侵入性**：不需要修改目标应用
- **高安全性**：仅使用JDK认证的工具和命令
- **远程监控**：通过SSH支持本地和远程JVM监控

## 核心能力

### 基础监控
- Java进程列表查询和识别
- JVM基础信息获取
- 内存使用情况监控
- 线程信息和堆栈分析
- 类加载统计
- 详细的类结构信息

### 高级特性
- 方法调用路径分析
- 类反编译
- 方法搜索和检查
- 方法调用监控
- 日志级别管理
- 系统资源面板

## 系统要求

- Python 3.6+
- JDK 8+
- Linux/Unix/Windows系统
- SSH访问权限（用于远程监控）

## 安装方法

### 使用 uv 安装（推荐）

```bash
# 如果尚未安装 uv，请先安装
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# 或者
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# 安装包
uv pip install jvm-mcp-server
```

### 使用 pip 安装

```bash
pip install jvm-mcp-server
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/jvm-mcp-server.git
cd jvm-mcp-server

# 使用 uv（推荐）
uv venv  # 创建虚拟环境
uv sync  # 安装依赖

# 或者以开发模式安装
uv pip install -e .
```

## 快速开始

### 启动服务器

#### 使用 uv（推荐）

```bash
# 本地模式
uv run jvm-mcp-server

# 使用环境变量文件进行远程模式
uv run --env-file .env jvm-mcp-server

# 在指定目录下启动
uv --directory /path/to/project run --env-file .env jvm-mcp-server
```

#### 使用 uvx

```bash
# 本地模式
uvx run jvm-mcp-server

# 使用环境变量
uvx run --env-file .env jvm-mcp-server
```

#### 使用 Python 直接启动

```python
from jvm_mcp_server import JvmMcpServer

# 本地模式
server = JvmMcpServer()
server.run()

# 远程模式（通过环境变量）
# 设置 SSH_HOST, SSH_PORT, SSH_USER, SSH_PASSWORD 或 SSH_KEY
import os
os.environ['SSH_HOST'] = 'user@remote-host'
os.environ['SSH_PORT'] = '22'
server = JvmMcpServer()
server.run()
```

### 使用MCP配置

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

## 可用工具

JVM-MCP-Server提供了一套全面的JVM监控和诊断工具：

- `list_java_processes`：列出所有Java进程
- `get_thread_info`：获取特定进程的线程信息
- `get_jvm_info`：获取JVM基本信息
- `get_memory_info`：获取内存使用信息
- `get_stack_trace`：获取线程堆栈信息
- `get_class_info`：获取详细的类信息，包括结构
- `get_stack_trace_by_method`：获取方法调用路径
- `decompile_class`：反编译类源代码
- `search_method`：在类中搜索方法
- `watch_method`：监控方法调用
- `get_logger_info`：获取日志记录器信息
- `set_logger_level`：设置日志级别
- `get_dashboard`：获取系统资源面板
- `get_jcmd_output`：执行JDK jcmd命令
- `get_jstat_output`：执行JDK jstat命令

有关每个工具的详细文档，请参阅[可用工具](./doc/available_tools.md)。

## 架构设计

JVM-MCP-Server基于模块化架构构建：

1. **命令层**：封装JDK原生命令
2. **执行器层**：处理本地和远程命令执行
3. **格式化器层**：处理和格式化命令输出
4. **MCP接口**：通过FastMCP协议暴露功能

### 核心组件


- `BaseCommand`：所有命令的抽象基类
- `CommandExecutor`：命令执行接口（本地和远程）
- `OutputFormatter`：命令输出格式化接口
- `JvmMcpServer`：注册所有工具的主服务器类


## 开发状态

该项目正在积极开发中。请参阅[Native_TODO.md](Native_TODO.md)了解当前进度。

### 已完成
- 核心架构和命令框架
- 基本命令实现（jps、jstack、jmap、jinfo、jcmd、jstat）
- 类信息检索系统
- MCP工具参数类型兼容性修复

### 进行中
- 缓存机制
- 方法跟踪
- 性能监控
- 错误处理改进

## 参与贡献

欢迎贡献！请随时提交Pull Request。

1. Fork仓库
2. 创建功能分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m '添加一些惊人的功能'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 开启Pull Request

## 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 致谢

- JDK工具文档
- FastMCP协议规范
- 贡献者和测试者 
