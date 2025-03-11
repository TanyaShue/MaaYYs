# -*- coding: UTF-8 -*-
import logging
from typing import Dict, Optional, List, Union

from PySide6.QtCore import QObject, Signal, Slot, QMutexLocker, QRecursiveMutex

from app.models.config.device_config import DeviceConfig
from app.models.config.global_config import RunTimeConfigs, global_config
from core.task_executor import TaskExecutor, TaskPriority, DeviceState


class TaskerManager(QObject):
    """
    集中管理所有设备任务执行器的管理器，使用单例模式确保整个应用中只有一个实例。
    """
    device_added = Signal(str)   # 设备添加信号
    device_removed = Signal(str) # 设备移除信号

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._executors: Dict[str, TaskExecutor] = {}
        self._mutex = QRecursiveMutex()
        self.logger = logging.getLogger("TaskerManager")

    def create_executor(self, device_config: DeviceConfig) -> bool:
        """
        创建并启动设备的任务执行器。

        Args:
            device_config: 设备配置信息

        Returns:
            True：成功创建或已存在；False：创建失败
        """
        with QMutexLocker(self._mutex):
            if device_config.device_name in self._executors:
                self.logger.warning(f"设备 {device_config.device_name} 的任务执行器已存在")
                return True

            try:
                executor = TaskExecutor(device_config, parent=self)
                if executor.start():
                    self._executors[device_config.device_name] = executor
                    self.device_added.emit(device_config.device_name)
                    return True
                return False
            except Exception as e:
                self.logger.error(f"为设备 {device_config.device_name} 创建任务执行器失败: {e}")
                return False

    def submit_task(self, device_name: str,
                    task_data: Union[RunTimeConfigs, List[RunTimeConfigs]],
                    priority: TaskPriority = TaskPriority.NORMAL
                    ) -> Optional[Union[str, List[str]]]:
        """
        向特定设备的执行器提交任务。

        Args:
            device_name: 设备名称
            task_data: 单个任务或任务列表
            priority: 任务优先级

        Returns:
            单个任务时返回任务ID；列表时返回任务ID列表；失败返回 None
        """
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return None

            try:
                return executor.submit_task(task_data, priority)
            except Exception as e:
                self.logger.error(f"向设备 {device_name} 提交任务失败: {e}")
                return None

    def stop_executor(self, device_name: str) -> bool:
        """
        停止特定设备的执行器。

        Args:
            device_name: 设备名称

        Returns:
            True：成功停止；False：停止失败
        """
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return False

            try:
                executor.stop()
                del self._executors[device_name]
                self.device_removed.emit(device_name)
                return True
            except Exception as e:
                self.logger.error(f"停止设备 {device_name} 的执行器失败: {e}")
                return False

    def get_executor_state(self, device_name: str) -> Optional[DeviceState]:
        """
        获取设备执行器的当前状态。

        Args:
            device_name: 设备名称

        Returns:
            设备状态对象，未找到返回 None
        """
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            return executor.get_state() if executor else None

    def _get_executor(self, device_name: str) -> Optional[TaskExecutor]:
        """
        内部辅助方法，获取特定设备的执行器。

        Args:
            device_name: 设备名称

        Returns:
            设备执行器对象，未找到返回 None
        """
        executor = self._executors.get(device_name)
        if not executor:
            self.logger.warning(f"设备 {device_name} 的执行器未找到")
        return executor

    def get_active_devices(self) -> List[str]:
        """
        获取所有活跃设备名称列表。

        Returns:
            活跃设备名称列表
        """
        with QMutexLocker(self._mutex):
            return list(self._executors.keys())

    @Slot()
    def stop_all(self) -> None:
        """
        停止所有执行器。
        """
        self.logger.info("正在停止所有任务执行器")
        with QMutexLocker(self._mutex):
            device_names = list(self._executors.keys())
        for device_name in device_names:
            try:
                self.stop_executor(device_name)
            except Exception as e:
                self.logger.error(f"停止设备 {device_name} 的执行器时出错: {e}")

    def is_device_active(self, device_name: str) -> bool:
        """
        检查设备执行器是否处于活跃状态。

        Args:
            device_name: 设备名称

        Returns:
            True：活跃；False：不活跃
        """
        with QMutexLocker(self._mutex):
            return device_name in self._executors

    def get_device_queue_info(self) -> Dict[str, int]:
        """
        获取所有设备的队列状态信息。

        Returns:
            设备名称到队列长度的映射字典
        """
        with QMutexLocker(self._mutex):
            return {name: executor.get_queue_length() for name, executor in self._executors.items()}

    def run_device_all_resource_task(self, device_config: DeviceConfig) -> None:
        """
        一键启动：提交所有已启用资源的任务。
        """
        runtime_configs = [
            global_config.get_runtime_configs_for_resource(resource.resource_name, device_config.device_name)
            for resource in device_config.resources
            if resource.enable and global_config.get_runtime_configs_for_resource(resource.resource_name, device_config.device_name)
        ]
        if runtime_configs:
            self.create_executor(device_config)
            self.submit_task(device_config.device_name, runtime_configs)

    def run_resource_task(self, device_config: DeviceConfig, resource_name: str) -> None:
        """
        提交指定资源的任务。
        """
        runtime_config = global_config.get_runtime_configs_for_resource(resource_name, device_config.device_name)
        self.create_executor(device_config)
        self.submit_task(device_config.device_name, runtime_config)


task_manager = TaskerManager()
