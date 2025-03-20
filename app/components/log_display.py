from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QComboBox, QFrame
)

from app.models.logging.log_manager import log_manager


class LogDisplay(QFrame):
    """
    Component to display application and device logs with real-time updates
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logDisplay")
        self.setFrameShape(QFrame.StyledPanel)

        # Current display mode: "all" or device name
        self.current_device = "all"

        # Configure colors for different log levels
        self.log_colors = {
            "INFO": QColor("#888888"),  # Gray instead of blue
            "ERROR": QColor("#F44336"),  # Red
            "WARNING": QColor("#FF9800"),  # Orange
            "DEBUG": QColor("#4CAF50")  # Green
        }

        self.init_ui()

        # Connect to log manager signals
        log_manager.app_log_updated.connect(self.on_app_log_updated)
        log_manager.device_log_updated.connect(self.on_device_log_updated)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Header with title and device selector
        header_layout = QHBoxLayout()

        # Log display title
        title_label = QLabel("系统日志")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)

        # Dropdown for device selection
        self.device_selector = QComboBox()
        self.device_selector.addItem("全部日志", "all")
        self.device_selector.currentIndexChanged.connect(self.on_device_changed)
        header_layout.addStretch()
        header_layout.addWidget(self.device_selector)

        main_layout.addLayout(header_layout)

        # Log text display area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMinimumHeight(150)
        self.log_text.setPlaceholderText("暂无日志记录")
        # Set line spacing and text formatting
        self.log_text.document().setDocumentMargin(8)
        # Apply CSS styling for better spacing and wrapping
        self.log_text.setStyleSheet("""
            QTextEdit {
                line-height: 150%;
                padding: 5px;
            }
        """)

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
        if self.current_device == "all":
            logs = log_manager.get_all_logs()
        else:
            logs = log_manager.get_device_logs(self.current_device)

        self.display_logs(logs)

    def display_logs(self, logs):
        """Display logs with optimized formatting - only time and message"""
        # Store current scroll position
        scrollbar = self.log_text.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()

        # Clear text
        self.log_text.clear()

        if not logs:
            self.log_text.setPlainText("暂无日志记录")
            return

        # Process and display logs with color coding and simplified format
        for log in logs:
            try:
                # Determine log level for coloring
                if " - INFO - " in log:
                    level = "INFO"
                elif " - ERROR - " in log:
                    level = "ERROR"
                elif " - WARNING - " in log:
                    level = "WARNING"
                elif " - DEBUG - " in log:
                    level = "DEBUG"
                else:
                    level = "INFO"  # Default

                # Extract timestamp and message only
                # Format is typically: "YYYY-MM-DD HH:MM:SS,SSS - LEVEL - Message"
                parts = log.split(' - ', 2)  # Split into timestamp, level, message

                if len(parts) >= 3:
                    # Extract only the time portion (HH:MM:SS) from timestamp
                    timestamp = parts[0].strip()
                    try:
                        # Extract time part (assumes format like "YYYY-MM-DD HH:MM:SS")
                        time_part = timestamp.split(' ')[1].split(',')[0]  # Gets just HH:MM:SS
                    except IndexError:
                        time_part = timestamp  # Fallback if timestamp format is unexpected

                    message = parts[2].strip()
                    # Format log with proper spacing and indentation for wrapped lines
                    simplified_log = f"{time_part} {message}"

                    # Set color based on log level and display simplified log
                    self.log_text.setTextColor(self.log_colors.get(level, QColor("#888888")))

                    # Add the log with extra spacing between entries
                    if self.log_text.document().isEmpty():
                        self.log_text.append(simplified_log)
                    else:
                        # Insert a small height spacer and then the log
                        self.log_text.append("\n" + simplified_log)
                else:
                    # Fallback for unexpected log format
                    self.log_text.setTextColor(QColor("#888888"))
                    self.log_text.append(log.strip())

            except Exception as e:
                # For any parsing error, just show the line in default color
                self.log_text.setTextColor(QColor("#888888"))
                self.log_text.append(log.strip())

        # Restore scroll to bottom if it was at bottom
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

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

    def on_app_log_updated(self):
        """Handle app log update signal"""
        if self.current_device == "all":
            self.request_logs_update()

    def on_device_log_updated(self, device_name):
        """Handle device log update signal"""
        if self.current_device == device_name or self.current_device == "all":
            self.request_logs_update()

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