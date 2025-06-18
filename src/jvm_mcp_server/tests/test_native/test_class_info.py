"""ClassInfoCoordinator测试"""

from datetime import datetime
from unittest.mock import Mock, patch
from jvm_mcp_server.native.base import CommandResult, NativeCommandExecutor
from jvm_mcp_server.native.tools.class_info import ClassInfoCoordinator
import pytest

class TestClassInfoCoordinator:
    """ClassInfoCoordinator测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        self.executor = Mock(spec=NativeCommandExecutor)
        self.coordinator = ClassInfoCoordinator(self.executor)

    def test_get_class_info_basic(self):
        """测试基础类信息获取"""
        # 模拟 jmap 结果
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000},
                {"class_name": "java.util.HashMap", "instances": 500, "bytes": 25000},
                {"class_name": "[B", "instances": 200, "bytes": 10000}
            ]
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result):
            result = self.coordinator.get_class_info(pid="1234")
            
            assert result["success"] is True
            assert len(result["classes"]) == 3
            assert result["total_matches"] == 3
            assert result["limited_by_max"] is False
            
            # 检查第一个类的信息
            first_class = result["classes"][0]
            assert first_class["class_name"] == "java.lang.String"
            assert first_class["runtime_info"]["instances"] == 1000
            assert first_class["runtime_info"]["bytes"] == 50000
            assert first_class["runtime_info"]["rank"] == 1

    def test_get_class_info_with_pattern_wildcard(self):
        """测试通配符模式匹配"""
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000},
                {"class_name": "java.util.HashMap", "instances": 500, "bytes": 25000},
                {"class_name": "com.example.MyClass", "instances": 100, "bytes": 5000}
            ]
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result):
            result = self.coordinator.get_class_info(
                pid="1234", 
                class_pattern="java.*", 
                use_regex=False
            )
            
            assert result["success"] is True
            assert len(result["classes"]) == 2  # 应该匹配 java.lang.String 和 java.util.HashMap
            
            class_names = [cls["class_name"] for cls in result["classes"]]
            assert "java.lang.String" in class_names
            assert "java.util.HashMap" in class_names
            assert "com.example.MyClass" not in class_names

    def test_get_class_info_with_pattern_regex(self):
        """测试正则表达式模式匹配"""
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000},
                {"class_name": "java.util.HashMap", "instances": 500, "bytes": 25000},
                {"class_name": "com.example.MyClass", "instances": 100, "bytes": 5000}
            ]
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result):
            result = self.coordinator.get_class_info(
                pid="1234", 
                class_pattern=r"java\.lang\..*", 
                use_regex=True
            )
            
            assert result["success"] is True
            assert len(result["classes"]) == 1  # 应该只匹配 java.lang.String
            assert result["classes"][0]["class_name"] == "java.lang.String"

    def test_get_class_info_with_max_matches(self):
        """测试最大匹配数量限制"""
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000},
                {"class_name": "java.util.HashMap", "instances": 500, "bytes": 25000},
                {"class_name": "java.util.ArrayList", "instances": 300, "bytes": 15000},
                {"class_name": "java.lang.Object", "instances": 200, "bytes": 10000}
            ]
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result):
            result = self.coordinator.get_class_info(
                pid="1234", 
                max_matches=2
            )
            
            assert result["success"] is True
            assert len(result["classes"]) == 2
            assert result["total_matches"] == 2
            assert result["limited_by_max"] is True

    def test_get_class_info_with_detail(self):
        """测试获取详细信息"""
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000}
            ]
        }
        
        javap_result = {
            "success": True,
            "class_info": {
                "class_name": "java.lang.String",
                "modifiers": ["public", "final"],
                "superclass": "java.lang.Object",
                "interfaces": ["java.io.Serializable"],
                "fields": [{"name": "value", "type": "char[]", "visibility": "private"}],
                "methods": [{"name": "length", "return_type": "int", "visibility": "public"}]
            }
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result), \
             patch.object(self.coordinator.javap_cmd, 'execute', return_value=javap_result):
            
            result = self.coordinator.get_class_info(
                pid="1234", 
                show_detail=True
            )
            
            assert result["success"] is True
            assert len(result["classes"]) == 1
            
            class_info = result["classes"][0]
            assert "runtime_info" in class_info
            assert "structure_info" in class_info
            assert class_info["structure_info"]["class_name"] == "java.lang.String"

    def test_get_class_info_skip_array_classes(self):
        """测试跳过数组类型"""
        coordinator = ClassInfoCoordinator(self.executor)
        
        # 测试数组类型
        assert coordinator._should_skip_class("[B") is True
        assert coordinator._should_skip_class("[Ljava.lang.String;") is True
        assert coordinator._should_skip_class("[[I") is True
        
        # 测试基础类型
        assert coordinator._should_skip_class("int") is True
        assert coordinator._should_skip_class("boolean") is True
        
        # 测试正常类型
        assert coordinator._should_skip_class("java.lang.String") is False
        assert coordinator._should_skip_class("com.example.MyClass") is False

    def test_get_class_info_jmap_failure(self):
        """测试 jmap 执行失败"""
        jmap_result = {
            "success": False,
            "error": "Process not found"
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result):
            result = self.coordinator.get_class_info(pid="invalid")
            
            assert result["success"] is False
            assert "Failed to get histogram data" in result["error"]
            assert result["classes"] == []
            assert result["total_matches"] == 0

    def test_get_class_info_javap_partial_failure(self):
        """测试 javap 部分失败"""
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000},
                {"class_name": "com.invalid.Class", "instances": 500, "bytes": 25000}
            ]
        }
        
        def mock_javap_execute(class_name, **kwargs):
            if class_name == "java.lang.String":
                return {
                    "success": True,
                    "class_info": {
                        "class_name": "java.lang.String",
                        "modifiers": ["public", "final"]
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Class not found"
                }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result), \
             patch.object(self.coordinator.javap_cmd, 'execute', side_effect=mock_javap_execute):
            
            result = self.coordinator.get_class_info(
                pid="1234", 
                show_detail=True
            )
            
            assert result["success"] is True
            assert len(result["classes"]) == 2
            
            # 第一个类应该有结构信息
            first_class = result["classes"][0]
            assert "structure_info" in first_class
            
            # 第二个类应该没有结构信息（javap 失败）
            second_class = result["classes"][1]
            assert "structure_info" not in second_class

    def test_filter_classes_empty_pattern(self):
        """测试空模式匹配"""
        histogram = [
            {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000},
            {"class_name": "java.util.HashMap", "instances": 500, "bytes": 25000}
        ]
        
        result = self.coordinator._filter_classes(histogram, "", False)
        assert len(result) == 2
        assert result == histogram

    def test_filter_classes_invalid_regex(self):
        """测试无效正则表达式"""
        histogram = [
            {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000}
        ]
        
        # 无效的正则表达式应该返回原始列表
        result = self.coordinator._filter_classes(histogram, "[", True)
        assert result == histogram

    def test_get_class_info_parallel(self):
        """测试并行获取类信息"""
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000},
                {"class_name": "java.util.HashMap", "instances": 500, "bytes": 25000}
            ]
        }
        
        javap_result = {
            "success": True,
            "class_info": {
                "class_name": "java.lang.String",
                "modifiers": ["public", "final"]
            }
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result), \
             patch.object(self.coordinator.javap_cmd, 'execute', return_value=javap_result):
            
            result = self.coordinator.get_class_info_parallel(
                pid="1234", 
                show_detail=True,
                max_workers=2
            )
            
            assert result["success"] is True
            assert len(result["classes"]) == 2

    def test_get_class_info_parallel_no_detail(self):
        """测试并行模式但不需要详细信息"""
        jmap_result = {
            "success": True,
            "histogram": [
                {"class_name": "java.lang.String", "instances": 1000, "bytes": 50000}
            ]
        }
        
        with patch.object(self.coordinator.jmap_histo_cmd, 'execute', return_value=jmap_result):
            result = self.coordinator.get_class_info_parallel(
                pid="1234", 
                show_detail=False
            )
            
            assert result["success"] is True
            assert len(result["classes"]) == 1

if __name__ == '__main__':
    pytest.main() 