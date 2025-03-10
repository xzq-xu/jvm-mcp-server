# JVM MCP Server

这是一个基于JVM的MCP（Model Context Protocol）服务器实现项目。该项目旨在为JVM平台提供标准化的MCP服务器实现，使得AI模型能够更好地与Java生态系统进行交互。

## 项目简介

MCP（Model Context Protocol）是一个开放协议，用于标准化应用程序如何向大语言模型（LLM）提供上下文。本项目提供了一个基于JVM的MCP服务器实现，支持与各种AI模型的交互。

## 特性

- 基于Arthas的JVM监控
- 实时进程状态查看
- 线程分析
- 内存使用监控
- 类加载信息查询
- AI辅助性能分析

## 项目结构

```
.
├── mcp.md                 # MCP协议详细介绍文档
├── arthas_mcp_server.py   # Arthas MCP服务器实现
├── mcp_server_demo.py     # Python版本的服务器演示代码
├── pyproject.toml         # Python项目配置文件
├── .venv/                 # Python虚拟环境
└── .vscode/              # VS Code配置文件
```

## 环境要求

- Python 3.8+
- Java 11+
- curl（用于下载Arthas）

## 快速开始

1. 克隆项目：
```bash
git clone [项目地址]
```

2. 安装依赖：
```bash
# 使用 uv 安装依赖
uv pip install -r requirements.txt
```

3. 运行Arthas MCP服务器：
```bash
python arthas_mcp_server.py
```

## 使用方法

### 工具（Tools）

1. 列出Java进程：
```python
processes = await mcp.invoke("list_java_processes")
```

2. 获取线程信息：
```python
thread_info = await mcp.invoke("get_thread_info", {"pid": 1234})
```

3. 获取JVM信息：
```python
jvm_info = await mcp.invoke("get_jvm_info", {"pid": 1234})
```

4. 获取JVM状态：
```python
# 获取默认Java进程的状态
status = await mcp.invoke("get_jvm_status")

# 获取指定进程的状态
status = await mcp.invoke("get_jvm_status", {"pid": 1234})
```

### 资源（Resources）

获取JVM状态：
```python
# 获取默认Java进程的状态
status = await mcp.get_resource("jvm://status")

# 获取指定进程的状态
status = await mcp.get_resource("jvm://status/1234")  # 1234为进程ID
```

### 提示（Prompts）

使用AI分析JVM状态：
```python
# 获取JVM分析提示（会自动分析默认Java进程）
prompt = await mcp.get_prompt("jvm_analysis_prompt")
```

## 文档

- [MCP协议介绍](mcp.md) - 详细的MCP协议说明文档

## 开发计划

- [x] 项目基础架构搭建
- [x] MCP协议文档编写
- [x] Arthas集成
- [x] 工具（Tools）接口实现
- [x] 资源（Resources）接口实现
- [x] 提示（Prompts）接口实现
- [ ] 完整的测试用例
- [ ] 性能优化
- [ ] 远程连接支持
- [ ] 更多Arthas命令支持

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。在提交代码前，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的测试用例
3. 更新了相关文档

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。 