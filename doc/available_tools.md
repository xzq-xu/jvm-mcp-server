# 可用工具

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


### get_class_info
获取类信息，包括成员变量
- 参数：
  - `pid`: 进程ID
  - `class_pattern`: 类名表达式匹配
  - `show_detail`: 是否显示详细信息
  - `show_field`: 是否显示成员变量信息(需要show_detail=True)
  - `use_regex`: 是否使用正则表达式匹配
  - `depth`: 指定输出静态变量时属性的遍历深度
  - `classloader_hash`: 指定class的ClassLoader的hashcode
  - `classloader_class`: 指定执行表达式的ClassLoader的class name
  - `max_matches`: 具有详细信息的匹配类的最大数量
- 返回值：类信息


### get_jvm_status(pid: Optional[int] = None)
获取JVM整体状态报告。
- 参数：
  - pid: 可选的进程ID，如果不指定则自动选择第一个非arthas的Java进程
- 返回值：包含完整JVM状态信息的字典