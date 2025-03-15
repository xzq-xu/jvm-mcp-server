# JVM MCP Server

[English](README.md) | [中文](README_zh.md)

A JVM monitoring MCP server implementation based on Arthas, providing a simple and easy-to-use Python interface for monitoring and analyzing Java processes.

## Features

- Automatic download and management of Arthas tools
- Support for local and remote Java process monitoring
- Java process list querying
- Real-time JVM thread information
- JVM memory usage monitoring
- Thread stack trace information
- Class loading information querying
- Support for class and method decompilation
- Method call monitoring
- Dynamic log level adjustment
- AI-driven JVM performance analysis

## System Requirements

- Python 3.10+
- Java Runtime Environment (JRE) 8+
- Network connection (for downloading Arthas)
- SSH access to target server (if using remote mode)

## Installation and Environment Setup

### 1. Install uv tool

```bash
## linux shell
curl -LsSf https://astral.sh/uv/install.sh | sh
## or install using pip
pip install uv
## or install using pipx (if you have pipx installed)
pipx install uv 
## windows powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone the project

```bash
git clone https://github.com/xzq-xu/jvm-mcp-server.git
cd jvm-mcp-server
```

### 3. Initialize project environment using uv

```bash
# Create virtual environment
uv venv
# Sync project dependencies
uv sync
```

### 4. Configure environment variables (Optional, for remote connections)

Create a `.env` file and add the following configurations:

```bash
# Linux/Mac
ARTHAS_SSH_HOST=user@remote-host
ARTHAS_SSH_PORT=22  # Optional, default is 22
ARTHAS_SSH_PASSWORD=your-password  # If using password authentication

# Windows PowerShell
$env:ARTHAS_SSH_HOST="user@remote-host"
$env:ARTHAS_SSH_PORT="22"  # Optional, default is 22
$env:ARTHAS_SSH_PASSWORD="your-password"  # If using password authentication
```

## Quick Start

1. Start the server using uv:

```bash
# Start in local mode
uv run jvm-mcp-server

# Start with environment file (if remote connection is configured)
uv run --env-file .env jvm-mcp-server

# Start in a specific directory (if needed)
uv --directory /path/to/project run --env-file .env jvm-mcp-server
```

2. Use in Python code:

```python
from jvm_mcp_server import JvmMcpServer

server = JvmMcpServer()
server.run()
```

3. Using MCP tools:

Using configuration file:
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
Without using configuration file, it will read system environment variables, if not present it will monitor local threads:
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

## Available Tools

[Available Tools List](./doc/available_tools.md)

## Important Notes

1. Ensure Java is installed in the runtime environment
2. Arthas tool will be automatically downloaded on first run (arthas will be downloaded to home directory, can be downloaded in advance and named as arthas-boot.jar)
3. Requires access permissions to target Java process
4. Remote mode requires SSH access and appropriate user permissions
5. Recommended for use in development environment, production use should be carefully evaluated

## Feedback

If you encounter any issues, please submit an Issue or Pull Request.

## License

[MIT License](./LICENSE) 