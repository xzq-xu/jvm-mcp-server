# 可用工具

## 基础工具

### list_java_processes()
列出所有运行中的Java进程。
- **返回值**：包含进程信息的字典列表，每个字典包含：
  - `pid` (str): 进程ID
  - `name` (str): 进程名称
  - `args` (str): 进程参数

### get_thread_info(pid: str = "")
获取指定进程的线程信息。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
- **返回值**：包含线程信息的字典，包含以下字段：
  - `threads` (List[Dict]): 线程信息列表
  - `thread_count` (int): 线程数量
  - `raw_output` (str): 原始输出
  - `timestamp` (float): 时间戳
  - `success` (bool): 是否成功
  - `error` (Optional[str]): 错误信息

### get_jvm_info(pid: str = "")
获取JVM基础信息。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
- **返回值**：包含JVM信息的字典，包含以下字段：
  - `raw_output` (str): 原始输出
  - `timestamp` (float): 时间戳
  - `success` (bool): 是否成功
  - `error` (Optional[str]): 错误信息

### get_memory_info(pid: str = "")
获取内存使用情况。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
- **返回值**：包含内存使用信息的字典，包含以下字段：
  - `raw_output` (str): 原始输出
  - `timestamp` (float): 时间戳
  - `success` (bool): 是否成功
  - `error` (Optional[str]): 错误信息

### get_stack_trace(pid: str = "", thread_id: str = "", top_n: str = "5", find_blocking: bool = False, interval: str = "", show_all: bool = False)
获取线程堆栈信息。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `thread_id` (str): 线程ID，使用字符串形式。支持十六进制（如："0x2c03"）
  - `top_n` (str): 显示前N个线程，使用字符串形式（如："5"），默认值为"5"
  - `find_blocking` (bool): 是否只查找阻塞线程（BLOCKED状态或等待锁的线程）
  - `interval` (str): 采样间隔，使用字符串形式（如："1000"表示1秒）
  - `show_all` (bool): 是否显示所有信息
- **返回值**：包含线程堆栈信息的字典，包含以下字段：
  - `threads` (List[Dict]): 线程信息列表
  - `thread_count` (int): 线程数量
  - `raw_output` (str): 原始输出
  - `timestamp` (float): 时间戳
  - `success` (bool): 是否成功
  - `error` (Optional[str]): 错误信息

## 高级工具

### get_class_info(pid: str = "", class_pattern: str = "", show_detail: bool = False, show_field: bool = False, use_regex: bool = False, depth: str = "", classloader_hash: Optional[str] = None, classloader_class: Optional[str] = None, max_matches: str = "")
获取类信息 - 使用jmap -histo和javap命令获取完整的类信息。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `class_pattern` (str): 类名表达式匹配
  - `show_detail` (bool): 是否显示详细信息，默认false
  - `show_field` (bool): 是否显示成员变量信息(需要show_detail=True)，默认false
  - `use_regex` (bool): 是否使用正则表达式匹配，默认false
  - `depth` (str): 属性遍历深度（暂未使用）
  - `classloader_hash` (Optional[str]): 指定class的ClassLoader的hashcode（暂未使用）
  - `classloader_class` (Optional[str]): 指定执行表达式的ClassLoader的class name（暂未使用）
  - `max_matches` (str): 匹配类的最大数量，使用字符串形式（如："50"）
- **返回值**：包含类信息的字典，包含以下字段：
  - `classes` (List[Dict]): 类信息列表
  - `total_matches` (int): 匹配的类总数
  - `limited_by_max` (bool): 是否因为达到最大匹配数而限制结果
  - `success` (bool): 是否成功
  - `error` (Optional[str]): 错误信息

### get_stack_trace_by_method(pid: str = "", class_pattern: str = "", method_pattern: str = "", condition: Optional[str] = None, use_regex: bool = False, max_matches: str = "", max_times: str = "")
获取方法的调用路径。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `class_pattern` (str): 类名表达式匹配
  - `method_pattern` (str): 方法名表达式匹配
  - `condition` (Optional[str]): 条件表达式，例如：'params[0]<0' 或 '#cost>10'
  - `use_regex` (bool): 是否开启正则表达式匹配，默认为通配符匹配
  - `max_matches` (str): Class最大匹配数量，使用字符串形式（如："50"）
  - `max_times` (str): 执行次数限制，使用字符串形式
