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
        layout = QVBoxLayout(self)

        # Add title
        title_label = QLabel("设备管理系统")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # Create scroll area for devices
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(self.scroll_content)
        layout.addWidget(scroll_area)

    def load_sample_data(self):
        try:
            # Sample path for devices config
            devices_config_path = "assets/config/devices.json"
            self.global_config.load_devices_config(devices_config_path)

            # Load all resource configs from assets/resource directory
            resource_dir = "assets/resource"
            self.global_config.load_all_resources_from_directory(resource_dir)

            # Populate device cards after loading configs
            self.populate_device_cards()
        except Exception as e:
            # In case of error, create fallback config
            print(f"Error loading config files: {e}")
            # self.create_fallback_configs()

    # def create_fallback_configs(self):
    #     """Create sample configuration data for testing when files can't be loaded"""
    #     import json
    #     from app.models.config.device_config import DevicesConfig
    #
    #     # Sample device config similar to the example in device_config.py
    #     sample_config = {
    #         "devices": [
    #             {
    #                 "device_name": "雷电模拟器-阴阳师1",
    #                 "adb_config": {
    #                     "name": "LDPlayer",
    #                     "adb_path": "D:\\leidian\\LDPlayer9\\adb.exe",
    #                     "address": "127.0.0.1:5555",
    #                     "screencap_methods": 18446744073709551559,
    #                     "input_methods": 18446744073709551607,
    #                     "config": {}
    #                 },
    #                 "resources": [],
    #                 "schedule_enabled": True,
    #                 "start_command": "D:\\leidian\\LDPlayer9\\dnplayer.exe index=0"
    #             },
    #             {
    #                 "device_name": "夜神模拟器-战双",
    #                 "adb_config": {
    #                     "name": "夜神模拟器",
    #                     "adb_path": "C:\\Android\\adb.exe",
    #                     "address": "emulator-5554",
    #                     "screencap_methods": 18446744073709551559,
    #                     "input_methods": 18446744073709551607,
    #                     "config": {}
    #                 },
    #                 "resources": [],
    #                 "schedule_enabled": False,
    #                 "start_command": ""
    #             }
    #         ]
    #     }
    #
    #     # Load the device config
    #     self.global_config.devices_config = DevicesConfig.from_dict(sample_config)
    #
    #     # Now populate the device cards
    #     self.populate_device_cards()

    def populate_device_cards(self):
        # Clear existing cards
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            # Get devices from global config
            devices = self.global_config.get_devices_config().devices

            # Define grid layout parameters
            row, col = 0, 0
            max_col = 3

            # Add device cards to grid
            for device in devices:
                # Determine device status based on schedule_enabled
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
            # Handle case when devices config is not loaded
            print(f"Error populating device cards: {e}")
            # Add a message in the grid
            error_label = QLabel("无法加载设备配置")
            error_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)