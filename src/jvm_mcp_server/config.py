"""配置管理模块"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CommandConfig:
    """命令配置类"""
    timeout: int  # 超时时间(秒)
    max_retries: int = 3  # 最大重试次数
    retry_interval: int = 1  # 重试间隔(秒)
    description: str = ""  # 命令描述

@dataclass
class ArthasConfig:
    """Arthas配置类"""
    # 连接池配置
    pool_max_size: int = 5
    pool_min_size: int = 1
    pool_connection_timeout: int = 30  # 增加连接超时时间到30秒
    pool_idle_timeout: int = 300
    pool_max_lifetime: int = 3600
    pool_health_check_interval: int = 60
    
    # 命令超时配置
    command_timeouts: Dict[str, CommandConfig] = field(default_factory=lambda: {
        # 基础命令
        "version": CommandConfig(timeout=10, max_retries=3, retry_interval=1, description="获取版本信息"),
        "help": CommandConfig(timeout=10, max_retries=3, retry_interval=1, description="获取帮助信息"),
        
        # 线程相关命令
        "thread": CommandConfig(timeout=20, max_retries=3, retry_interval=2, description="查看线程信息"),
        "stack": CommandConfig(timeout=25, max_retries=3, retry_interval=2, description="查看方法调用栈"),
        "thread_pool": CommandConfig(timeout=20, max_retries=3, retry_interval=2, description="查看线程池信息"),
        
        # 类相关命令
        "sc": CommandConfig(timeout=25, max_retries=3, retry_interval=2, description="查看类信息"),
        "sm": CommandConfig(timeout=25, max_retries=3, retry_interval=2, description="查看方法信息"),
        "jad": CommandConfig(timeout=30, max_retries=3, retry_interval=2, description="反编译类"),
        
        # 监控相关命令
        "monitor": CommandConfig(timeout=40, max_retries=3, retry_interval=2, description="方法监控"),
        "watch": CommandConfig(timeout=40, max_retries=3, retry_interval=2, description="方法执行数据观测"),
        "trace": CommandConfig(timeout=40, max_retries=3, retry_interval=2, description="方法调用路径追踪"),
        
        # 系统相关命令
        "dashboard": CommandConfig(timeout=20, max_retries=3, retry_interval=2, description="系统面板"),
        "jvm": CommandConfig(timeout=20, max_retries=3, retry_interval=2, description="JVM信息"),
        "memory": CommandConfig(timeout=20, max_retries=3, retry_interval=2, description="内存信息"),
        
        # 默认配置
        "default": CommandConfig(timeout=25, max_retries=3, retry_interval=2, description="默认配置")
    })
    
    @classmethod
    def load(cls, config_file: str = None) -> 'ArthasConfig':
        """
        从配置文件加载配置
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认配置
            
        Returns:
            ArthasConfig: 配置对象
        """
        config = cls()
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                
                # 更新连接池配置
                for key in ['pool_max_size', 'pool_min_size', 'pool_connection_timeout',
                          'pool_idle_timeout', 'pool_max_lifetime', 'pool_health_check_interval']:
                    if key in data:
                        setattr(config, key, data[key])
                
                # 更新命令超时配置
                if 'command_timeouts' in data:
                    for cmd, cfg in data['command_timeouts'].items():
                        config.command_timeouts[cmd] = CommandConfig(**cfg)
                        
                logger.info(f"已从 {config_file} 加载配置")
                
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                logger.info("使用默认配置")
        
        return config
    
    def save(self, config_file: str):
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            # 转换为字典
            config_dict = {
                'pool_max_size': self.pool_max_size,
                'pool_min_size': self.pool_min_size,
                'pool_connection_timeout': self.pool_connection_timeout,
                'pool_idle_timeout': self.pool_idle_timeout,
                'pool_max_lifetime': self.pool_max_lifetime,
                'pool_health_check_interval': self.pool_health_check_interval,
                'command_timeouts': {
                    cmd: {
                        'timeout': cfg.timeout,
                        'max_retries': cfg.max_retries,
                        'retry_interval': cfg.retry_interval,
                        'description': cfg.description
                    }
                    for cmd, cfg in self.command_timeouts.items()
                }
            }
            
            # 保存到文件
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
            logger.info(f"配置已保存到 {config_file}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def get_command_config(self, command: str) -> CommandConfig:
        """
        获取命令配置
        
        Args:
            command: 命令名称
            
        Returns:
            CommandConfig: 命令配置
        """
        # 提取命令名称（去掉参数）
        cmd_name = command.split()[0].lower()
        return self.command_timeouts.get(cmd_name, self.command_timeouts['default'])
    
    def update_command_config(self, command: str, config: CommandConfig):
        """
        更新命令配置
        
        Args:
            command: 命令名称
            config: 新的配置
        """
        self.command_timeouts[command.lower()] = config
        logger.info(f"已更新命令 {command} 的配置") 