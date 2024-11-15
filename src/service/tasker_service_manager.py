# -*- coding: UTF-8 -*-
import json
import logging
import threading
from typing import Dict, Any
from datetime import datetime

from maa.tasker import Tasker
from maa.toolkit import Toolkit

from src.service.tasker import TaskLogger
from src.utils.config_projects import Project, ProjectRunData
from src.service.core.tasker_thread import TaskerThread

from src.service.exceptions import TaskerNotFoundError, TaskerError, TaskerInitializationError, TaskerValidationError
from src.service.tasker import TaskerState, TaskerStatus
from src.utils.singleton import singleton

logger = logging.getLogger(__name__)


@singleton
class TaskerServiceManager:
    def __init__(self):
        self._tasker_threads: Dict[str, TaskerThread] = {}
        self._states: Dict[str, TaskerState] = {}
        self._lock = threading.Lock()
        self._taskers: Dict[str, Tasker] = {}
        self._logger = TaskLogger()

    def create_tasker(self, project_key: str, project: Project) -> bool:
        if not project_key or not project:
            raise TaskerValidationError("Invalid project key or project data")

        with self._lock:
            if project_key in self._tasker_threads:
                raise TaskerError(f"Tasker {project_key} already exists")

            try:
                tasker_thread = TaskerThread(project_key, project)
                controller_handle = tasker_thread._initialize_resources()
                if not controller_handle:
                    raise TaskerInitializationError(f"Failed to initialize resources for {project_key}")

                # Initialize logger with tasker and project_key mapping
                self._logger.init_logger(controller_handle, project_key)
                tasker_thread.start()
                self._tasker_threads[project_key] = tasker_thread
                self._taskers[project_key] = controller_handle
                self._states[project_key] = TaskerState(
                    status=TaskerStatus.RUNNING,
                    created_at=datetime.now(),
                    last_active=datetime.now()
                )

                self._logger.log(controller_handle, f"Tasker created and initialized successfully", "INFO")

                return True

            except Exception as e:
                error_msg = f"Failed to create tasker: {str(e)}"
                if controller_handle:
                    self._logger.log(controller_handle, error_msg, "ERROR")
                raise TaskerInitializationError(error_msg)

    def send_task(self, project_key: str, task_data: Any) -> None:
        """发送任务到指定Tasker"""
        with self._lock:
            tasker = self._get_tasker(project_key)
            state = self._states[project_key]

            state.current_task = task_data
            state.last_active = datetime.now()

            try:
                task = (ProjectRunData.from_json(task_data)
                        if isinstance(task_data, dict) else task_data)
                tasker.send_task(task)
                logger.info(f"Task sent to {project_key}: {task}")
            except Exception as e:
                state.status = TaskerStatus.ERROR
                state.error = str(e)
                raise TaskerError(f"Failed to send task: {e}")

    def terminate_tasker(self, project_key: str) -> None:
        """终止指定的Tasker"""
        with self._lock:
            tasker = self._get_tasker(project_key)
            state = self._states[project_key]

            try:
                state.status = TaskerStatus.STOPPING
                tasker.terminate()
                tasker.join()

                del self._tasker_threads[project_key]
                del self._states[project_key]

                logger.info(f"Tasker {project_key} terminated successfully")
            except Exception as e:
                logger.error(f"Error terminating tasker {project_key}: {e}")
                raise TaskerError(f"Failed to terminate tasker: {e}")

    def get_status(self, project_key: str) -> TaskerState:
        """获取Tasker状态"""
        with self._lock:
            if project_key not in self._states:
                raise TaskerNotFoundError(f"Tasker {project_key} not found")
            return self._states[project_key]

    def _get_tasker(self, project_key: str) -> TaskerThread:
        """获取Tasker实例"""
        tasker = self._tasker_threads.get(project_key)
        if not tasker:
            raise TaskerNotFoundError(f"Tasker {project_key} not found")
        return tasker

    def terminate_all(self) -> None:
        """终止所有Tasker"""
        logger.info("Terminating all taskers...")
        with self._lock:
            for project_key in list(self._tasker_threads.keys()):
                try:
                    self.terminate_tasker(project_key)
                except Exception as e:
                    logger.error(f"Error terminating tasker {project_key}: {e}")

    def get_all_devices(self) -> str:
        with self._lock:
            devices_list = Toolkit.find_adb_devices()
            # Convert each device to a dictionary and convert WindowsPath to string
            devices = [
                {
                    "name": device.name,
                    "adb_path": str(device.adb_path),  # Convert WindowsPath to string
                    "address": device.address,
                    "screencap_methods": device.screencap_methods,
                    "input_methods": device.input_methods,
                    "config": device.config
                }
                for device in devices_list
            ]

            return json.dumps(devices, indent=4)

    def get_all_logs(self) -> str:
        with self._lock:
            logs = self._logger.get_all_logs()
            return json.dumps(logs, indent=4)
