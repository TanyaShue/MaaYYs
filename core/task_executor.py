# -*- coding: UTF-8 -*-
import importlib.util
import logging
import os
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable, QMutexLocker, QRecursiveMutex, Qt
from maa.controller import AdbController
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit

from app.models.config import DeviceConfig
from app.models.config.global_config import RunTimeConfigs


class TaskStatus(Enum):
    """任务执行状态枚举"""
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    CANCELED = "canceled"  # 已取消


class TaskPriority(Enum):
    """任务优先级枚举"""
    HIGH = 0  # 高优先级
    NORMAL = 1  # 普通优先级
    LOW = 2  # 低优先级


class Task:
    """统一任务表示"""

    def __init__(self, task_data: RunTimeConfigs, priority: TaskPriority = TaskPriority.NORMAL):
        self.id = f"task_{id(self)}"  # 唯一任务ID
        self.data = task_data  # 任务数据
        self.priority = priority  # 任务优先级
        self.status = TaskStatus.PENDING  # 任务状态
        self.created_at = datetime.now()  # 创建时间
        self.started_at = None  # 开始时间
        self.completed_at = None  # 完成时间
        self.error = None  # 错误信息
        self.runner = None  # 任务执行器引用


class DeviceStatus(Enum):
    """设备状态枚举"""
    IDLE = "idle"  # 空闲状态
    RUNNING = "running"  # 运行状态
    ERROR = "error"  # 错误状态
    STOPPING = "stopping"  # 正在停止


