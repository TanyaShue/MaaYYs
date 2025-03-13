from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QBrush, QTextCursor
from PySide6.QtCore import Qt

from app.models.logging.log_manager import log_manager


class LogTab(QWidget):
    def __init__(self, device_config, parent=None):
        super().__init__(parent)
        self.device_config = device_config
        self.device_name = device_config.device_name
        self.init_ui()

        # Connect to log manager signals for real-time updates
        log_manager.device_log_updated.connect(self.update_logs)

        # Initial log load
        self.update_logs(self.device_name)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # Header with title and refresh button
        header_layout = QHBoxLayout()

        log_label = QLabel("设备日志")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        log_label.setObjectName("sectionTitle")
        header_layout.addWidget(log_label)

        # Add refresh button
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedWidth(60)
        refresh_btn.clicked.connect(lambda: self.update_logs(self.device_name))
        header_layout.addWidget(refresh_btn)

        header_layout.addStretch()

        # Add legend for log levels
        info_label = QLabel("信息")
        info_label.setStyleSheet("color: #000000;")
        header_layout.addWidget(info_label)

        warning_label = QLabel("警告")
        warning_label.setStyleSheet("color: #FF8C00;")
        header_layout.addWidget(warning_label)

        error_label = QLabel("错误")
        error_label.setStyleSheet("color: #FF0000;")
        header_layout.addWidget(error_label)

        self.layout.addLayout(header_layout)

        # Log text display area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("logTextEdit")
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setPlaceholderText(f"暂无 {self.device_name} 日志记录")
        self.layout.addWidget(self.log_text)

        # Define color formats for different log levels
        self.format_info = QTextCharFormat()
        self.format_info.setForeground(QBrush(QColor("#000000")))

        self.format_warning = QTextCharFormat()
        self.format_warning.setForeground(QBrush(QColor("#FF8C00")))

        self.format_error = QTextCharFormat()
        self.format_error.setForeground(QBrush(QColor("#FF0000")))

    def update_logs(self, device_name):
        """Update logs when signal is received or refresh is requested"""
        # Only update if this is our device
        if device_name != self.device_name:
            return

        self.log_text.clear()

        # Get device logs from log manager
        logs = log_manager.get_device_logs(self.device_name)

        if logs:
            # Process logs with color formatting
            self.format_logs(logs)

            # Scroll to bottom to show latest logs
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
        else:
            self.log_text.setPlainText(f"暂无 {self.device_name} 日志记录")

    def format_logs(self, logs):
        """Format logs with different colors based on log level"""
        cursor = self.log_text.textCursor()

        for log_line in logs:
            # Determine log level from the line content
            if " - ERROR - " in log_line:
                format_to_use = self.format_error
            elif " - WARNING - " in log_line:
                format_to_use = self.format_warning
            else:
                format_to_use = self.format_info

            # Insert text with the appropriate format
            cursor.insertText(log_line, format_to_use)

        self.log_text.setTextCursor(cursor)

    def clear_logs(self):
        """Clear all logs from the display"""
        self.log_text.clear()