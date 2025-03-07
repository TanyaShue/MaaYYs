# -*- coding: UTF-8 -*-
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from PySide6.QtCore import QObject, Signal, Slot, QMutexLocker, QRecursiveMutex

from app.models.config import DeviceConfig
from core.singleton import singleton
from core.task_executor import TaskExecutor


class TaskStatus(Enum):
    """任务执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    HIGH = 0
    NORMAL = 1
    LOW = 2


class Task:
    """统一任务表示"""

    def __init__(self, task_data: Any, priority: TaskPriority = TaskPriority.NORMAL):
        self.id = f"task_{id(self)}"  # 唯一任务ID
        self.data = task_data
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.cancelable = True
        self.runner = None  # 引用执行此任务的TaskRunner


class DeviceStatus(Enum):
    """设备状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"


class DeviceState(QObject):
    """设备状态类"""
    status_changed = Signal(str)  # 状态变化信号
    error_occurred = Signal(str)  # 错误信号

    def __init__(self):
        super().__init__()
        self.status = DeviceStatus.IDLE
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.current_task = None
        self.error = None
        self.task_history = []
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_runtime": 0
        }

    def update_status(self, status: DeviceStatus, error=None):
        """更新设备状态"""
        self.status = status
        self.last_active = datetime.now()
        self.status_changed.emit(status.value)
        if error:
            self.error = error
            self.error_occurred.emit(error)


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
        self._executors: Dict[str, TaskExecutor] = {}
        # 使用递归互斥锁代替普通互斥锁
        self._mutex = QRecursiveMutex()
        self.logger = logging.getLogger("TaskerManager")

    def create_executor(self,device_config: DeviceConfig) -> bool:
        """创建并启动设备的任务执行器"""
        with QMutexLocker(self._mutex):
            if device_config.device_name in self._executors:
                self.logger.warning(f"设备 {device_config.device_name} 的任务执行器已存在")
                return False

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

    def submit_task(self, device_name: str, task_data: Any,
                    priority: TaskPriority = TaskPriority.NORMAL) -> Optional[str]:
        """向特定设备的执行器提交任务"""
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

    @Slot(str, str)
    def cancel_task(self, device_name: str, task_id: str) -> bool:
        """取消特定设备上的任务"""
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return False
            return executor.cancel_task(task_id)

    def stop_executor(self, device_name: str) -> bool:
        """停止特定设备的执行器"""
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return False

            try:
                executor.stop()
                # 注意: 不要删除executor，因为它是QObject的子对象，会自动清理
                # 只需要从字典中移除引用
                del self._executors[device_name]
                self.device_removed.emit(device_name)
                return True
            except Exception as e:
                self.logger.error(f"停止设备 {device_name} 的执行器失败: {e}")
                return False

    def get_executor_state(self, device_name: str) -> Optional[DeviceState]:
        """获取设备执行器的当前状态"""
        with QMutexLocker(self._mutex):
            executor = self._get_executor(device_name)
            if not executor:
                return None
            return executor.get_state()

    def _get_executor(self, device_name: str) -> Optional[TaskExecutor]:
        """获取特定设备的执行器"""
        executor = self._executors.get(device_name)
        if not executor:
            self.logger.warning(f"设备 {device_name} 的执行器未找到")
        return executor

    def get_active_devices(self) -> List[str]:
        """获取所有活跃设备名称的列表"""
        with QMutexLocker(self._mutex):
            return list(self._executors.keys())

    @Slot()
    def stop_all(self):
        """停止所有执行器"""
        self.logger.info("正在停止所有任务执行器")
        # 首先获取所有设备名称的列表，避免在遍历过程中修改字典
        with QMutexLocker(self._mutex):
            device_names = list(self._executors.keys())

        # 然后逐个停止执行器
        for device_name in device_names:
            try:
                self.stop_executor(device_name)
            except Exception as e:
                self.logger.error(f"停止设备 {device_name} 的执行器时出错: {e}")

    def is_device_active(self, device_name: str) -> bool:
        """检查设备执行器是否处于活跃状态"""
        with QMutexLocker(self._mutex):
            return device_name in self._executors

    def get_device_queue_info(self) -> Dict[str, int]:
        """获取所有设备的队列状态信息"""
        with QMutexLocker(self._mutex):
            queue_info = {}
            for device_name, executor in self._executors.items():
                queue_info[device_name] = executor.get_queue_length()
            return queue_info
