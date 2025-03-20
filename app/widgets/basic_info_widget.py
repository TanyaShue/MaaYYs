from PySide6.QtCore import Qt, QSize, QMutexLocker
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from datetime import datetime

from app.models.logging.log_manager import log_manager
from core.tasker_manager import task_manager
from app.pages.add_device_dialog import AddDeviceDialog
from app.models.config.global_config import global_config


class BasicInfoWidget(QFrame):
    """Basic device information widget"""

    def __init__(self, device_name, device_config, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.device_config = device_config
        self.parent_widget = parent

        # 设置基本属性
        self.setObjectName("infoFrame")
        self.setFrameShape(QFrame.StyledPanel)

        # 初始化UI
        self.init_ui()

        # 连接信号到状态更新函数
        self.connect_signals()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Section title
        section_title = QLabel("基本信息")
        section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section_title.setObjectName("sectionTitle")
        layout.addWidget(section_title)

        # Content container
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 5, 0, 5)
        content_layout.setSpacing(15)

        # Device details
        if self.device_config:
            # Device Name
            name_layout = QHBoxLayout()
            name_label = QLabel("设备名称:")
            name_label.setObjectName("infoLabel")
            name_value = QLabel(self.device_config.device_name)
            name_value.setObjectName("infoValue")
            name_value.setFont(QFont("Segoe UI", 13, QFont.Medium))
            name_layout.addWidget(name_label)
            name_layout.addWidget(name_value)
            name_layout.addStretch()
            content_layout.addLayout(name_layout)

            # Device Type
            type_layout = QHBoxLayout()
            type_label = QLabel("设备类型:")
            type_label.setObjectName("infoLabel")
            type_value = QLabel(self.device_config.adb_config.name)
            type_value.setObjectName("infoValue")
            type_layout.addWidget(type_label)
            type_layout.addWidget(type_value)
            type_layout.addStretch()
            content_layout.addLayout(type_layout)

            # Status
            status_layout = QHBoxLayout()
            status_label = QLabel("状态:")
            status_label.setObjectName("infoLabel")

            # 创建状态指示器和状态文本，但先不设置内容
            self.status_indicator = QLabel()
            self.status_indicator.setFixedSize(12, 12)
            self.status_indicator.setObjectName("statusIndicator")

            self.status_value = QLabel()
            self.status_value.setObjectName("statusText")
            self.status_value.setWordWrap(True)  # 允许文本换行

            status_layout.addWidget(status_label)
            status_layout.addWidget(self.status_indicator)
            status_layout.addWidget(self.status_value)
            status_layout.addStretch()

            content_layout.addLayout(status_layout)

            # 定时任务信息
            schedule_layout = QHBoxLayout()
            schedule_label = QLabel("定时任务:")
            schedule_label.setObjectName("infoLabel")

            self.schedule_value = QLabel()
            self.schedule_value.setObjectName("infoValue")
            self.schedule_value.setWordWrap(True)  # 允许文本换行

            schedule_layout.addWidget(schedule_label)
            schedule_layout.addWidget(self.schedule_value)
            schedule_layout.addStretch()

            content_layout.addLayout(schedule_layout)

            # 立即更新状态显示
            self.update_status_display()

        else:
            error_label = QLabel("未找到设备配置信息")
            error_label.setObjectName("errorText")
            content_layout.addWidget(error_label)

        layout.addWidget(content_widget)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("separator")
        separator.setMaximumHeight(1)
        layout.addWidget(separator)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        run_btn = QPushButton("运行任务")
        run_btn.setObjectName("primaryButton")
        run_btn.setIcon(QIcon("assets/icons/play.svg"))
        run_btn.clicked.connect(self.run_device_tasks)

        settings_btn = QPushButton("设备设置")
        settings_btn.setObjectName("secondaryButton")
        settings_btn.setIcon(QIcon("assets/icons/settings.svg"))
        settings_btn.clicked.connect(self.open_settings_dialog)

        button_layout.addWidget(run_btn)
        button_layout.addWidget(settings_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

    def connect_signals(self):
        """连接信号到状态更新函数"""
        # 连接TaskerManager的全局信号
        task_manager.device_added.connect(self.on_device_changed)
        task_manager.device_removed.connect(self.on_device_changed)

        # 如果设备执行器已存在，连接其信号
        if task_manager.is_device_active(self.device_name):
            self.connect_executor_signals()

    def connect_executor_signals(self):
        """连接设备执行器的信号"""
        # 获取执行器
        with QMutexLocker(task_manager._mutex):
            executor = task_manager._executors.get(self.device_name)
            if not executor:
                return

            # 连接执行器信号
            executor.task_started.connect(self.update_status_display)
            executor.task_completed.connect(self.update_status_display)
            executor.task_failed.connect(self.update_status_display)
            executor.task_canceled.connect(self.update_status_display)
            executor.progress_updated.connect(lambda *args: self.update_status_display())
            executor.executor_started.connect(self.update_status_display)
            executor.executor_stopped.connect(self.update_status_display)
            executor.task_queued.connect(self.update_status_display)

            # 连接设备状态信号
            state = executor.get_state()
            if state:
                state.status_changed.connect(lambda *args: self.update_status_display())
                state.error_occurred.connect(lambda *args: self.update_status_display())

    def on_device_changed(self, device_name):
        """设备添加/移除时的处理函数"""
        # 仅处理当前设备的变化
        if device_name != self.device_name:
            return

        # 更新显示
        self.update_status_display()

        # 如果设备现在处于活跃状态，连接其信号
        if task_manager.is_device_active(self.device_name):
            self.connect_executor_signals()

    def update_status_display(self, *args, **kwargs):
        """更新任务状态和定时任务信息显示"""
        if not self.device_config:
            return

        # 1. 更新定时任务状态
        schedule_text = ""
        next_run_time = None

        if self.device_config.schedule_enabled:
            # 获取设备的定时任务信息
            tasks_info = task_manager.get_scheduled_tasks_info()
            device_tasks = [task for task in tasks_info if task['device_name'] == self.device_name]

            if device_tasks:
                schedule_times = [task['time'] for task in device_tasks]
                schedule_text = f"已启用，执行时间: {', '.join(schedule_times)}"

                # 找出最近的下次执行时间
                next_run_times = [datetime.strptime(task['next_run'], '%Y-%m-%d %H:%M:%S') for task in device_tasks]
                if next_run_times:
                    next_run_time = min(next_run_times)
            else:
                schedule_text = "已启用，但未设置具体执行时间"
        else:
            schedule_text = "未启用"

        self.schedule_value.setText(schedule_text)

        # 2. 更新任务运行状态
        status_text = ""
        is_active = task_manager.is_device_active(self.device_name)

        if is_active:
            # 获取设备当前状态
            device_state = task_manager.get_executor_state(self.device_name)
            if device_state:
                status = device_state.status.value

                if status == "idle":
                    status_text = "空闲"
                    self.status_indicator.setObjectName("statusIndicatorNormal")
                elif status == "running":
                    status_text = "正在执行任务"
                    self.status_indicator.setObjectName("statusIndicatorRunning")
                elif status == "error":
                    status_text = f"错误: {device_state.error or '未知错误'}"
                    self.status_indicator.setObjectName("statusIndicatorError")
                elif status == "stopping":
                    status_text = "正在停止"
                    self.status_indicator.setObjectName("statusIndicatorWarning")

                # 添加当前任务信息
                if device_state.current_task:
                    task_id = device_state.current_task.id
                    status_text += f"，任务ID: {task_id}"

                # 添加队列信息
                queue_length = task_manager.get_device_queue_info().get(self.device_name, 0)
                if queue_length > 0:
                    status_text += f"，队列中还有 {queue_length} 个任务"
        else:
            status_text = "未运行"
            self.status_indicator.setObjectName("statusIndicatorIdle")

        # 添加下次执行时间信息
        if next_run_time:
            status_text += f"\n下次定时执行: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}"

        self.status_value.setText(status_text)

        # 刷新样式
        self.status_indicator.style().unpolish(self.status_indicator)
        self.status_indicator.style().polish(self.status_indicator)

    def run_device_tasks(self):
        """Run device tasks and log the action"""
        try:
            if self.device_config:
                # Log the start of task execution
                log_manager.log_device_info(self.device_name, f"开始执行设备任务")
                # Execute tasks
                task_manager.run_device_all_resource_task(self.device_config)
                # Log completion
                log_manager.log_device_info(self.device_name, f"设备任务执行完成")
                # Update status display
                self.update_status_display()

                # 如果新创建了执行器，需要连接信号
                if task_manager.is_device_active(self.device_name):
                    self.connect_executor_signals()
        except Exception as e:
            # Log error
            log_manager.log_device_error(self.device_name, f"运行任务时出错: {str(e)}")

    def open_settings_dialog(self):
        """Open device settings dialog"""
        if self.device_config:
            dialog = AddDeviceDialog(global_config, self, edit_mode=True, device_config=self.device_config)
            if dialog.exec_():
                # Log configuration change
                log_manager.log_device_info(self.device_name, "设备配置已更新")

                # 获取更新后的设备配置（假设global_config中有更新后的设备配置）
                updated_device_config = global_config.get_device_config(self.device_name)

                # 更新定时任务设置
                task_manager.update_device_scheduled_tasks(updated_device_config)
                log_manager.log_device_info(self.device_name, "设备定时任务已更新")

                # 更新本地设备配置引用
                self.device_config = updated_device_config

                # 更新状态显示
                self.update_status_display()

                # Refresh UI
                if hasattr(self.parent_widget, 'refresh_ui'):
                    self.parent_widget.refresh_ui()

    def refresh_ui(self, device_config=None):
        """Refresh widget with updated device config"""
        if device_config:
            self.device_config = device_config

        # 移除当前布局
        if self.layout():
            QWidget().setLayout(self.layout())

        # 重新初始化UI
        self.init_ui()

        # 重新连接信号
        self.connect_signals()

    def showEvent(self, event):
        """当组件显示时更新状态"""
        super().showEvent(event)
        self.update_status_display()