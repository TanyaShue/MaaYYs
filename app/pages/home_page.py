import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from app.components.log_display import LogDisplay
from app.models.config.global_config import global_config
from app.models.logging.log_manager import log_manager


class HomePage(QWidget):
    device_added = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = global_config
        self.init_ui()

        # Log startup message
        self.log_startup_message()

    def log_startup_message(self):
        """记录应用启动日志，包含日志处理相关信息"""
        app_logger = log_manager.get_app_logger()
        app_logger.info("MFWPH已启动")
        app_logger.info(f"日志存储路径: {os.path.abspath(log_manager.log_dir)}")

        # 如果刚才进行了日志备份，记录一条信息
        backup_dir = log_manager.backup_dir
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("logs_backup_")]
        if backup_files:
            # 获取最新的备份文件
            latest_backup = max(backup_files)
            app_logger.info(f"启动时发现日志超过10MB，已备份至: {os.path.join('backup', latest_backup)}")

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("设备管理系统")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Welcome message
        welcome_label = QLabel("欢迎使用设备管理系统")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("Arial", 14))
        main_layout.addWidget(welcome_label)

        # Instructions
        instructions_label = QLabel("请从左侧导航栏选择设备或系统功能")
        instructions_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(instructions_label)

        # Summary info
        summary_frame = QFrame()
        summary_frame.setObjectName("summaryFrame")
        summary_frame.setFrameShape(QFrame.StyledPanel)
        summary_layout = QVBoxLayout(summary_frame)

        devices = self.global_config.get_devices_config().devices
        device_count_label = QLabel(f"当前设备总数: {len(devices)}")
        device_count_label.setAlignment(Qt.AlignCenter)
        device_count_label.setFont(QFont("Arial", 12))
        summary_layout.addWidget(device_count_label)

        # You can add more summary info here if needed

        main_layout.addWidget(summary_frame)
        main_layout.addStretch()

        # Log display for system logs
        self.log_display = LogDisplay()
        self.log_display.hide()  # Hidden by default
        main_layout.addWidget(self.log_display)

    def connect_signals(self):
        """Connect log manager signals to log display updates"""
        log_manager.app_log_updated.connect(self.on_app_log_updated)

    def on_app_log_updated(self):
        """Handle app log updates"""
        # If currently showing all logs, refresh
        if self.log_display.current_device == "all":
            self.log_display.request_logs_update()

    def show_all_logs(self):
        """Show all logs"""
        self.log_display.show()
        self.log_display.device_selector.setCurrentIndex(0)