# JVM MCP Server

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/JDK-8+-green.svg" alt="JDK Version">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

[English](README.md) | [中文](README_zh.md)

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/xzq-xu-jvm-mcp-server-badge.png)](https://mseep.ai/app/xzq-xu-jvm-mcp-server)


A lightweight JVM monitoring and diagnostic MCP (Multi-Agent Communication Protocol) server implementation based on native JDK tools. Provides AI agents with powerful capabilities to monitor and analyze Java applications without requiring third-party tools like Arthas.

## Features

- **Zero Dependencies**: Uses only native JDK tools (jps, jstack, jmap, etc.)
- **Lightweight**: Minimal resource consumption compared to agent-based solutions
- **High Compatibility**: Works with all Java versions and platforms
- **Non-Intrusive**: No modifications to target applications required
- **Secure**: Uses only JDK certified tools and commands
- **Remote Monitoring**: Support for both local and remote JVM monitoring via SSH

## Core Capabilities

### Basic Monitoring
- Java process listing and identification
- JVM basic information retrieval
- Memory usage monitoring
- Thread information and stack trace analysis
- Class loading statistics
- Detailed class structure information

### Advanced Features
- Method call path analysis
- Class decompilation
- Method search and inspection
- Method invocation monitoring
- Logger level management
- System resource dashboard

## System Requirements

- Python 3.6+
- JDK 8+
- Linux/Unix/Windows OS
- SSH access (for remote monitoring)

## Installation

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# or
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install the package
uv pip install jvm-mcp-server
```

### Using pip

```bash
pip install jvm-mcp-server
```

### From Source

```bash
# Clone the repository
git clone https://github.com/your-repo/jvm-mcp-server.git
cd jvm-mcp-server

# Using uv (recommended)
uv venv  # Create virtual environment
uv sync  # Install dependencies

# Or install in development mode
uv pip install -e .
```

## Quick Start

### Starting the Server

#### Using uv (Recommended)

```bash
# Local mode
uv run jvm-mcp-server

# Using environment variables file for remote mode
uv run --env-file .env jvm-mcp-server

# In specific directory
uv --directory /path/to/project run --env-file .env jvm-mcp-server
```

#### Using uvx

```bash
# Local mode
uvx run jvm-mcp-server

# With environment variables
uvx run --env-file .env jvm-mcp-server
```

#### Using Python directly

```python
from jvm_mcp_server import JvmMcpServer

# Local mode
server = JvmMcpServer()
server.run()

# Remote mode (via environment variables)
# Set SSH_HOST, SSH_PORT, SSH_USER, SSH_PASSWORD or SSH_KEY
import os
os.environ['SSH_HOST'] = 'user@remote-host'
os.environ['SSH_PORT'] = '22'
server = JvmMcpServer()
server.run()
```

### Using with MCP Configuration

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

## Available Tools

JVM-MCP-Server provides a comprehensive set of tools for JVM monitoring and diagnostics:

- `list_java_processes`: List all Java processes
- `get_thread_info`: Get thread information for a specific process
- `get_jvm_info`: Get JVM basic information
- `get_memory_info`: Get memory usage information
- `get_stack_trace`: Get thread stack trace information
- `get_class_info`: Get detailed class information including structure
- `get_stack_trace_by_method`: Get method call path
- `decompile_class`: Decompile class source code
- `search_method`: Search for methods in classes
- `watch_method`: Monitor method invocations
- `get_logger_info`: Get logger information
- `set_logger_level`: Set logger levels
- `get_dashboard`: Get system resource dashboard
- `get_jcmd_output`: Execute JDK jcmd commands
- `get_jstat_output`: Execute JDK jstat commands

For detailed documentation on each tool, see [Available Tools](./doc/available_tools.md).

## Architecture

JVM-MCP-Server is built on a modular architecture:

1. **Command Layer**: Wraps JDK native commands
2. **Executor Layer**: Handles local and remote command execution
3. **Formatter Layer**: Processes and formats command output
4. **MCP Interface**: Exposes functionality through FastMCP protocol

### Key Components

- `BaseCommand`: Abstract base class for all commands
- `CommandExecutor`: Interface for command execution (local and remote)
- `OutputFormatter`: Interface for formatting command output
- `JvmMcpServer`: Main server class that registers all tools

## Development Status

The project is in active development. See [Native_TODO.md](Native_TODO.md) for current progress.

### Completed
- Core architecture and command framework
- Basic commands implementation (jps, jstack, jmap, jinfo, jcmd, jstat)
- Class information retrieval system
- MCP tool parameter type compatibility fixes

### In Progress
- Caching mechanism
- Method tracing
- Performance monitoring
- Error handling improvements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- JDK tools documentation
- FastMCP protocol specification
- Contributors and testers 