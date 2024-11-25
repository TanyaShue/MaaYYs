# -*- coding: UTF-8 -*-
import os
import json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ServerConfig:
    """服务器配置类"""
    host: str = "localhost"
    port: int = 54345
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 10
    task_timeout: int = 300
    start_script: bool = False
    scheduler_enabled: bool = False  # 是否启用调度器
    scheduler_timezone: str = "Asia/Shanghai"  # 调度器时区
    scheduler_jobs: Dict[str, Any] = None  # 调度任务配置

    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """从环境变量读取配置"""
        return cls(
            host=os.getenv('TASKER_HOST', 'localhost'),
            port=int(os.getenv('TASKER_PORT', 54345)),
            debug=os.getenv('TASKER_DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('TASKER_LOG_LEVEL', 'INFO'),
            max_workers=int(os.getenv('TASKER_MAX_WORKERS', 10)),
            task_timeout=int(os.getenv('TASKER_TASK_TIMEOUT', 300)),
            start_script=os.getenv('TASKER_START_SCRIPT', 'false').lower() == 'true',
            scheduler_enabled=os.getenv('TASKER_SCHEDULER_ENABLED', 'false').lower() == 'true',
            scheduler_timezone=os.getenv('TASKER_SCHEDULER_TIMEZONE', 'Asia/Shanghai'),
            scheduler_jobs={}
        )

    @classmethod
    def from_json(cls, file_path: str) -> 'ServerConfig':
        """从 JSON 文件读取配置"""
        with open(file_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)

        return cls(
            host=config_data.get('server_host', 'localhost'),
            port=config_data.get('server_port', 54345),
            debug=config_data.get('DEBUG', False),
            log_level=config_data.get('log_level', 'INFO'),
            max_workers=config_data.get('max_workers', 10),
            task_timeout=config_data.get('task_timeout', 300),
            start_script=config_data.get('start_script', False),
            scheduler_enabled=config_data.get('scheduler_enabled', False),
            scheduler_timezone=config_data.get('scheduler_timezone', 'Asia/Shanghai'),
            scheduler_jobs=config_data.get('scheduler_jobs', {})
        )