# -*- coding: UTF-8 -*-
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable, QMutexLocker, QRecursiveMutex, Qt
from maa.controller import AdbController
from maa.resource import Resource
from maa.tasker import Tasker

from app.models.config import DeviceConfig
from app.models.config.global_config import RunTimeConfigs


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

    def __init__(self, task_data: RunTimeConfigs, priority: TaskPriority = TaskPriority.NORMAL):
        self.id = f"task_{id(self)}"  # 唯一任务ID
        self.data:RunTimeConfigs = task_data
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

class TaskExecutor(QObject):
    """任务执行控制器，管理单个设备的任务执行"""
    # 定义信号
    task_started = Signal(str)  # 任务开始信号
    task_completed = Signal(str, object)  # 任务完成信号
    task_failed = Signal(str, str)  # 任务失败信号
    task_canceled = Signal(str)  # 任务取消信号
    progress_updated = Signal(str, int)  # 任务进度更新信号
    executor_started = Signal()  # 执行器启动信号
    executor_stopped = Signal()  # 执行器停止信号
    task_queued = Signal(str)  # 任务入队信号
    process_next_task_signal = Signal()  # 用于安全触发下一个任务处理的信号

    def __init__(self, device_config: DeviceConfig, parent=None):
        super().__init__(parent)
        self.device_name = device_config.device_name
        self.device_config = device_config
        self.resource_path:Optional[str] = None
        adb_config=device_config.adb_config
        self._controller=AdbController(adb_config.adb_path,adb_config.address,adb_config.screencap_methods,
                                       adb_config.input_methods,adb_config.config)
        # 设备状态管理
        self.state = DeviceState()
        self._tasker:Optional[Tasker] = Tasker()

        # 使用全局线程池
        self.thread_pool = QThreadPool.globalInstance()

        # 激活状态
        self._active = False
        # 使用递归互斥锁代替普通互斥锁
        self._mutex = QRecursiveMutex()

        # 任务管理 - 添加任务队列
        self._pending_tasks = {}
        self._running_task = None  # 当前正在运行的任务
        self._task_queue = []  # 任务队列

        # 设置日志
        self.logger = logging.getLogger(f"TaskExecutor.{device_config.device_name}")

        # 连接信号 - 使用新的处理方式
        self.task_completed.connect(self._handle_task_completed)
        self.task_failed.connect(self._handle_task_failed)

        # 使用信号连接处理下一个任务，避免递归锁问题
        self.process_next_task_signal.connect(self._process_next_task, Qt.QueuedConnection)

    def start(self):
        """启动任务执行器"""
        with QMutexLocker(self._mutex):
            if self._active:
                return True

            try:
                self._active = True
                self.state.update_status(DeviceStatus.IDLE)
                self.logger.info(f"任务执行器 {self.device_name} 已启动")
                self.executor_started.emit()
                return True
            except Exception as e:
                self.state.update_status(DeviceStatus.ERROR, str(e))
                self.logger.error(f"启动任务执行器失败: {e}")
                return False

    def _initialize_resources(self,resource_path:str)-> bool:
        """初始化资源"""
        try:
            # 特定实现的资源初始化
            self.resource_path = resource_path
            self.resource = Resource()
            self.resource.post_bundle(resource_path).wait()
            return True
        except Exception as e:
            self.logger.error(f"资源初始化失败: {e}")
            raise

    @Slot()
    def _process_next_task(self):
        """处理队列中的下一个任务"""
        with QMutexLocker(self._mutex):
            # 如果执行器未激活或已有任务正在执行，则退出
            if not self._active or self._running_task:
                return

            # 如果队列为空，则退出
            if not self._task_queue:
                self.state.update_status(DeviceStatus.IDLE)
                self.state.current_task = None
                return

            # 按优先级排序队列
            self._task_queue.sort(key=lambda t: t.priority.value)

            # 获取下一个任务
            task = self._task_queue.pop(0)
            self._running_task = task

            if self.resource_path!=task.data.resource_path:
                self._initialize_resources(task.data.resource_path)
            if self._controller:
                self._controller.post_connection().wait()
            self._tasker.bind(resource=self.resource,controller=self._controller)
            # 创建任务执行器
            runner = TaskRunner(task, self)
            runner.setAutoDelete(True)

            # 启动任务，不再设置线程优先级
            self.thread_pool.start(runner)

            # 更新设备状态
            self.state.update_status(DeviceStatus.RUNNING)
            self.state.current_task = task

            self.logger.info(f"设备 {self.device_name} 开始执行任务 {task.id}")

    # 使用新的槽函数处理任务完成，避免在信号处理中直接使用锁
    @Slot(str, object)
    def _handle_task_completed(self, task_id):
        """任务完成处理器 - 安全方式"""
        with QMutexLocker(self._mutex):
            if self._running_task and self._running_task.id == task_id:
                # task = self._running_task
                # self._running_task = None
                # self.state.stats["tasks_completed"] += 1
                # self.state.task_history.append({
                #     "id": task_id,
                #     "status": "completed",
                #     "runtime": (task.completed_at - task.started_at).total_seconds()
                # })

                # 更新总运行时间统计
                # self.state.stats["total_runtime"] += (task.completed_at - task.started_at).total_seconds()

                # 通过信号异步触发下一个任务处理
                self.process_next_task_signal.emit()

    @Slot(str, str)
    def _handle_task_failed(self, task_id, error):
        """任务失败处理器 - 安全方式"""
        with QMutexLocker(self._mutex):
            if self._running_task and self._running_task.id == task_id:
                # task = self._running_task
                # self._running_task = None
                # self.state.stats["tasks_failed"] += 1
                # self.state.task_history.append({
                #     "id": task_id,
                #     "status": "failed",
                #     "error": error
                # })

                # 通过信号异步触发下一个任务处理
                self.process_next_task_signal.emit()


    def submit_task(self, task_data: RunTimeConfigs, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """提交任务到执行队列"""
        with QMutexLocker(self._mutex):
            if not self._active:
                raise RuntimeError("任务执行器未运行")

            task = Task(task_data, priority)
            self._pending_tasks[task.id] = task

            # 将任务添加到队列
            self._task_queue.append(task)
            self.task_queued.emit(task.id)

            self.logger.info(f"任务 {task.id} 已提交到设备 {self.device_name} 队列，优先级 {priority.name}")

            # 如果当前没有任务在执行，则通过信号异步触发任务处理
            if not self._running_task:
                self.process_next_task_signal.emit()

            return task.id

    def stop(self):
        """停止任务执行器"""
        with QMutexLocker(self._mutex):
            if not self._active:
                return

            self.logger.info(f"正在停止任务执行器 {self.device_name}")
            self._active = False
            self.state.update_status(DeviceStatus.STOPPING)

            # 清空任务队列
            for task in self._task_queue:
                task.status = TaskStatus.CANCELED
                self.task_canceled.emit(task.id)
            self._task_queue.clear()

            # 清理资源
            if self._tasker:
                try:
                    # self._tasker.cleanup()
                    pass  # 实际清理代码的占位符
                except Exception as e:
                    self.logger.error(f"清理资源时出错: {e}")

            self.logger.info(f"任务执行器 {self.device_name} 已停止")
            self.executor_stopped.emit()

    def get_state(self):
        """获取执行器当前状态"""
        with QMutexLocker(self._mutex):
            return self.state

    def get_queue_length(self):
        """获取队列中等待的任务数量"""
        with QMutexLocker(self._mutex):
            return len(self._task_queue)

class TaskRunner(QRunnable):
    """任务执行器，在QThreadPool中运行"""

    def __init__(self, task: Task, executor: TaskExecutor):
        super().__init__()
        self.task = task
        self.executor = executor
        self.tasker = executor._tasker
        self.canceled = False
        # 将Runner关联到任务，便于取消
        self.task.runner = self
        self.logger = logging.getLogger(f"TaskRunner.{task.id}")

    def run(self):
        """运行任务"""
        self.task.status = TaskStatus.RUNNING
        self.task.started_at = datetime.now()

        # 通知任务开始
        self.executor.task_started.emit(self.task.id)

        try:
            if self.canceled:
                self.task.status = TaskStatus.CANCELED
                self.executor.task_canceled.emit(self.task.id)
                return

            self.logger.info(f"执行任务 {self.task}")

            # 实际任务执行逻辑
            result = self.execute_task(self.task.data)

            if self.canceled:
                self.task.status = TaskStatus.CANCELED
                self.executor.task_canceled.emit(self.task.id)
                return

            # 任务成功完成
            self.task.status = TaskStatus.COMPLETED
            self.task.completed_at = datetime.now()
            self.executor.task_completed.emit(self.task.id, result)

        except Exception as e:
            if self.canceled:
                self.task.status = TaskStatus.CANCELED
                self.executor.task_canceled.emit(self.task.id)
            else:
                # 任务执行失败
                self.task.status = TaskStatus.FAILED
                self.task.error = str(e)
                self.task.completed_at = datetime.now()
                self.logger.error(f"任务 {self.task.id} 失败: {e}")
                self.executor.task_failed.emit(self.task.id, str(e))

    def execute_task(self, task_data):
        """执行具体任务的方法，需要子类实现"""
        # 实际应用中，这里需要根据不同任务类型实现具体的执行逻辑
        for task in task_data.task_list:
            self.tasker.post_task(task.task_entry,task.pipeline_override)
        # 可以在这里添加进度更新
        self.executor.progress_updated.emit(self.task.id, 50)

        time.sleep(0.5)  # 继续模拟任务执行
        return {"result": "success", "data": task_data}
