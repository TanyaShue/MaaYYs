from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QLabel
)

from app.models.config.global_config import global_config
from app.widgets.basic_info_widget import BasicInfoWidget
from app.widgets.device_log_widget import DeviceLogWidget
from app.widgets.resource_widget import ResourceWidget
from app.widgets.task_settings_widget import TaskSettingsWidget


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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # Set widget style
        self.setObjectName("content_widget")

        # Title
        title_label = QLabel(f"设备: {self.device_name}")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setFixedHeight(40)  # Set fixed height for the title
        main_layout.addWidget(title_label)

        # Main horizontal splitter (3 parts)
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        self.horizontal_splitter.setObjectName("horizontalSplitter")
        self.horizontal_splitter.setHandleWidth(0)
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
        self.left_splitter.setHandleWidth(0)
        self.left_splitter.setChildrenCollapsible(False)

        # Create widgets
        self.basic_info_widget = BasicInfoWidget(self.device_name, self.device_config, self)
        self.resource_widget = ResourceWidget(self.device_name, self.device_config, self)
        self.task_settings_widget = TaskSettingsWidget(self.device_config, self)
        self.log_widget = DeviceLogWidget(self.device_name, self)

        # Connect signals
        self.resource_widget.resource_selected.connect(self.task_settings_widget.show_resource_settings)

        # Connect the new resource status changed signal
        self.resource_widget.resource_status_changed.connect(self.task_settings_widget.update_resource_status)

        # Add widgets to splitters
        self.left_splitter.addWidget(self.basic_info_widget)
        self.left_splitter.addWidget(self.resource_widget)

        # Set initial sizes for left splitter (1:2 ratio for basic info and resource selection)
        self.left_splitter.setSizes([100, 300])

        left_layout.addWidget(self.left_splitter)

        # Add all parts to horizontal splitter
        self.horizontal_splitter.addWidget(left_widget)
        self.horizontal_splitter.addWidget(self.task_settings_widget)
        self.horizontal_splitter.addWidget(self.log_widget)

        # Set initial sizes for horizontal splitter (1:1:1 ratio)
        self.horizontal_splitter.setSizes([400, 400, 300])

        main_layout.addWidget(self.horizontal_splitter)

    def run_device_tasks(self):
        """Run device tasks - delegate to basic info widget"""
        self.basic_info_widget.run_device_tasks()

    def refresh_ui(self):
        """Refresh all UI components with updated device config"""
        self.device_config = global_config.get_device_config(self.device_name)
        self.basic_info_widget.refresh_ui(self.device_config)
        self.resource_widget.refresh_ui(self.device_config)
        self.task_settings_widget.clear_settings()