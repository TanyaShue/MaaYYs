from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox
)

from app.models.config.global_config import global_config
from app.models.logging.log_manager import log_manager
from core.tasker_manager import task_manager


class ResourceWidget(QFrame):
    """Resource selection widget with table of available resources"""

    # Signal to notify when a resource is selected for configuration
    resource_selected = Signal(str)

    # New signal to notify when a resource's enable status changes
    resource_status_changed = Signal(str, bool)

    def __init__(self, device_name, device_config, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.device_config = device_config

        self.setObjectName("resourceFrame")
        self.setFrameShape(QFrame.StyledPanel)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Header with section title and count
        header_layout = QHBoxLayout()

        # Section title
        section_title = QLabel("资源选择")
        section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section_title.setObjectName("sectionTitle")

        header_layout.addWidget(section_title)
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
        one_key_start_btn.clicked.connect(self.run_all_resources)
        layout.addWidget(one_key_start_btn)

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
            run_btn.clicked.connect(lambda checked, r_name=resource_name:
                                    task_manager.run_resource_task(self.device_config, r_name))

            settings_btn = QPushButton()
            settings_btn.setFixedSize(32, 32)
            settings_btn.setIcon(QIcon("assets/icons/settings.svg"))
            settings_btn.setIconSize(QSize(16, 16))
            settings_btn.setToolTip("配置此资源")
            settings_btn.clicked.connect(lambda checked, r_name=resource_name:
                                         self.show_resource_settings(r_name))

            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)
            button_layout.addStretch()
            table.setCellWidget(row, 2, button_widget)
            table.setRowHeight(row, 48)  # Increase row height for better spacing

        return table

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

        # Emit signal with resource name and new status
        self.resource_status_changed.emit(resource_name, enabled)

    def show_resource_settings(self, resource_name):
        """Emit signal to show settings for the selected resource"""
        self.resource_selected.emit(resource_name)

    def run_all_resources(self):
        """Run all enabled resources for this device"""
        try:
            if self.device_config:
                # Log the start of task execution
                log_manager.log_device_info(self.device_name, f"开始执行所有资源任务")
                # Execute tasks
                task_manager.run_device_all_resource_task(self.device_config)
                # Log completion
                log_manager.log_device_info(self.device_name, f"所有资源任务执行完成")
        except Exception as e:
            # Log error
            log_manager.log_device_error(self.device_name, f"运行任务时出错: {str(e)}")

    def refresh_ui(self, device_config):
        """Refresh widget with updated device config"""
        self.device_config = device_config
        # Remove current layout
        self.setLayout(None)
        # Reinitialize UI
        self.init_ui()