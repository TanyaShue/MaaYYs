# -*- coding: UTF-8 -*-
import logging
from typing import Dict, Optional, List

from PySide6.QtCore import QObject, Signal, Slot, QMutexLocker, QRecursiveMutex

from app.models.config import DeviceConfig
from app.models.config.global_config import RunTimeConfigs
from core.singleton import singleton
from core.task_executor import TaskExecutor, TaskPriority, DeviceState


@singleton
class TaskerManager(QObject):
    """
    集中管理所有设备任务执行器的管理器
    使用单例模式确保整个应用中只有一个实例
    """
    # 定义信号
    device_added = Signal(str)  # 设备添加信号
    device_removed = Signal(str)  # 设备移除信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._executors: Dict[str, TaskExecutor] = {}  # 设备名称到执行器的映射
        self._mutex = QRecursiveMutex()  # 使用递归互斥锁保证线程安全
        self.logger = logging.getLogger("TaskerManager")

    def create_executor(self, device_config: DeviceConfig) -> bool:
        """
        创建并启动设备的任务执行器

        Args:
            device_config: 设备配置信息

        Returns:
            bool: 是否成功创建执行器
        """
        with QMutexLocker(self._mutex):
            # 检查执行器是否已存在
            if device_config.device_name in self._executors:
                self.logger.warning(f"设备 {device_config.device_name} 的任务执行器已存在")
                return True

            try:
                # 创建执行器并设置parent为self，使其随manager销毁而自动清理
                executor = TaskExecutor(device_config, parent=self)
                success = executor.start()

                if success:
                    self._executors[device_config.device_name] = executor
                    self.device_added.emit(device_config.device_name)
                    return True
                return False
            except Exception as e:
                self.logger.error(f"为设备 {device_config.device_name} 创建任务执行器失败: {e}")
                return False

    def submit_task(self, device_name: str, task_data: RunTimeConfigs,
                    priority: TaskPriority = TaskPriority.NORMAL) -> Optional[str]:
        """
        向特定设备的执行器提交任务

        Args:
            device_name: 设备名称
            task_data: 任务数据
            priority: 任务优先级

        Returns:
            Optional[str]: 任务ID，失败时返回None
        """
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return None

            try:
                task_id = executor.submit_task(task_data, priority)
                return task_id
            except Exception as e:
                self.logger.error(f"向设备 {device_name} 提交任务失败: {e}")
                return None

    def stop_executor(self, device_name: str) -> bool:
        """
        停止特定设备的执行器

        Args:
            device_name: 设备名称

        Returns:
            bool: 是否成功停止执行器
        """
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return False

            try:
                executor.stop()
                # 从字典中移除引用，Qt对象会自动清理
                del self._executors[device_name]
                self.device_removed.emit(device_name)
                return True
            except Exception as e:
                self.logger.error(f"停止设备 {device_name} 的执行器失败: {e}")
                return False

    def get_executor_state(self, device_name: str) -> Optional[DeviceState]:
        """
        获取设备执行器的当前状态

        Args:
            device_name: 设备名称

        Returns:
            Optional[DeviceState]: 设备状态对象，未找到时返回None
        """
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return None
            return executor.get_state()

    def _get_executor(self, device_name: str) -> Optional[TaskExecutor]:
        """
        获取特定设备的执行器（内部辅助方法）

        Args:
            device_name: 设备名称

        Returns:
            Optional[TaskExecutor]: 设备执行器对象，未找到时返回None
        """
        executor = self._executors.get(device_name)
        if not executor:
            self.logger.warning(f"设备 {device_name} 的执行器未找到")
        return executor

    def get_active_devices(self) -> List[str]:
        """
        获取所有活跃设备名称的列表

        Returns:
            List[str]: 活跃设备名称列表
        """
        with QMutexLocker(self._mutex):
            return list(self._executors.keys())

    @Slot()
    def stop_all(self):
        """停止所有执行器"""
        self.logger.info("正在停止所有任务执行器")

        # 获取所有设备名称的列表，避免在遍历过程中修改字典
        with QMutexLocker(self._mutex):
            device_names = list(self._executors.keys())

        # 逐个停止执行器
        for device_name in device_names:
            try:
                self.stop_executor(device_name)
            except Exception as e:
                self.logger.error(f"停止设备 {device_name} 的执行器时出错: {e}")

    def is_device_active(self, device_name: str) -> bool:
        """
        检查设备执行器是否处于活跃状态

        Args:
            device_name: 设备名称

        Returns:
            bool: 设备是否活跃
        """
        with QMutexLocker(self._mutex):
            return device_name in self._executors

    def get_device_queue_info(self) -> Dict[str, int]:
        """
        获取所有设备的队列状态信息

        Returns:
            Dict[str, int]: 设备名称到队列长度的映射
        """
        with QMutexLocker(self._mutex):
            queue_info = {}
            for device_name, executor in self._executors.items():
                queue_info[device_name] = executor.get_queue_length()
            return queue_info