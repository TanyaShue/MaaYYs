from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from app.models.config.global_config import global_config
from core.tasker_manager import task_manager
from app.pages.add_device_dialog import AddDeviceDialog


class DeviceCard(QFrame):
    def __init__(self, device_name, device_type, status, parent=None):
        super().__init__(parent)
        self.device_name = device_name
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
        run_btn.clicked.connect(
            lambda: task_manager.run_device_all_resource_task(global_config.get_device_config(device_name)))
        run_btn.setFixedHeight(28)
        settings_btn = QPushButton("设置")
        settings_btn.setFixedHeight(28)
        settings_btn.clicked.connect(self.open_settings_dialog)

        button_layout.addWidget(run_btn)
        button_layout.addWidget(settings_btn)
        layout.addLayout(button_layout)

    def open_settings_dialog(self):
        """打开设备设置对话框"""
        # 获取当前设备的配置信息
        device_config = global_config.get_device_config(self.device_name)
        if device_config:
            # 创建设置对话框并传入设备配置
            dialog = AddDeviceDialog(global_config, self, edit_mode=True, device_config=device_config)
            if dialog.exec_():
                # 如果用户点击保存，更新设备信息
                # 这里可能需要刷新卡片显示
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'populate_device_cards'):
                    parent_widget = parent_widget.parent()

                if parent_widget and hasattr(parent_widget, 'populate_device_cards'):
                    parent_widget.populate_device_cards()