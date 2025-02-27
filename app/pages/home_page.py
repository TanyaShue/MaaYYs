from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame, QPushButton, QHBoxLayout
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from app.components import DeviceCard
from app.models.config.global_config import GlobalConfig




class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = GlobalConfig()
        self.init_ui()
        self.load_sample_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 大标题放在 QFrame 之外
        title_label = QLabel("设备管理系统")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        main_layout.addWidget(title_label)

        # 创建滚动区域，内部用单个 QFrame 承载卡片布局
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QFrame()  # 单一 QFrame 作为卡片容器
        self.scroll_content.setFrameShape(QFrame.StyledPanel)
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area)

    def load_sample_data(self):
        try:
            devices_config_path = "assets/config/devices.json"
            self.global_config.load_devices_config(devices_config_path)

            resource_dir = "assets/resource"
            self.global_config.load_all_resources_from_directory(resource_dir)

            self.populate_device_cards()
        except Exception as e:
            print(f"Error loading config files: {e}")

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

        except Exception as e:
            print(f"Error populating device cards: {e}")
            error_label = QLabel("无法加载设备配置")
            error_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)


