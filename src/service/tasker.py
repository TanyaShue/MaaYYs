# -*- coding: UTF-8 -*-
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Any, Union

from utils.log_entry import LogEntry
from utils.singleton import singleton


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


from collections import defaultdict
from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional, Any
import logging




@singleton
class TaskLogger:
    def __init__(self):
        self.logs = defaultdict(list)  # project_key -> logs
        self._handle_to_project = {}  # tasker -> project_key mapping
        self.lock = Lock()
        self._max_logs_per_project = 1000

    def init_logger(self, _handle: Any, project_key: str) -> None:
        """Initialize logger for a tasker and establish mapping to project_key"""
        # print(f"Initializing logger for tasker {_handle}, project key: {project_key}")
        self._handle_to_project[_handle] = project_key
        if project_key not in self.logs:
            self.logs[project_key] = []
        # print(self._handle_to_project)

    def log(self, _handle: Any, message: str, level: str = "INFO", task_id: Optional[str] = None) -> None:
        """Add a log entry using tasker object"""
        project_key = self._handle_to_project.get(_handle)
        # print(self.tasker_to_project)
        # print(f"Logging for tasker {_handle}, project key: {project_key}")
        if not project_key:
            logging.error(f"No project key found for tasker {_handle}")
            return

        log_entry = LogEntry(message, level, task_id)
        # print(f"Log entry: {log_entry.to_dict()}")
        self.logs[project_key].append(log_entry)

        # Implement rotation if needed
        if len(self.logs[project_key]) > self._max_logs_per_project:
            self.logs[project_key] = self.logs[project_key][-self._max_logs_per_project:]

    def get_logs(self, project_key: str, limit: int = None, level: str = None) -> List[dict]:
        """Get logs for a specific project with optional filtering"""

        project_logs = self.logs.get(project_key, [])
        filtered_logs = [
            log.to_dict() for log in project_logs
            if level is None or log.level == level
        ]
        if limit:
            filtered_logs = filtered_logs[-limit:]
        return filtered_logs
    def get_logs_from_tasker(self, _handle: Any) -> List[dict]:
        project_key = self._handle_to_project.get(_handle)
        return self.get_logs(project_key)


    def get_all_logs(self, limit: int = None, level: str = None) -> Dict[str, List[dict]]:
        """
        获取所有项目的日志

        Args:
            limit: 每个项目返回的日志条数限制
            level: 日志级别过滤

        Returns:
            Dict[str, List[dict]]: 以project_key为key的所有项目日志字典
        """
        # with self.lock:
        all_logs = {}
        for project_key in self.logs.keys():
            all_logs[project_key] = self.get_logs(project_key, limit, level)
        return all_logs

    def get_recent_logs(self, minutes: int = 60) -> Dict[str, List[dict]]:
        """
        获取最近一段时间内的所有日志

        Args:
            minutes: 最近多少分钟内的日志

        Returns:
            Dict[str, List[dict]]: 以project_key为key的最近日志字典
        """

        now = datetime.now()
        time_threshold = now - timedelta(minutes=minutes)

        recent_logs = {}
        for project_key, logs in self.logs.items():
            filtered_logs = [
                log.to_dict() for log in logs
                if datetime.strptime(log.timestamp, "%Y-%m-%d %H:%M:%S") > time_threshold
            ]
            if filtered_logs:
                recent_logs[project_key] = filtered_logs
        return recent_logs

    def get_error_logs(self, limit: int = None) -> Dict[str, List[dict]]:
        """
        获取所有错误日志

        Args:
            limit: 每个项目返回的错误日志条数限制

        Returns:
            Dict[str, List[dict]]: 以project_key为key的错误日志字典
        """
        return self.get_all_logs(limit=limit, level="ERROR")

    def get_project_keys(self) -> List[str]:
        """获取所有已注册的project_key列表"""
        return list(self.logs.keys())

    def get_active_taskers(self) -> Dict[Any, str]:
        """获取所有活动中的tasker和对应的project_key映射"""
        return dict(self._handle_to_project)

    def get_log_count(self, project_key: Optional[str] = None) -> Union[int, Dict[str, int]]:
        """
        获取日志数量统计

        Args:
            project_key: 指定项目,如果为None则返回所有项目的统计

        Returns:
            Union[int, Dict[str, int]]: 指定项目的日志数量或所有项目的日志数量字典
        """
        if project_key:
            return len(self.logs.get(project_key, []))
        return {key: len(logs) for key, logs in self.logs.items()}

    def clear_logs(self, project_key: Optional[str] = None) -> None:
        """Clear logs for a specific project or all logs"""
        if project_key:
            self.logs[project_key].clear()
        else:
            self.logs.clear()

    def clear_old_logs(self, days: int = 7) -> None:
        """
        清理指定天数之前的旧日志

        Args:
            days: 保留最近多少天的日志
        """
        time_threshold = datetime.now() - timedelta(days=days)
        for project_key in self.logs:
            self.logs[project_key] = [
                log for log in self.logs[project_key]
                if datetime.strptime(log.timestamp, "%Y-%m-%d %H:%M:%S") > time_threshold
            ]

    def remove_tasker(self, _handle: Any) -> None:
        """Remove tasker mapping when tasker is terminated"""
        if _handle in self._handle_to_project:
            del self._handle_to_project[_handle]

    def set_max_logs(self, max_logs: int) -> None:
        """设置每个项目的最大日志数量"""
        self._max_logs_per_project = max_logs
        # 对现有日志进行裁剪
        for project_key in self.logs:
            if len(self.logs[project_key]) > max_logs:
                self.logs[project_key] = self.logs[project_key][-max_logs:]