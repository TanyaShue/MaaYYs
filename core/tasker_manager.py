# -*- coding: UTF-8 -*-
import json
import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from maa.tasker import Tasker

from core.singleton import singleton


class TaskerStatus:
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"

class TaskerThread:
    """Tasker线程类，负责执行任务"""

    def __init__(self, device_name: str, device_config: Any, resource_path: str):
        self.status: str = TaskerStatus.IDLE
        self.device_name = device_name
        self.device_config = device_config
        self.resource_path = resource_path
        self._tasker: Optional[Tasker] = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._running = False

    def start(self):
        """启动Tasker线程"""
        self._running = True
        self._thread.start()

    def _run(self):
        """线程执行函数"""
        while self._running:
            # 简单的主循环，在实际应用中可能需要更复杂的逻辑
            time.sleep(0.1)

    def _initialize_resources(self) -> Optional[Tasker]:
        """初始化Tasker资源"""
        try:
            # 这里根据实际需求创建和初始化Tasker
            # 简化示例，实际实现可能更复杂
            self._tasker = Tasker()

            return self._tasker
        except Exception as e:
            print(f"初始化失败: {str(e)}")
            return None

    def send_task(self, task_data: Any):
        """发送任务到Tasker"""
        self._tasker.send_task(task_data)

    def terminate(self):
        """终止Tasker线程"""
        if not self._tasker:
            return
        self._running = False
        self._tasker.stop()

    def join(self, timeout=None):
        """等待线程结束"""
        if self._thread.is_alive():
            self._thread.join(timeout)


@singleton
class TaskerManager:
    def __init__(self):
        self._tasker_threads: Dict[str, TaskerThread] = {}
        self._states: Dict[str, TaskerStatus] = {}
        self._lock = threading.Lock()
        self._taskers: Dict[str, Tasker] = {}

    def create_tasker(self, device_name: str, device_config: Any, resource_path: str) -> bool:
        """
        创建并启动一个新的Tasker

        Args:
            device_name: 设备名称
            device_config: 设备配置
            resource_path: 资源路径

        Returns:
            bool: 创建是否成功
        """
        with self._lock:
            if device_name in self._tasker_threads:
                print(f"Tasker for device {device_name} already exists")

            try:
                tasker_thread = TaskerThread(device_name, device_config, resource_path)
                controller_handle = tasker_thread._initialize_resources()

                # 初始化logger
                tasker_thread.start()
                self._tasker_threads[device_name] = tasker_thread
                self._taskers[device_name] = controller_handle
                self._states[device_name] = TaskerState(
                    status=TaskerStatus.RUNNING,
                    created_at=datetime.now(),
                    last_active=datetime.now()
                )

                return True

            except Exception as e:
                print(f"初始化失败: {str(e)}")

    def send_task(self, device_name: str, task_data: Any) -> None:
        """
        发送任务到指定设备的Tasker

        Args:
            device_name: 设备名称
            task_data: 任务数据
        """
        with self._lock:
            tasker_thread = self._get_tasker_thread(device_name)
            state = self._states[device_name]

            state.current_task = task_data
            state.last_active = datetime.now()

            try:
                # 这里假设有一个ProjectRunData类，根据实际情况调整
                task = (task_data if not isinstance(task_data, dict)
                        else task_data)  # 简化处理
                tasker_thread.send_task(task)
            except Exception as e:
                state.status = TaskerStatus.ERROR
                state.error = str(e)
                print(f"Failed to send task: {e}")

    def terminate_tasker(self, device_name: str) -> None:
        """
        终止指定设备的Tasker

        Args:
            device_name: 设备名称
        """
        with self._lock:
            tasker_thread = self._get_tasker_thread(device_name)
            state = self._states[device_name]

            try:
                state.status = TaskerStatus.STOPPING
                tasker_thread.terminate()
                tasker_thread.join()

                del self._tasker_threads[device_name]
                del self._taskers[device_name]
                del self._states[device_name]

            except Exception as e:
                print(f"Failed to terminate tasker: {e}")

    def get_status(self, device_name: str) -> TaskerStatus:
        """
        获取指定设备Tasker的状态

        Args:
            device_name: 设备名称

        Returns:
            TaskerState: Tasker状态
        """
        with self._lock:
            if device_name not in self._states:
                print(f"Tasker for device {device_name} not found")
            return self._states[device_name]

    def _get_tasker_thread(self, device_name: str) -> TaskerThread:
        """
        获取指定设备的TaskerThread实例

        Args:
            device_name: 设备名称

        Returns:
            TaskerThread: Tasker线程实例
        """
        tasker_thread = self._tasker_threads.get(device_name)
        if not tasker_thread:
            print(f"Tasker for device {device_name} not found")
        return tasker_thread

    def terminate_all(self) -> None:
        """终止所有Tasker"""
        with self._lock:
            for device_name in list(self._tasker_threads.keys()):
                try:
                    self.terminate_tasker(device_name)
                except Exception as e:
                    print(f"Error terminating tasker for {device_name}: {e}")


    def get_active_devices(self) -> List[str]:
        """
        获取所有活跃的设备名称

        Returns:
            List[str]: 活跃设备名称列表
        """
        with self._lock:
            return list(self._tasker_threads.keys())

    def is_device_running(self, device_name: str) -> bool:
        """
        检查设备是否正在运行

        Args:
            device_name: 设备名称

        Returns:
            bool: 是否运行中
        """
        with self._lock:
            return device_name in self._tasker_threads