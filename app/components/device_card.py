from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from app.models.config.global_config import global_config
from app.models.logging.log_manager import log_manager
from app.pages.add_device_dialog import AddDeviceDialog
from core.tasker_manager import task_manager


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
        run_btn.clicked.connect(self.run_device_tasks)
        run_btn.setFixedHeight(28)

        logs_btn = QPushButton("日志")
        logs_btn.clicked.connect(self.view_device_logs)
        logs_btn.setFixedHeight(28)

        settings_btn = QPushButton("设置")
        settings_btn.setFixedHeight(28)
        settings_btn.clicked.connect(self.open_settings_dialog)

        button_layout.addWidget(run_btn)
        button_layout.addWidget(logs_btn)
        button_layout.addWidget(settings_btn)
        layout.addLayout(button_layout)

    def run_device_tasks(self):
        """运行设备任务并记录日志"""
        try:
            device_config = global_config.get_device_config(self.device_name)
            if device_config:
                # 记录开始运行的日志
                log_manager.log_device_info(self.device_name, f"开始执行设备任务")
                # 执行任务
                task_manager.run_device_all_resource_task(device_config)
                # 记录完成日志
                log_manager.log_device_info(self.device_name, f"设备任务执行完成")
        except Exception as e:
            # 记录错误日志
            log_manager.log_device_error(self.device_name, f"运行任务时出错: {str(e)}")

    def view_device_logs(self):
        """查看设备日志"""
        # 寻找主窗口中的日志显示组件
        home_page = self.find_home_page()
        if home_page:
            # 显示该设备的日志
            home_page.show_device_logs(self.device_name)

    def find_home_page(self):
        """查找HomePage实例"""
        # 向上遍历父级组件
        parent_widget = self.parent()
        while parent_widget:
            # 向上遍历直到找到根窗口
            if parent_widget.parent() is None:
                # 找到根窗口后尝试获取HomePage实例
                from app.pages.home_page import HomePage
                for child in parent_widget.findChildren(HomePage):
                    return child
            parent_widget = parent_widget.parent()
        return None

    def open_settings_dialog(self):
        """打开设备设置对话框"""
        # 获取当前设备的配置信息
        device_config = global_config.get_device_config(self.device_name)
        if device_config:
            # 创建设置对话框并传入设备配置
            dialog = AddDeviceDialog(global_config, self, edit_mode=True, device_config=device_config)
            if dialog.exec_():
                # 记录配置变更日志
                log_manager.log_device_info(self.device_name, "设备配置已更新")

                # 如果用户点击保存，更新设备信息
                # 这里可能需要刷新卡片显示
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'populate_device_cards'):
                    parent_widget = parent_widget.parent()

                if parent_widget and hasattr(parent_widget, 'populate_device_cards'):
                    parent_widget.populate_device_cards()