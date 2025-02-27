from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class DeviceCard(QFrame):
    def __init__(self, device_name, device_type, status):
        super().__init__()
        self.setObjectName("deviceCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        layout = QVBoxLayout(self)

        # Device name label
        name_label = QLabel(device_name)
        name_label.setObjectName("deviceCardName")
        layout.addWidget(name_label)

        # Device type label
        type_label = QLabel(device_type)
        type_label.setObjectName("deviceCardType")
        layout.addWidget(type_label)

        # Status indicator
        status_layout = QHBoxLayout()
        status_indicator = QLabel()
        status_indicator.setFixedSize(10, 10)
        status_indicator.setObjectName("statusIndicator" + ("Normal" if status == "运行正常" else "Error"))
        status_text = QLabel(status)
        status_text.setObjectName("statusText")

        status_layout.addWidget(status_indicator)
        status_layout.addWidget(status_text)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Buttons
        button_layout = QHBoxLayout()
        run_btn = QPushButton("运行")
        run_btn.setFixedHeight(28)
        settings_btn = QPushButton("设置")
        settings_btn.setFixedHeight(28)

        button_layout.addWidget(run_btn)
        button_layout.addWidget(settings_btn)

        layout.addLayout(button_layout)
