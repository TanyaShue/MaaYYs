# -*- coding: UTF-8 -*-
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ServerConfig:
    """服务器配置类"""
    host: str = "localhost"
    port: int = 54345
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 10
    task_timeout: int = 300

    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """从环境变量读取配置"""
        return cls(
            host=os.getenv('TASKER_HOST', 'localhost'),
            port=int(os.getenv('TASKER_PORT', 54345)),
            debug=os.getenv('TASKER_DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('TASKER_LOG_LEVEL', 'INFO'),
            max_workers=int(os.getenv('TASKER_MAX_WORKERS', 10)),
            task_timeout=int(os.getenv('TASKER_TASK_TIMEOUT', 300))
        )
