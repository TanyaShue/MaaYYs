from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame
from PySide6.QtGui import QFont

from app.components.device_card import DeviceCard
from app.models.device import Device


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Add title
        title_label = QLabel("设备管理系统")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # Add devices section label
        # devices_label = QLabel("设备信息")
        # devices_label.setFont(QFont("Arial", 14, QFont.Bold))
        # devices_label.setObjectName("sectionTitle")
        # layout.addWidget(devices_label)

        # Create scroll area for devices
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)

        # Add device cards to grid
        row, col = 0, 0
        max_col = 3

        devices = Device.get_sample_devices()
        for device in devices:
            device_card = DeviceCard(device.name, device.device_type, device.status)
            grid_layout.addWidget(device_card, row, col)

            col += 1
            if col >= max_col:
                col = 0
                row += 1

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)