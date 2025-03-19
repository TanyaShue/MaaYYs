from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QPushButton, QComboBox, QFrame
)
from PySide6.QtGui import QFont

from app.models.logging.log_manager import log_manager


class LogDisplay(QFrame):
    """
    Component to display application and device logs with real-time updates
    """

    # Signal to request log updates
    log_update_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logDisplay")
        self.setFrameShape(QFrame.StyledPanel)

        # Current display mode: "all" or device name
        self.current_device = "all"

        self.init_ui()

        # Connect the update signal
        self.log_update_requested.connect(self.update_logs)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Header with title and controls
        header_layout = QHBoxLayout()

        # Log display title
        title_label = QLabel("系统日志")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)

        # Dropdown for device selection
        self.device_selector = QComboBox()
        self.device_selector.addItem("全部日志", "all")
        self.device_selector.currentIndexChanged.connect(self.on_device_changed)
        header_layout.addWidget(self.device_selector)

        main_layout.addLayout(header_layout)

        # Log text display area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMinimumHeight(150)
        self.log_text.setPlaceholderText("暂无日志记录")
        main_layout.addWidget(self.log_text)

    def update_device_list(self, devices):
        """Update the device dropdown list"""
        # Store current selection
        current_index = self.device_selector.currentIndex()
        current_data = self.device_selector.currentData() if current_index >= 0 else "all"

        # Clear and repopulate
        self.device_selector.clear()
        self.device_selector.addItem("全部日志", "all")

        for device in devices:
            self.device_selector.addItem(device.device_name, device.device_name)

        # Try to restore previous selection
        new_index = self.device_selector.findData(current_data)
        if new_index >= 0:
            self.device_selector.setCurrentIndex(new_index)
        else:
            self.device_selector.setCurrentIndex(0)

        # Refresh logs for current selection
        self.request_logs_update()

    def on_device_changed(self, index):
        """Handle device selection change"""
        if index >= 0:
            self.current_device = self.device_selector.currentData()
            self.request_logs_update()

    def request_logs_update(self):
        """Request a log update for the current device"""
        self.log_update_requested.emit(self.current_device)

    def update_logs(self, device_name=None):
        """Update logs in response to a signal"""
        device_to_update = device_name if device_name else self.current_device

        self.log_text.clear()

        if device_to_update == "all":
            logs = log_manager.get_all_logs()
        else:
            logs = log_manager.get_device_logs(device_to_update)

        if logs:
            self.log_text.setPlainText("".join(logs))
            # Scroll to bottom to show latest logs
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
        else:
            self.log_text.setPlainText("暂无日志记录")

    def show_device_logs(self, device_name):
        """Show logs for a specific device"""
        # Find and select the device in the dropdown
        index = self.device_selector.findData(device_name)
        if index >= 0:
            self.device_selector.setCurrentIndex(index)
        else:
            # If device not found, add it
            self.device_selector.addItem(device_name, device_name)
            self.device_selector.setCurrentIndex(self.device_selector.count() - 1)

    def on_close(self):
        """关闭日志显示区域"""
        # 找到HomePage并调整分割器
        parent = self.parent()
        while parent and not hasattr(parent, 'content_splitter'):
            parent = parent.parent()

        if parent and hasattr(parent, 'content_splitter'):
            # 获取当前分割器大小
            sizes = parent.content_splitter.sizes()
            # 设置日志区域为0高度
            parent.content_splitter.setSizes([sizes[0] + sizes[1], 0])