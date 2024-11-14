# -*- coding: UTF-8 -*-
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any



class TaskerStatus(Enum):
    """Tasker状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TaskerState:
    """Tasker状态信息"""
    status: TaskerStatus
    created_at: datetime
    last_active: datetime
    error: Optional[str] = None
    current_task: Optional[Any] = None

