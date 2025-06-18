"""类信息协调器实现"""

import re
import fnmatch
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..base import NativeCommandExecutor
from .jmap import JmapCommand, JmapHistoFormatter, JmapOperation
from .javap import JavapCommand, JavapFormatter

class ClassInfoCoordinator:
    """类信息协调器 - 协调 JmapCommand 和 JavapCommand 获取完整的类信息"""

    def __init__(self, executor: NativeCommandExecutor):
        """初始化协调器

        Args:
            executor: 命令执行器
        """
        self.executor = executor
        # 初始化命令
        self.jmap_histo_cmd = JmapCommand(executor, JmapHistoFormatter())
        self.javap_cmd = JavapCommand(executor, JavapFormatter())

    def get_class_info(self, pid: str, class_pattern: str = "", 
                      show_detail: bool = False, show_field: bool = False,
                      use_regex: bool = False, max_matches: Optional[int] = None,
                      **kwargs) -> Dict[str, Any]:
        """获取类信息

        Args:
            pid: 进程ID
            class_pattern: 类名模式匹配
            show_detail: 是否显示详细信息
            show_field: 是否显示字段信息
            use_regex: 是否使用正则表达式匹配
            max_matches: 最大匹配数量

        Returns:
            Dict[str, Any]: 包含类信息的字典
        """
        try:
            # 第一步：使用 jmap -histo 获取运行时统计信息
            jmap_result = self.jmap_histo_cmd.execute(
                pid=pid, 
                operation=JmapOperation.HISTO,
                live_only=kwargs.get('live_only', False)
            )
            
            if not jmap_result.get('success', False):
                return {
                    "success": False,
                    "error": f"Failed to get histogram data: {jmap_result.get('error', 'Unknown error')}",
                    "classes": [],
                    "total_matches": 0,
                    "limited_by_max": False
                }

            # 第二步：提取和过滤类信息
            histogram = jmap_result.get('histogram', [])
            filtered_classes = self._filter_classes(histogram, class_pattern, use_regex)
            
            # 第三步：应用最大匹配限制
            limited_by_max = False
            if max_matches and len(filtered_classes) > max_matches:
                filtered_classes = filtered_classes[:max_matches]
                limited_by_max = True

            # 第四步：构建基础结果
            classes_info = []
            for class_data in filtered_classes:
                class_info = {
                    "class_name": class_data["class_name"],
                    "runtime_info": {
                        "instances": class_data["instances"],
                        "bytes": class_data["bytes"],
                        "rank": len(classes_info) + 1  # 排名基于内存使用顺序
                    }
                }
                
                # 第五步：如果需要详细信息，获取结构信息
                if show_detail:
                    structure_info = self._get_structure_info(
                        class_data["class_name"], 
                        show_field,
                        **kwargs
                    )
                    if structure_info:
                        class_info["structure_info"] = structure_info

                classes_info.append(class_info)

            return {
                "success": True,
                "classes": classes_info,
                "total_matches": len(classes_info),
                "limited_by_max": limited_by_max,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Coordinator error: {str(e)}",
                "classes": [],
                "total_matches": 0,
                "limited_by_max": False
            }

    def _filter_classes(self, histogram: List[Dict[str, Any]], 
                       pattern: str, use_regex: bool) -> List[Dict[str, Any]]:
        """过滤类列表

        Args:
            histogram: jmap 直方图数据
            pattern: 过滤模式
            use_regex: 是否使用正则表达式

        Returns:
            List[Dict[str, Any]]: 过滤后的类列表
        """
        if not pattern:
            return histogram

        filtered = []
        
        try:
            for class_data in histogram:
                class_name = class_data.get("class_name", "")
                
                if use_regex:
                    # 使用正则表达式匹配
                    if re.search(pattern, class_name, re.IGNORECASE):
                        filtered.append(class_data)
                else:
                    # 使用通配符匹配
                    if fnmatch.fnmatch(class_name.lower(), pattern.lower()):
                        filtered.append(class_data)
                        
        except re.error as e:
            # 正则表达式错误，返回原始列表
            return histogram
            
        return filtered

    def _get_structure_info(self, class_name: str, show_field: bool = False, 
                           **kwargs) -> Optional[Dict[str, Any]]:
        """获取类的结构信息

        Args:
            class_name: 类名
            show_field: 是否显示字段信息
            **kwargs: 其他参数

        Returns:
            Optional[Dict[str, Any]]: 类结构信息，失败时返回 None
        """
        try:
            # 排除数组类型和基础类型
            if self._should_skip_class(class_name):
                return None

            # 构建 javap 参数
            javap_kwargs = {
                "show_detail": kwargs.get('show_javap_detail', False),
                "show_fields": show_field,
                "show_line_numbers": kwargs.get('show_line_numbers', False),
                "show_method_signatures": kwargs.get('show_method_signatures', False),
                "classpath": kwargs.get('classpath')
            }

            # 执行 javap 命令
            javap_result = self.javap_cmd.execute(class_name, **javap_kwargs)
            
            if javap_result.get('success', False):
                return javap_result.get('class_info')
            else:
                # javap 失败，返回 None 但不影响整体结果
                return None
                
        except Exception:
            # 忽略单个类的结构信息获取失败
            return None

    def _should_skip_class(self, class_name: str) -> bool:
        """判断是否应该跳过某个类的结构信息获取

        Args:
            class_name: 类名

        Returns:
            bool: 是否应该跳过
        """
        # 跳过数组类型
        if class_name.startswith('['):
            return True
            
        # 跳过基础类型
        primitive_types = {
            'boolean', 'byte', 'char', 'short', 'int', 'long', 'float', 'double'
        }
        if class_name in primitive_types:
            return True
            
        return False

    def get_class_info_parallel(self, pid: str, class_pattern: str = "", 
                               show_detail: bool = False, show_field: bool = False,
                               use_regex: bool = False, max_matches: Optional[int] = None,
                               max_workers: int = 5, **kwargs) -> Dict[str, Any]:
        """并行获取类信息（优化版本）

        Args:
            pid: 进程ID
            class_pattern: 类名模式匹配
            show_detail: 是否显示详细信息
            show_field: 是否显示字段信息
            use_regex: 是否使用正则表达式匹配
            max_matches: 最大匹配数量
            max_workers: 最大工作线程数

        Returns:
            Dict[str, Any]: 包含类信息的字典
        """
        if not show_detail:
            # 如果不需要详细信息，使用普通版本
            return self.get_class_info(
                pid, class_pattern, show_detail, show_field, 
                use_regex, max_matches, **kwargs
            )

        try:
            # 第一步：获取基础信息
            base_result = self.get_class_info(
                pid, class_pattern, False, False, 
                use_regex, max_matches, **kwargs
            )
            
            if not base_result.get('success', False):
                return base_result

            classes_info = base_result["classes"]
            
            # 第二步：并行获取结构信息
            if classes_info:
                self._parallel_get_structure_info(
                    classes_info, show_field, max_workers, **kwargs
                )

            return {
                "success": True,
                "classes": classes_info,
                "total_matches": base_result["total_matches"],
                "limited_by_max": base_result["limited_by_max"],
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Parallel coordinator error: {str(e)}",
                "classes": [],
                "total_matches": 0,
                "limited_by_max": False
            }

    def _parallel_get_structure_info(self, classes_info: List[Dict[str, Any]], 
                                   show_field: bool, max_workers: int, 
                                   **kwargs) -> None:
        """并行获取结构信息

        Args:
            classes_info: 类信息列表（会被就地修改）
            show_field: 是否显示字段
            max_workers: 最大工作线程数
            **kwargs: 其他参数
        """
        def get_single_structure(class_info: Dict[str, Any]) -> Tuple[int, Optional[Dict[str, Any]]]:
            """获取单个类的结构信息"""
            class_name = class_info["class_name"]
            structure_info = self._get_structure_info(class_name, show_field, **kwargs)
            return classes_info.index(class_info), structure_info

        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(get_single_structure, class_info): i 
                for i, class_info in enumerate(classes_info)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                try:
                    index, structure_info = future.result(timeout=30)  # 30秒超时
                    if structure_info:
                        classes_info[index]["structure_info"] = structure_info
                except Exception:
                    # 忽略单个类的失败
                    continue 