- **返回值**：包含方法调用路径信息的字典（暂未实现）

### decompile_class(pid: str = "", class_pattern: str = "", method_pattern: Optional[str] = None)
反编译指定类的源码。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `class_pattern` (str): 类名表达式匹配
  - `method_pattern` (Optional[str]): 可选的方法名表达式
- **返回值**：包含反编译源码的字典（暂未实现）

### search_method(pid: str = "", class_pattern: str = "", method_pattern: Optional[str] = None, show_detail: bool = False, use_regex: bool = False, classloader_hash: Optional[str] = None, classloader_class: Optional[str] = None, max_matches: str = "")
查看类的方法信息。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `class_pattern` (str): 类名表达式匹配
  - `method_pattern` (Optional[str]): 可选的方法名表达式
  - `show_detail` (bool): 是否展示每个方法的详细信息
  - `use_regex` (bool): 是否开启正则表达式匹配，默认为通配符匹配
  - `classloader_hash` (Optional[str]): 指定class的ClassLoader的hashcode
  - `classloader_class` (Optional[str]): 指定执行表达式的ClassLoader的class name
  - `max_matches` (str): 匹配类的最大数量，使用字符串形式（如："100"）
- **返回值**：包含方法信息的字典（暂未实现）

### watch_method(pid: str = "", class_pattern: str = "", method_pattern: str = "", watch_params: bool = True, watch_return: bool = True, condition: Optional[str] = None, max_times: str = "10")
监控方法的调用情况。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `class_pattern` (str): 类名表达式匹配
  - `method_pattern` (str): 方法名表达式匹配
  - `watch_params` (bool): 是否监控方法参数
  - `watch_return` (bool): 是否监控方法返回值
  - `condition` (Optional[str]): 条件表达式
  - `max_times` (str): 最大监控次数，使用字符串形式（如："10"）
- **返回值**：包含方法监控信息的字典（暂未实现）

## 日志和系统工具

### get_logger_info(pid: str = "", name: Optional[str] = None)
获取logger信息。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `name` (Optional[str]): logger名称，如果不指定则获取所有logger信息
- **返回值**：包含logger信息的字典（暂未实现）

### set_logger_level(pid: str = "", name: str = "", level: str = "")
设置logger级别。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `name` (str): logger名称
  - `level` (str): 日志级别(trace, debug, info, warn, error)
- **返回值**：设置结果的字典（暂未实现）

### get_dashboard(pid: str = "")
获取系统实时数据面板。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
- **返回值**：包含系统实时数据的字典（暂未实现）

## JDK 原生命令工具

### get_jcmd_output(pid: str = "", subcommand: Optional[str] = None)
执行 jcmd 子命令。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `subcommand` (Optional[str]): jcmd子命令，如果不指定则执行help命令
- **返回值**：包含jcmd执行结果的字典，包含以下字段：
  - `raw_output` (str): 原始输出
  - `timestamp` (float): 时间戳
  - `success` (bool): 是否成功
  - `error` (Optional[str]): 错误信息

### get_jstat_output(pid: str = "", option: Optional[str] = None, interval: str = "", count: str = "")
执行 jstat 监控命令。
- **参数**：
  - `pid` (str): 进程ID，使用字符串形式（如："12345"）
  - `option` (Optional[str]): jstat选项，如gc、class、compiler等
  - `interval` (str): 采样间隔（毫秒），使用字符串形式（如："1000"表示1秒）
  - `count` (str): 采样次数，使用字符串形式（如："10"）
- **返回值**：包含jstat执行结果的字典，包含以下字段：
  - `raw_output` (str): 原始输出
  - `timestamp` (float): 时间戳
  - `success` (bool): 是否成功
  - `error` (Optional[str]): 错误信息