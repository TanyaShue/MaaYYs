from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from app.models.config.global_config import global_config
from core.tasker_manager import task_manager


class DeviceCard(QFrame):
    def __init__(self, device_name, device_type, status, parent=None):
        super().__init__(parent)
        self.setObjectName("deviceCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        # 设置每张卡片的最大高度（例如 150 像素）
        self.setMaximumHeight(150)

        layout = QVBoxLayout(self)

        # 设备名称标签
        name_label = QLabel(device_name)
        name_label.setObjectName("deviceCardName")
        layout.addWidget(name_label)

        # 设备类型标签
        type_label = QLabel(device_type)
        type_label.setObjectName("deviceCardType")
        layout.addWidget(type_label)

        # 状态指示布局
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

        # 按钮布局
        button_layout = QHBoxLayout()
        run_btn = QPushButton("运行")
        run_btn.clicked.connect(lambda :task_manager.run_device_all_resource_task(global_config.get_device_config(device_name)))
        run_btn.setFixedHeight(28)
        settings_btn = QPushButton("设置")
        settings_btn.setFixedHeight(28)

        button_layout.addWidget(run_btn)
        button_layout.addWidget(settings_btn)
        layout.addLayout(button_layout)
