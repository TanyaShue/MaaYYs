import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame, QPushButton, QHBoxLayout, \
    QSplitter

from app.components.device_card import DeviceCard
from app.components.log_display import LogDisplay
from app.models.config.global_config import global_config
from app.models.logging.log_manager import log_manager
from app.pages.add_device_dialog import AddDeviceDialog


class HomePage(QWidget):
    device_added = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = global_config
        self.init_ui()
        self.connect_signals()
        self.load_sample_data()

        # 初始化后记录应用启动日志
        self.log_startup_message()

    def log_startup_message(self):
        """记录应用启动日志，包含日志处理相关信息"""
        app_logger = log_manager.get_app_logger()
        app_logger.info("MFWPH以启动")
        app_logger.info(f"日志存储路径: {os.path.abspath(log_manager.log_dir)}")
        # app_logger.info("日志将在每次应用启动时重新开始")

        # 如果刚才进行了日志备份，记录一条信息
        backup_dir = log_manager.backup_dir
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("logs_backup_")]
        if backup_files:
            # 获取最新的备份文件
            latest_backup = max(backup_files)
            app_logger.info(f"启动时发现日志超过10MB，已备份至: {os.path.join('backup', latest_backup)}")

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 标题栏布局，包含标题和添加设备按钮
        title_bar = QHBoxLayout()

        # 大标题
        title_label = QLabel("设备管理系统")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        title_bar.addWidget(title_label)

        # 添加设备按钮
        add_device_btn = QPushButton("添加设备")
        add_device_btn.setObjectName("addDeviceButton")
        add_device_btn.setFixedHeight(32)
        add_device_btn.clicked.connect(self.open_add_device_dialog)

        # 查看全部日志按钮
        view_logs_btn = QPushButton("全部日志")
        view_logs_btn.setObjectName("viewLogsButton")
        view_logs_btn.setFixedHeight(32)
        view_logs_btn.clicked.connect(self.view_all_logs)

        # 按钮容器
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(view_logs_btn)
        buttons_layout.addWidget(add_device_btn)
        title_bar.addLayout(buttons_layout)

        main_layout.addLayout(title_bar)

        # 创建内容分割器 - 上面是设备卡片，下面是日志显示区域
        self.content_splitter = QSplitter(Qt.Vertical)

        # 设备卡片区域
        cards_widget = QWidget()
        cards_layout = QVBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域，内部用单个 QFrame 承载卡片布局
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QFrame()  # 单一 QFrame 作为卡片容器
        self.scroll_content.setFrameShape(QFrame.StyledPanel)
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(self.scroll_content)
        cards_layout.addWidget(scroll_area)

        # 日志显示组件
        self.log_display = LogDisplay()

        # 添加到分割器
        self.content_splitter.addWidget(cards_widget)
        self.content_splitter.addWidget(self.log_display)

        # 设置分割器初始大小比例（日志区域初始隐藏但保留空间）
        self.content_splitter.setSizes([500, 0])

        main_layout.addWidget(self.content_splitter)

    def connect_signals(self):
        """Connect log manager signals to log display updates"""
        # Connect app log updates
        log_manager.app_log_updated.connect(self.on_app_log_updated)

        # Connect device log updates
        log_manager.device_log_updated.connect(self.on_device_log_updated)

    def on_app_log_updated(self):
        """Handle app log updates"""
        # If currently showing all logs, refresh
        if self.log_display.current_device == "all":
            self.log_display.request_logs_update()

    def on_device_log_updated(self, device_name):
        """Handle device log updates"""
        # If currently showing this device's logs, refresh
        if self.log_display.current_device == device_name:
            self.log_display.request_logs_update()
        # Also refresh if showing all logs
        elif self.log_display.current_device == "all":
            self.log_display.request_logs_update()

    def load_sample_data(self):
        try:
            devices_config_path = "assets/config/devices.json"
            # 如果文件不存在，先创建该文件并写入 "{}"
            if not os.path.exists(devices_config_path):
                # 确保父目录存在
                os.makedirs(os.path.dirname(devices_config_path), exist_ok=True)
                with open(devices_config_path, "w", encoding="utf-8") as f:
                    f.write("{}")

            self.global_config.load_devices_config(devices_config_path)

            resource_dir = "assets/resource/"
            self.global_config.load_all_resources_from_directory(resource_dir)

            self.populate_device_cards()
        except Exception as e:
            error_msg = f"加载配置文件出错: {e}"
            print(error_msg)
            log_manager.get_app_logger().error(error_msg)

    def populate_device_cards(self):
        # 清空已有卡片
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            devices = self.global_config.get_devices_config().devices
            row, col = 0, 0
            max_col = 3

            for device in devices:
                status = "运行正常" if device.schedule_enabled else "未启用计划任务"
                device_card = DeviceCard(
                    device.device_name,
                    device.adb_config.name,
                    status
                )
                self.grid_layout.addWidget(device_card, row, col)
                col += 1
                if col >= max_col:
                    col = 0
                    row += 1

            # 更新日志显示组件中的设备列表
            self.log_display.update_device_list(devices)

        except Exception as e:
            error_msg = f"加载设备卡片出错: {e}"
            print(error_msg)
            log_manager.get_app_logger().error(error_msg)

            error_label = QLabel("无法加载设备配置")
            error_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)

    def open_add_device_dialog(self):
        """打开添加设备对话框"""
        dialog = AddDeviceDialog(self.global_config, self)
        if dialog.exec_():
            # 如果用户点击确定，记录日志并重新加载设备列表
            log_manager.get_app_logger().info("添加了新设备")
            self.populate_device_cards()
            # Emit the signal to notify other components
            self.device_added.emit()

    def view_all_logs(self):
        """查看所有日志"""
        # 显示日志区域
        self.show_log_display()
        # 确保选择"全部日志"
        self.log_display.device_selector.setCurrentIndex(0)

    def show_device_logs(self, device_name):
        """显示特定设备的日志"""
        # 显示日志区域
        self.show_log_display()
        # 显示特定设备的日志
        self.log_display.show_device_logs(device_name)

    def show_log_display(self):
        """显示日志区域"""
        # 确保日志显示组件是可见的
        self.log_display.show()

        # 获取当前分割器大小
        sizes = self.content_splitter.sizes()
        if sizes[1] == 0:  # 如果日志区域高度为0
            # 调整分割器比例，设置为卡片区域70%，日志区域30%
            total_height = sum(sizes)
            self.content_splitter.setSizes([int(total_height * 0.7), int(total_height * 0.3)])