class DeviceState(QObject):
    """设备状态类"""
    status_changed = Signal(str)  # 状态变化信号
    error_occurred = Signal(str)  # 错误信号

    def __init__(self):
        super().__init__()
        self.status = DeviceStatus.IDLE  # 初始状态为空闲
        self.created_at = datetime.now()  # 创建时间
        self.last_active = datetime.now()  # 最后活动时间
        self.current_task = None  # 当前任务
        self.error = None  # 错误信息

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
    # 核心信号定义
    task_started = Signal(str)  # 任务开始信号
    task_completed = Signal(str, object)  # 任务完成信号
    task_failed = Signal(str, str)  # 任务失败信号
    task_canceled = Signal(str)  # 任务取消信号
    progress_updated = Signal(str, int)  # 任务进度更新信号
    executor_started = Signal()  # 执行器启动信号
    executor_stopped = Signal()  # 执行器停止信号
    task_queued = Signal(str)  # 任务入队信号
    process_next_task_signal = Signal()  # 触发下一个任务处理的信号

    def __init__(self, device_config: DeviceConfig, parent=None):
        super().__init__(parent)
        self.device_name = device_config.device_name
        self.device_config = device_config
        self.resource_path: Optional[str] = None

        # 初始化ADB控制器
        adb_config = device_config.adb_config
        self._controller = AdbController(
            adb_config.adb_path,
            adb_config.address,
            adb_config.screencap_methods,
            adb_config.input_methods,
            adb_config.config
        )

        # 设备状态管理
        self.state = DeviceState()
        self._tasker: Optional[Tasker] = Tasker()

        # 使用全局线程池
        self.thread_pool = QThreadPool.globalInstance()

        # 互斥锁和状态控制
        self._active = False  # 激活状态
        self._mutex = QRecursiveMutex()  # 递归互斥锁

        # 任务管理
        self._running_task = None  # 当前正在运行的任务
        self._task_queue = []  # 任务队列

        # 日志配置
        self.logger = logging.getLogger(f"TaskExecutor.{device_config.device_name}")

        # 信号连接
        self.task_completed.connect(self._handle_task_completed)
        self.task_failed.connect(self._handle_task_failed)
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

    def _initialize_resources(self, resource_path: str) -> bool:
        """初始化MAA资源"""
        try:
            self.resource_path = resource_path
            self.resource = Resource()
            self.resource.post_bundle(resource_path).wait()
            return True
        except Exception as e:
            self.logger.error(f"资源初始化失败: {e}")
            raise

    def load_custom_objects(self, custom_dir):
        if not os.path.exists(custom_dir):
            self.logger.warning(f"自定义文件夹 {custom_dir} 不存在")
            return

        if not os.listdir(custom_dir):
            self.logger.warning(f"自定义文件夹 {custom_dir} 为空")
            return

        # 遍历模块类型文件夹
        for module_type, base_class in [("custom_actions", CustomAction),
                                        ("custom_recognition", CustomRecognition)]:
            module_type_dir = os.path.join(custom_dir, module_type)

            if not os.path.exists(module_type_dir):
                self.logger.warning(f"{module_type} 文件夹不存在于 {custom_dir}")
                continue

            self.logger.info(f"开始加载 {module_type} 模块")
            print(f"开始加载 {module_type} 模块")
            # 遍历该类型目录下的所有Python文件
            for file in os.listdir(module_type_dir):
                file_path = os.path.join(module_type_dir, file)

                # 确保是文件且是Python文件
                if os.path.isfile(file_path) and file.endswith('.py'):
                    try:
                        # 使用文件名作为模块名（去除.py后缀）
                        module_name = os.path.splitext(file)[0]
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # 遍历模块中的所有属性
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)

                            # 检查是否是类并且是对应基类的子类（但不是基类本身）
                            if isinstance(attr, type) and issubclass(attr, base_class) and attr != base_class:

                                # 使用类名作为注册名
                                class_name = attr.__name__
                                instance = attr()

                                if module_type == "custom_actions":
                                    if self.resource.register_custom_action(class_name, instance):
                                        self.logger.info(f"加载自定义动作 {class_name} 成功")
                                        print(f"加载自定义动作 {class_name} 成功")

                                elif module_type == "custom_recognition":
                                    if self.resource.register_custom_recognition(class_name, instance):
                                        self.logger.info(f"加载自定义识别器 {class_name} 成功")

                    except Exception as e:
                        self.logger.error(f"加载自定义内容时发生错误 {file_path}: {e}")

    @Slot()
    def _process_next_task(self):
        """处理队列中的下一个任务"""
        with QMutexLocker(self._mutex):
            # 检查执行器状态和任务队列
            if not self._active or self._running_task or not self._task_queue:
                if not self._task_queue and self._active and not self._running_task:
                    self.state.update_status(DeviceStatus.IDLE)
                    self.state.current_task = None
                return

            # 按优先级排序并获取下一个任务
            self._task_queue.sort(key=lambda t: t.priority.value)
            task = self._task_queue.pop(0)
            self._running_task = task
            current_dir = os.getcwd()
            Toolkit.init_option(os.path.join(current_dir, "assets"))
            # 初始化资源和控制器
            if self.resource_path != task.data.resource_path:
                self._initialize_resources(task.data.resource_path)

            if self._controller:
                self._controller.post_connection().wait()

            self.resource.clear_custom_action()
            self.resource.clear_custom_recognition()

            self._tasker.bind(resource=self.resource, controller=self._controller)
            self.load_custom_objects(os.path.join(task.data.resource_path, "custom_dir"))

            # 创建并启动任务执行器
            runner = TaskRunner(task, self)
            runner.setAutoDelete(True)
            self.thread_pool.start(runner)

            # 更新设备状态
            self.state.update_status(DeviceStatus.RUNNING)
            self.state.current_task = task
            self.logger.info(f"设备 {self.device_name} 开始执行任务 {task.id}")

    @Slot(str, object)
    def _handle_task_completed(self, task_id):
        """任务完成处理器"""
        with QMutexLocker(self._mutex):
            if self._running_task and self._running_task.id == task_id:
                self._running_task = None
                self.process_next_task_signal.emit()

    @Slot(str, str)
    def _handle_task_failed(self, task_id, error):
        """任务失败处理器"""
        with QMutexLocker(self._mutex):
            if self._running_task and self._running_task.id == task_id:
                self._running_task = None
                self.process_next_task_signal.emit()

    def submit_task(self, task_data: RunTimeConfigs | list[RunTimeConfigs],
                    priority: TaskPriority = TaskPriority.NORMAL) -> str | list[str]:
        """提交任务到执行队列

        如果 task_data 是单个 RunTimeConfigs，则返回任务 id（str），
        如果 task_data 是列表，则为每个配置创建一个任务，并返回任务 id 列表。
        """
        with QMutexLocker(self._mutex):
            if not self._active:
                raise RuntimeError("任务执行器未运行")

            task_ids = []
            # 如果传入的是列表，则依次为每个配置创建任务
            if isinstance(task_data, list):
                for data in task_data:
                    task = Task(data, priority)
                    self._task_queue.append(task)
                    self.task_queued.emit(task.id)
                    print(f"任务 {task.id} 已提交到设备 {self.device_name} 队列，优先级 {priority.name}")
                    print(f"当前任务队列{self._task_queue},当前任务{task.data}")
                    task_ids.append(task.id)
            else:
                task = Task(task_data, priority)
                self._task_queue.append(task)
                self.task_queued.emit(task.id)
                print(f"任务 {task.id} 已提交到设备 {self.device_name} 队列，优先级 {priority.name}")
                task_ids.append(task.id)

            # 如果当前没有任务在执行，则触发任务处理
            if not self._running_task:
                self.process_next_task_signal.emit()
            print("----------------")

            # 如果只有一个任务则返回单个 id，否则返回 id 列表
            return task_ids[0] if len(task_ids) == 1 else task_ids

    def stop(self):
        """停止任务执行器"""
        with QMutexLocker(self._mutex):
            if not self._active:
                return

            self.logger.info(f"正在停止任务执行器 {self.device_name}")
            self._active = False
            self.state.update_status(DeviceStatus.STOPPING)

            # 取消队列中的所有任务
            for task in self._task_queue:
                task.status = TaskStatus.CANCELED
                self.task_canceled.emit(task.id)
            self._task_queue.clear()

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
        self.task.runner = self
        self.logger = logging.getLogger(f"TaskRunner.{task.id}")

    def run(self):
        """运行任务"""
        self.task.status = TaskStatus.RUNNING
        self.task.started_at = datetime.now()
        self.executor.task_started.emit(self.task.id)

        try:
            # 检查是否已取消
            if self.canceled:
                self.task.status = TaskStatus.CANCELED
                self.executor.task_canceled.emit(self.task.id)
                return

            print(f"开始执行任务 {self.task.data}")

            # 执行任务
            result = self.execute_task(self.task.data)

            # 再次检查是否已取消
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
        """执行具体任务的方法"""
        # 执行所有任务列表中的任务
        for task in task_data.task_list:
            self.tasker.post_task(task.task_entry, task.pipeline_override).wait()
        # 发送进度更新信号
        self.executor.progress_updated.emit(self.task.id, 50)

        # 简单延迟，确保任务有时间执行
        time.sleep(0.5)

        return {"result": "success", "data": task_data}