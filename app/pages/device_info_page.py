import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QComboBox, QLineEdit, QToolButton,
    QStyleFactory
)

from app.models.config.global_config import global_config
from app.components.log_display import LogDisplay
from app.models.logging.log_manager import log_manager
from core.tasker_manager import task_manager
from app.pages.add_device_dialog import AddDeviceDialog
from app.components.collapsible_widget import CollapsibleWidget, DraggableContainer
from app.models.config.resource_config import SelectOption, BoolOption, InputOption


class DeviceInfoPage(QWidget):
    """Device information page with horizontal three-part layout"""

    def __init__(self, device_name, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.device_config = global_config.get_device_config(device_name)
        self.selected_resource_name = None
        self.task_option_widgets = {}

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(15)

        # Set widget style
        self.setObjectName("content_widget")

        title_label = QLabel(f"设备: {self.device_name}")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setFixedHeight(10)  # Set fixed height for the title
        main_layout.addWidget(title_label)

        # Main horizontal splitter (3 parts)
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        self.horizontal_splitter.setObjectName("horizontalSplitter")
        self.horizontal_splitter.setHandleWidth(2)
        self.horizontal_splitter.setChildrenCollapsible(False)

        # 1. Left Part (Basic Info & Resource Selection)
        left_widget = QWidget()
        left_widget.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Vertical splitter for left part
        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.setObjectName("leftSplitter")
        self.left_splitter.setHandleWidth(2)
        self.left_splitter.setChildrenCollapsible(False)

        # Top of left part (Basic Info)
        self.basic_info_widget = self.create_basic_info_widget()
        self.left_splitter.addWidget(self.basic_info_widget)

        # Bottom of left part (Resource Selection - improved)
        self.resource_widget = self.create_resource_widget()
        self.left_splitter.addWidget(self.resource_widget)

        # Set initial sizes for left splitter (1:2 ratio for basic info and resource selection)
        self.left_splitter.setSizes([100, 200])

        left_layout.addWidget(self.left_splitter)

        # 2. Middle Part (Task Settings - improved)
        self.task_settings_widget = self.create_task_settings_widget()

        # 3. Right Part (Log Display)
        self.log_widget = self.create_log_widget()

        # Add all parts to horizontal splitter
        self.horizontal_splitter.addWidget(left_widget)
        self.horizontal_splitter.addWidget(self.task_settings_widget)
        self.horizontal_splitter.addWidget(self.log_widget)

        # Set initial sizes for horizontal splitter (30% left, 40% middle, 30% right)
        self.horizontal_splitter.setSizes([40, 40, 30])

        main_layout.addWidget(self.horizontal_splitter)

    def create_basic_info_widget(self):
        """Create the basic info widget (top of left part)"""
        frame = QFrame()
        frame.setObjectName("infoFrame")
        frame.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0,0,0,0)
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
            status_text = "运行正常" if self.device_config.schedule_enabled else "未启用计划任务"
            status_indicator = QLabel()
            status_indicator.setFixedSize(12, 12)
            status_indicator.setObjectName("statusIndicator" + ("Normal" if status_text == "运行正常" else "Error"))
            status_value = QLabel(status_text)
            status_value.setObjectName("statusText")
            status_layout.addWidget(status_label)
            status_layout.addWidget(status_indicator)
            status_layout.addWidget(status_value)
            status_layout.addStretch()
            content_layout.addLayout(status_layout)
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

        return frame

    def create_resource_widget(self):
        """Create the resource selection widget (bottom of left part) with functionality"""
        frame = QFrame()
        frame.setObjectName("resourceFrame")
        frame.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header with section title and count
        header_layout = QHBoxLayout()

        # Section title
        section_title = QLabel("资源选择")
        section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section_title.setObjectName("sectionTitle")

        # Resource count badge
        resource_count = 0
        if self.device_config and hasattr(self.device_config, 'resources'):
            resource_count = len(self.device_config.resources)
        count_label = QLabel(f"{resource_count}")
        count_label.setObjectName("countBadge")
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setFixedSize(24, 24)

        header_layout.addWidget(section_title)
        header_layout.addWidget(count_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Create resource table
        self.resource_table = self.create_resource_table()
        layout.addWidget(self.resource_table)

        # "One Key Start" button
        one_key_start_btn = QPushButton("一键启动所有资源")
        one_key_start_btn.setIcon(QIcon("assets/icons/rocket.svg"))
        one_key_start_btn.setIconSize(QSize(16, 16))
        one_key_start_btn.setObjectName("oneKeyButton")
        one_key_start_btn.clicked.connect(self.run_device_tasks)
        layout.addWidget(one_key_start_btn)

        return frame

    def create_resource_table(self):
        """Create a table for resource selection similar to ControlTab with enhanced styling"""
        # Get all available resources
        all_resources = global_config.get_all_resource_configs()

        # Create mapping of enabled resources for this device
        resource_enabled_map = {}
        if self.device_config and hasattr(self.device_config, 'resources'):
            resource_enabled_map = {r.resource_name: r.enable for r in self.device_config.resources}

        # Create table
        table = QTableWidget(len(all_resources), 3)
        table.setObjectName("resourceTable")
        table.setHorizontalHeaderLabels(["启用", "资源名称", "操作"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.setColumnWidth(0, 60)
        table.setColumnWidth(2, 150)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setFrameShape(QFrame.NoFrame)
        table.setShowGrid(False)
        table.setFocusPolicy(Qt.NoFocus)
        table.setSelectionMode(QTableWidget.NoSelection)

        for row, resource_config in enumerate(all_resources):
            resource_name = resource_config.resource_name

            # Checkbox for enabling/disabling the resource
            checkbox = QCheckBox()
            checkbox.setChecked(resource_enabled_map.get(resource_name, False))
            checkbox.stateChanged.connect(
                lambda state, r_name=resource_name, cb=checkbox:
                self.update_resource_enable_status(r_name, cb.isChecked())
            )
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(10, 2, 5, 2)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            table.setCellWidget(row, 0, checkbox_widget)

            # Resource name
            name_item = QTableWidgetItem(f"{resource_name}")
            name_item.setFont(QFont("Segoe UI", 10, QFont.Medium))
            table.setItem(row, 1, name_item)

            # Action buttons
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)
            button_layout.setSpacing(8)

            run_btn = QPushButton()
            run_btn.setFixedSize(32, 32)
            run_btn.setIcon(QIcon("assets/icons/play.svg"))
            run_btn.setIconSize(QSize(16, 16))
            run_btn.setToolTip("运行此资源")
            # run_btn.setObjectName("iconButton")
            run_btn.clicked.connect(lambda checked, r_name=resource_name:
                                    task_manager.run_resource_task(self.device_config, r_name))

            settings_btn = QPushButton()
            settings_btn.setFixedSize(32, 32)
            settings_btn.setIcon(QIcon("assets/icons/settings.svg"))
            settings_btn.setIconSize(QSize(16, 16))
            settings_btn.setToolTip("配置此资源")
            # settings_btn.setObjectName("iconButton")
            settings_btn.clicked.connect(lambda checked, r_name=resource_name:
                                         self.show_resource_settings(r_name))

            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)
            button_layout.addStretch()
            table.setCellWidget(row, 2, button_widget)
            table.setRowHeight(row, 48)  # Increase row height for better spacing

        return table

    def create_task_settings_widget(self):
        """Create the task settings widget (middle part) with enhanced styling"""
        frame = QFrame()
        frame.setObjectName("taskSettingsFrame")
        frame.setFrameShape(QFrame.StyledPanel)

        self.task_settings_layout = QVBoxLayout(frame)
        self.task_settings_layout.setContentsMargins(0,0,0,0)
        self.task_settings_layout.setSpacing(12)

        # Header with title and help button
        header_layout = QHBoxLayout()

        # Section title
        section_title = QLabel("任务设置")
        section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section_title.setObjectName("sectionTitle")

        # Help button
        help_btn = QToolButton()
        help_btn.setIcon(QIcon("assets/icons/help.svg"))
        help_btn.setIconSize(QSize(16, 16))
        help_btn.setToolTip("任务设置帮助")
        help_btn.setObjectName("helpButton")

        header_layout.addWidget(section_title)
        header_layout.addStretch()
        header_layout.addWidget(help_btn)

        self.task_settings_layout.addLayout(header_layout)

        # Content area with card-like appearance
        content_card = QFrame()
        content_card.setObjectName("contentCard")
        content_card.setFrameShape(QFrame.StyledPanel)

        card_layout = QVBoxLayout(content_card)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # Content area for resource settings (initially empty)
        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        self.settings_content_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_content_layout.setSpacing(15)

        # Add initial message with icon
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_layout.setSpacing(15)

        placeholder_icon = QLabel()
        placeholder_icon.setPixmap(QIcon("assets/icons/settings-gear.svg").pixmap(48, 48))
        placeholder_icon.setAlignment(Qt.AlignCenter)

        initial_message = QLabel("请从左侧资源列表中选择一个资源进行设置")
        initial_message.setAlignment(Qt.AlignCenter)
        initial_message.setObjectName("placeholderText")

        sub_message = QLabel("点击资源列表中的设置按钮来配置任务")
        sub_message.setAlignment(Qt.AlignCenter)
        sub_message.setObjectName("subText")

        placeholder_layout.addWidget(placeholder_icon)
        placeholder_layout.addWidget(initial_message)
        placeholder_layout.addWidget(sub_message)

        self.settings_content_layout.addWidget(placeholder_widget)

        card_layout.addWidget(self.settings_content)
        self.task_settings_layout.addWidget(content_card)
        self.task_settings_layout.addStretch()

        return frame

    def create_log_widget(self):
        """Create the log display widget (right part) with enhanced styling"""
        frame = QFrame()
        frame.setObjectName("logFrame")
        frame.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(12)

        # Header with title and controls
        header_layout = QHBoxLayout()

        # Section title
        section_title = QLabel("设备日志")
        section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section_title.setObjectName("sectionTitle")

        # Control buttons
        clear_btn = QToolButton()
        clear_btn.setIcon(QIcon("assets/icons/trash.svg"))
        clear_btn.setIconSize(QSize(16, 16))
        clear_btn.setToolTip("清除日志")
        clear_btn.setObjectName("logControlButton")

        refresh_btn = QToolButton()
        refresh_btn.setIcon(QIcon("assets/icons/refresh.svg"))
        refresh_btn.setIconSize(QSize(16, 16))
        refresh_btn.setToolTip("刷新日志")
        refresh_btn.clicked.connect(lambda: self.log_display.request_logs_update())
        refresh_btn.setObjectName("logControlButton")

        filter_btn = QToolButton()
        filter_btn.setIcon(QIcon("assets/icons/filter.svg"))
        filter_btn.setIconSize(QSize(16, 16))
        filter_btn.setToolTip("过滤日志")
        filter_btn.setObjectName("logControlButton")

        header_layout.addWidget(section_title)
        header_layout.addStretch()
        header_layout.addWidget(filter_btn)
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Log display
        log_container = QFrame()
        log_container.setObjectName("logContainer")
        log_container.setFrameShape(QFrame.StyledPanel)

        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)

        self.log_display = LogDisplay()
        self.log_display.setObjectName("logDisplay")
        self.log_display.show_device_logs(self.device_name)

        log_layout.addWidget(self.log_display)
        layout.addWidget(log_container)

        return frame

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
                # Update logs display
                self.log_display.request_logs_update()
        except Exception as e:
            # Log error
            log_manager.log_device_error(self.device_name, f"运行任务时出错: {str(e)}")
            # Update logs display
            self.log_display.request_logs_update()

    def open_settings_dialog(self):
        """Open device settings dialog"""
        if self.device_config:
            dialog = AddDeviceDialog(global_config, self, edit_mode=True, device_config=self.device_config)
            if dialog.exec_():
                # Log configuration change
                log_manager.log_device_info(self.device_name, "设备配置已更新")
                # Refresh device config
                self.device_config = global_config.get_device_config(self.device_name)
                # Refresh UI
                self.refresh_ui()

    def refresh_ui(self):
        """Refresh UI with updated device config"""
        # Replace the basic info widget
        old_basic_info = self.left_splitter.widget(0)
        self.left_splitter.replaceWidget(0, self.create_basic_info_widget())
        if old_basic_info:
            old_basic_info.deleteLater()

        # Replace the resource widget
        old_resource_widget = self.left_splitter.widget(1)
        self.left_splitter.replaceWidget(1, self.create_resource_widget())
        if old_resource_widget:
            old_resource_widget.deleteLater()

        # Clear task settings
        self._clear_layout(self.settings_content_layout)
        initial_message = QLabel("请从左侧资源列表中选择一个资源进行设置")
        initial_message.setAlignment(Qt.AlignCenter)
        initial_message.setObjectName("placeholderText")
        self.settings_content_layout.addWidget(initial_message)

    def update_resource_enable_status(self, resource_name, enabled):
        """Update the enable status of a resource"""
        if not self.device_config:
            return

        # Find the resource in device config
        resource = next((r for r in self.device_config.resources if r.resource_name == resource_name), None)

        if resource:
            resource.enable = enabled
        else:
            # Log error if resource doesn't exist
            log_manager.log_device_info(self.device_name, f"资源 {resource_name} 不存在，无法更新状态")
            return

        # Save the updated configuration
        global_config.save_all_configs()

        # Log the change
        status_text = "启用" if enabled else "禁用"
        log_manager.log_device_info(self.device_name, f"资源 {resource_name} 已{status_text}")

    def show_resource_settings(self, resource_name):
        """Show settings for the selected resource with enhanced styling"""
        self.selected_resource_name = resource_name

        # Clear current settings content
        self._clear_layout(self.settings_content_layout)

        # Get resource configurations
        full_resource_config = global_config.get_resource_config(resource_name)
        if not full_resource_config:
            # Show error message if resource config not found
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_layout.setAlignment(Qt.AlignCenter)

            error_icon = QLabel()
            error_icon.setPixmap(QIcon("assets/icons/error.svg").pixmap(48, 48))
            error_icon.setAlignment(Qt.AlignCenter)

            error_label = QLabel(f"未找到资源 {resource_name} 的配置信息")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setObjectName("errorText")

            error_layout.addWidget(error_icon)
            error_layout.addWidget(error_label)

            self.settings_content_layout.addWidget(error_widget)
            return

        # Get device-specific resource config
        device_resource = None
        if self.device_config:
            device_resource = next((r for r in self.device_config.resources if r.resource_name == resource_name), None)

        if not device_resource:
            # Show message if device has no configuration for this resource
            no_config_widget = QWidget()
            no_config_layout = QVBoxLayout(no_config_widget)
            no_config_layout.setAlignment(Qt.AlignCenter)

            warning_icon = QLabel()
            warning_icon.setPixmap(QIcon("assets/icons/warning.svg").pixmap(48, 48))
            warning_icon.setAlignment(Qt.AlignCenter)

            no_config_label = QLabel(f"设备未配置资源 {resource_name}")
            no_config_label.setAlignment(Qt.AlignCenter)
            no_config_label.setObjectName("warningText")

            action_btn = QPushButton("添加资源配置")
            action_btn.setObjectName("primaryButton")
            action_btn.setFixedWidth(150)

            no_config_layout.addWidget(warning_icon)
            no_config_layout.addWidget(no_config_label)
            no_config_layout.addSpacing(15)
            no_config_layout.addWidget(action_btn, 0, Qt.AlignCenter)

            self.settings_content_layout.addWidget(no_config_widget)
            return

        # Create resource settings UI with header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        resource_name_label = QLabel(f"{resource_name}")
        resource_name_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        resource_name_label.setObjectName("resourceSettingsTitle")

        # Add resource status indicator
        status_indicator = QWidget()
        status_layout = QHBoxLayout(status_indicator)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)

        status_dot = QLabel()
        status_dot.setFixedSize(8, 8)
        status_dot.setStyleSheet(
            f"background-color: {'#34a853' if device_resource.enable else '#ea4335'}; border-radius: 4px;")

        status_text = QLabel(f"{'已启用' if device_resource.enable else '已禁用'}")
        status_text.setObjectName("statusText")
        status_text.setStyleSheet(f"color: {'#34a853' if device_resource.enable else '#ea4335'}; font-size: 12px;")

        status_layout.addWidget(status_dot)
        status_layout.addWidget(status_text)

        header_layout.addWidget(resource_name_label)
        header_layout.addStretch()
        header_layout.addWidget(status_indicator)

        self.settings_content_layout.addWidget(header_widget)

        # Add description if available
        if hasattr(full_resource_config, 'description') and full_resource_config.description:
            description_label = QLabel(full_resource_config.description)
            description_label.setObjectName("resourceDescription")
            description_label.setWordWrap(True)
            description_label.setContentsMargins(0, 0, 0, 10)
            self.settings_content_layout.addWidget(description_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumHeight(1)
        separator.setObjectName("separator")
        self.settings_content_layout.addWidget(separator)
        self.settings_content_layout.addSpacing(10)

        # Instructions for drag & drop
        instructions = QLabel("拖放任务可调整执行顺序")
        instructions.setObjectName("instructionText")
        instructions.setAlignment(Qt.AlignCenter)
        self.settings_content_layout.addWidget(instructions)
        self.settings_content_layout.addSpacing(10)

        # Create scroll area for tasks
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Create draggable container for tasks
        scroll_content = DraggableContainer()
        scroll_content.setObjectName('draggableContainer')
        scroll_content.layout.setContentsMargins(0, 0, 0, 0)
        scroll_content.layout.setSpacing(10)
        scroll_content.layout.installEventFilter(self)
        scroll_content.drag.connect(self.on_drag_tasks)

        # Get task order information
        task_order_map = {task.task_name: idx for idx, task in enumerate(full_resource_config.resource_tasks)}
        selected_order = {task_name: idx for idx, task_name in enumerate(device_resource.selected_tasks or [])}

        # Sort tasks by selection status and order
        sorted_tasks = sorted(
            full_resource_config.resource_tasks,
            key=lambda task: (
                0 if task.task_name in selected_order else 1,
                selected_order.get(task.task_name, task_order_map.get(task.task_name, float('inf')))
            )
        )

        # Create task widgets
        self.task_option_widgets = {}  # Store widgets for later reference

        for task in sorted_tasks:
            # Create collapsible widget
            options_widget = CollapsibleWidget(task.task_name)
            options_widget.setObjectName("taskItem")

            is_task_selected = task.task_name in selected_order
            options_widget.checkbox.setChecked(is_task_selected)

            # Add drag handle indicator to header
            drag_icon = QLabel("≡")
            drag_icon.setFixedWidth(20)
            drag_icon.setAlignment(Qt.AlignCenter)
            drag_icon.setStyleSheet("color: #80868b; font-size: 16px;")
            options_widget.header_layout.insertWidget(0, drag_icon)

            options_widget.checkbox.stateChanged.connect(
                lambda state, t_name=task.task_name, cb=options_widget.checkbox:
                self.update_task_selection(device_resource, t_name, cb.isChecked())
            )

            # Add option widgets if task has options
            if hasattr(task, 'option') and task.option:
                for option_name in task.option:
                    for option in full_resource_config.options:
                        if option.name == option_name:
                            option_widget = self._create_option_widget(
                                option, option_name,
                                {opt.option_name: opt for opt in device_resource.options},
                                task.task_name,
                                self.task_option_widgets,
                                device_resource
                            )
                            options_widget.content_layout.addWidget(option_widget)
            else:
                no_options_label = QLabel("该任务没有可配置的选项")
                no_options_label.setObjectName("noOptionsLabel")
                no_options_label.setWordWrap(True)
                options_widget.content_layout.addWidget(no_options_label)

            scroll_content.layout.addWidget(options_widget)

        scroll_content.layout.addStretch()
        scroll_area.setWidget(scroll_content)
        self.settings_content_layout.addWidget(scroll_area)

    def _create_option_widget(self, option, option_name, current_options, task_name, task_options_map, resource_config):
        """Create a widget for an option based on its type with enhanced styling"""
        option_widget = QWidget()
        option_widget.setObjectName("optionWidget")

        option_layout = QHBoxLayout(option_widget)
        option_layout.setContentsMargins(10, 8, 10, 8)
        option_layout.setSpacing(15)

        # Option label with tooltip if description exists
        option_label = QLabel(option.name)
        option_label.setObjectName("optionLabel")
        if hasattr(option, 'description') and option.description:
            option_label.setToolTip(option.description)
            info_icon = QLabel("ℹ️")
            info_icon.setFixedWidth(16)
            info_icon.setToolTip(option.description)
            option_layout.addWidget(info_icon)

        option_layout.addWidget(option_label)
        option_layout.addStretch()

        # Create control based on option type
        if isinstance(option, SelectOption):
            widget = QComboBox()
            widget.setObjectName("optionComboBox")

            for choice in option.choices:
                widget.addItem(choice.name, choice.value)
            if option_name in current_options:
                index = widget.findData(current_options[option_name].value)
                if index >= 0:
                    widget.setCurrentIndex(index)
            widget.currentIndexChanged.connect(
                lambda index, w=widget, o_name=option_name, res_config=resource_config:
                self.update_option_value(res_config, o_name, w.currentData())
            )
        elif isinstance(option, BoolOption):
            widget = QCheckBox()
            widget.setObjectName("optionCheckBox")
            if option_name in current_options:
                widget.setChecked(current_options[option_name].value)
            else:
                widget.setChecked(option.default)
            widget.stateChanged.connect(
                lambda state, o_name=option_name, cb=widget, res_config=resource_config:
                self.update_option_value(res_config, o_name, cb.isChecked())
            )
        elif isinstance(option, InputOption):
            widget = QLineEdit()
            widget.setObjectName("optionLineEdit")

            if option_name in current_options:
                widget.setText(str(current_options[option_name].value))
            else:
                widget.setText(str(option.default))
            widget.editingFinished.connect(
                lambda o_name=option_name, le=widget, res_config=resource_config:
                self.update_option_value(res_config, o_name, le.text())
            )

            # Add placeholder text based on option type
            if hasattr(option, 'option_type'):
                if option.option_type == 'number':
                    # For numeric input
                    widget.setPlaceholderText("输入数字...")
                elif option.option_type == 'text':
                    # For text input
                    widget.setPlaceholderText("输入文本...")
        else:
            widget = QLabel("不支持的选项类型")
            widget.setStyleSheet("color: #ea4335; font-style: italic;")

        option_layout.addWidget(widget)
        task_options_map[(task_name, option_name)] = widget

        return option_widget

    def update_task_selection(self, resource_config, task_name, is_selected):
        """Update task selection status with improved UI feedback"""
        if not resource_config:
            return

        if not hasattr(resource_config, 'selected_tasks') or resource_config.selected_tasks is None:
            resource_config.selected_tasks = []

        if is_selected and task_name not in resource_config.selected_tasks:
            resource_config.selected_tasks.append(task_name)
        elif not is_selected and task_name in resource_config.selected_tasks:
            resource_config.selected_tasks.remove(task_name)

        # Save the updated configuration
        global_config.save_all_configs()

        # Update task count label if present
        for i in range(self.settings_content_layout.count()):
            widget = self.settings_content_layout.itemAt(i).widget()
            if isinstance(widget, QWidget):
                count_label = widget.findChild(QLabel, "countLabel")
                if count_label and resource_config:
                    count_label.setText(f"{len(resource_config.selected_tasks or [])} 个已选择")
                    break

        # Log the change with more details
        status_text = "已选择" if is_selected else "已取消选择"
        device_name = self.device_name if hasattr(self, 'device_name') else "未知设备"
        resource_name = resource_config.resource_name if hasattr(resource_config, 'resource_name') else "未知资源"
        log_manager.log_device_info(device_name, f"资源 [{resource_name}] 的任务 [{task_name}] {status_text}")

    def update_option_value(self, resource_config, option_name, value):
        """Update option value for a resource with improved feedback"""
        if not resource_config:
            return

        if not hasattr(resource_config, 'options') or resource_config.options is None:
            resource_config.options = []

        # Find existing option or create a new one
        option = next((opt for opt in resource_config.options if opt.option_name == option_name), None)

        if option:
            # Convert value to appropriate type if needed
            if isinstance(option.value, bool) and not isinstance(value, bool):
                if str(value).lower() in ['true', '1', 'yes', 'y']:
                    value = True
                else:
                    value = False
            elif isinstance(option.value, int) and not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    # Log error if conversion fails
                    log_manager.log_device_error(self.device_name, f"选项 {option_name} 的值 '{value}' 无法转换为整数")
                    return
            elif isinstance(option.value, float) and not isinstance(value, float):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    # Log error if conversion fails
                    log_manager.log_device_error(self.device_name,
                                                f"选项 {option_name} 的值 '{value}' 无法转换为浮点数")
                    return

            # Save the previous value for comparison
            prev_value = option.value
            option.value = value

            # Save the updated configuration
            global_config.save_all_configs()

            # Create a readable string representation for logging
            if isinstance(value, bool):
                value_str = "启用" if value else "禁用"
            else:
                value_str = str(value)

            # Log the change with more details
            resource_name = resource_config.resource_name if hasattr(resource_config, 'resource_name') else "未知资源"
            log_manager.log_device_info(
                self.device_name,
                f"资源 [{resource_name}] 的选项 [{option_name}] 已更新: {prev_value} → {value_str}"
            )
        else:
            # Log error if option doesn't exist
            log_manager.log_device_error(self.device_name, f"选项 {option_name} 不存在，无法更新")
            return

    def on_drag_tasks(self, current_order):
        """Handle task drag-and-drop reordering"""
        if not hasattr(self, 'selected_resource_name') or not self.selected_resource_name:
            return

        if not self.device_config:
            return

        resource_config = next(
            (r for r in self.device_config.resources if r.resource_name == self.selected_resource_name), None)
        if not resource_config:
            return

        # Update task order
        resource_config.selected_tasks = [
            task for task in current_order if task in resource_config.selected_tasks
        ]

        # Save the updated configuration
        global_config.save_all_configs()

        # Log the change
        log_manager.log_device_info(self.device_name, f"资源 {self.selected_resource_name} 的任务顺序已更新")

    def _clear_layout(self, layout):
        """Clear all widgets from a layout"""
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())