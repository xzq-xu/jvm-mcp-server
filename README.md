# JVM-MCP-Server Native分支

## 项目简介
JVM-MCP-Server的Native分支旨在提供一个不依赖Arthas的JVM监控解决方案。通过使用JDK原生工具（如jps、jstack、jmap等）和系统命令，实现与Arthas类似的功能，为Java应用提供轻量级的监控和诊断能力。

## 实现原理
不同于主分支使用Arthas作为核心实现，Native分支直接调用以下工具和命令：

### JDK工具
- jps：用于列出Java进程
- jstack：获取线程堆栈信息
- jmap：获取内存相关信息
- jinfo：获取JVM配置信息
- jstat：获取JVM统计信息
- javap：用于类信息查看和反编译

### 系统命令
- ps：进程管理
- top：系统资源监控
- grep/awk：文本处理
- kill：进程控制

## 主要功能

### 基础监控
1. Java进程列表查看
2. JVM基础信息获取
3. 内存使用情况监控
4. 线程信息查看
5. 堆栈信息获取
6. 类信息查看

### 高级特性
1. 方法调用路径分析
2. 类反编译
3. 方法搜索
4. 方法监控
5. 日志级别管理
6. 系统资源面板

## 优势特点
1. 零依赖：不需要额外的第三方工具
2. 轻量级：最小化资源占用
3. 高兼容性：适用于所有Java版本
4. 低侵入性：不需要修改目标应用
5. 安全性高：只使用JDK认证的工具

## 使用方法

### 环境要求
- JDK 8及以上版本
- Python 3.6及以上版本
- Linux/Unix/Windows系统

### 安装步骤
1. 克隆项目并切换到native分支：
```bash
git clone https://github.com/your-repo/jvm-mcp-server.git
cd jvm-mcp-server
git checkout native
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行服务：
```bash
python src/main.py
```

### 配置说明
配置文件位于`config/`目录下，主要包括：
- config.json：基础配置
- logging.json：日志配置
- security.json：安全配置

## 开发进度
请查看[Native_TODO.md](Native_TODO.md)文件了解当前开发进度。

## 注意事项
1. 需要确保运行用户具有足够的权限执行JDK工具
2. 在生产环境使用时需要注意性能开销
3. 某些功能在不同操作系统上可能有差异
4. 建议在使用前先在测试环境验证

## 性能考虑
1. 命令执行采用异步方式
2. 实现了结果缓存机制
3. 支持批量数据处理
4. 可配置采样频率
5. 内置资源使用限制

## 贡献指南
1. Fork本仓库
2. 创建功能分支
3. 提交变更
4. 发起Pull Request

## 问题反馈
如果您在使用过程中遇到任何问题，请：
1. 查看[常见问题](docs/FAQ.md)
2. 提交[Issue](https://github.com/your-repo/jvm-mcp-server/issues)
3. 通过[邮件列表](mailto:your-email@example.com)联系我们

## 许可证
本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。 