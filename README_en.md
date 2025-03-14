# JVM MCP Server

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
# Install uv using x-cmd
eval "$(curl https://get.x-cmd.com)"
x env use uv
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

# Install project dependencies
uv install
# or
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

```python
# Get list of all Java processes
processes = server.mcp.tools.list_java_processes()

# Get JVM status for a specific process
status = server.mcp.tools.get_jvm_status(pid=12345)

# Get thread information
thread_info = server.mcp.tools.get_thread_info(pid=12345)
```

## Available Tools

### list_java_processes()
Lists all running Java processes.
- Returns: A list of dictionaries containing process information:
  - pid: Process ID
  - name: Process name
  - args: Process arguments

### get_version(pid: int)
Get Arthas version information.
- Parameters:
  - pid: Java process ID
- Returns: Dictionary containing version information

### get_thread_info(pid: int)
Get thread information for a specified process.
- Parameters:
  - pid: Java process ID
- Returns: Dictionary containing thread information

### get_jvm_info(pid: int)
Get basic JVM information.
- Parameters:
  - pid: Java process ID
- Returns: Dictionary containing JVM information

### get_memory_info(pid: int)
Get memory usage information.
- Parameters:
  - pid: Java process ID
- Returns: Dictionary containing memory usage information

### get_stack_trace(pid: int, thread_name: str)
Get stack trace information for a specified thread.
- Parameters:
  - pid: Java process ID
  - thread_name: Thread name
- Returns: Dictionary containing stack trace information

### get_stack_trace_by_method(pid: int, class_pattern: str, method_pattern: str)
Get method call path.
- Parameters:
  - pid: Java process ID
  - class_pattern: Class name pattern
  - method_pattern: Method name pattern
- Returns: Dictionary containing method call path information

### decompile_class(pid: int, class_pattern: str, method_pattern: str = None)
Decompile source code of specified class.
- Parameters:
  - pid: Java process ID
  - class_pattern: Class name pattern
  - method_pattern: Optional method name, if specified only decompiles specific method
- Returns: Dictionary containing decompiled source code

### search_method(pid: int, class_pattern: str, method_pattern: str = None)
View method information of a class.
- Parameters:
  - pid: Java process ID
  - class_pattern: Class name pattern
  - method_pattern: Optional method name pattern
- Returns: Dictionary containing method information

### watch_method(pid: int, class_pattern: str, method_pattern: str, watch_params: bool = True, watch_return: bool = True, condition: str = None, max_times: int = 10)
Monitor method invocations.
- Parameters:
  - pid: Java process ID
  - class_pattern: Class name pattern
  - method_pattern: Method name pattern
  - watch_params: Whether to monitor parameters
  - watch_return: Whether to monitor return values
  - condition: Condition expression
  - max_times: Maximum number of monitoring times
- Returns: Dictionary containing method monitoring information

### get_logger_info(pid: int, name: str = None)
Get logger information.
- Parameters:
  - pid: Java process ID
  - name: Logger name
- Returns: Dictionary containing logger information

### set_logger_level(pid: int, name: str, level: str)
Set logger level.
- Parameters:
  - pid: Java process ID
  - name: Logger name
  - level: Log level (trace, debug, info, warn, error)
- Returns: Dictionary containing operation result

### get_dashboard(pid: int)
Get system real-time data dashboard.
- Parameters:
  - pid: Java process ID
- Returns: Dictionary containing real-time system data

### get_class_info(pid: int, class_pattern: str)
Get class information.
- Parameters:
  - pid: Java process ID
  - class_pattern: Class name pattern
- Returns: Dictionary containing class information

### get_jvm_status(pid: Optional[int] = None)
Get comprehensive JVM status report.
- Parameters:
  - pid: Optional process ID, if not specified, automatically selects the first non-arthas Java process
- Returns: Dictionary containing complete JVM status information

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