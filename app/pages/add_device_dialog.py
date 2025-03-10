from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QPushButton, QComboBox,
                               QWidget, QCheckBox, QGroupBox, QScrollArea,
                               QTimeEdit)
from PySide6.QtCore import Qt, QTime, QThread, Signal

from maa.toolkit import Toolkit
from app.models.config.device_config import DeviceConfig,AdbDevice

class DeviceSearchThread(QThread):
    """用于后台搜索设备的线程"""
    devices_found = Signal(list)
    search_error = Signal(str)

    def __init__(self, adb_path):
        super().__init__()
        self.adb_path = adb_path

    def run(self):
        try:
            devices=Toolkit.find_adb_devices()

            self.devices_found.emit(devices)

        except Exception as e:
            self.search_error.emit(str(e))


class AddDeviceDialog(QDialog):
    def __init__(self, global_config, parent=None):
        super().__init__(parent)
        self.global_config = global_config
        self.found_devices = []
        self.search_thread = None

        self.setWindowTitle("添加设备")
        self.setMinimumSize(500, 500)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 设备搜索区域
        search_group = QGroupBox("设备搜索")
        search_layout = QVBoxLayout()

        # 搜索按钮和结果显示
        search_btn_layout = QHBoxLayout()
        self.search_btn = QPushButton("搜索设备")
        self.search_btn.clicked.connect(self.search_devices)
        self.search_status = QLabel("未搜索")

        search_btn_layout.addWidget(self.search_btn)
        search_btn_layout.addWidget(self.search_status)
        search_btn_layout.addStretch()

        # 设备选择下拉框
        device_select_layout = QHBoxLayout()
        device_select_layout.addWidget(QLabel("发现的设备:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(250)
        self.device_combo.currentIndexChanged.connect(self.device_selected)
        device_select_layout.addWidget(self.device_combo)

        search_layout.addLayout(search_btn_layout)
        search_layout.addLayout(device_select_layout)
        search_group.setLayout(search_layout)

        scroll_layout.addWidget(search_group)

        # 设备基本信息
        info_group = QGroupBox("设备信息")
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.adb_path_edit = QLineEdit()
        # self.adb_path_edit.setText(self.global_config.get_default_adb_path())
        self.adb_address_edit = QLineEdit()
        self.screenshot_method_edit = QLineEdit()
        # self.screenshot_method_edit.setText("ADB")
        self.input_method_edit = QLineEdit()
        # self.input_method_edit.setText("ADB")
        self.config_edit = QLineEdit()

        form_layout.addRow("设备名称:", self.name_edit)
        form_layout.addRow("ADB 路径:", self.adb_path_edit)
        form_layout.addRow("ADB 地址:", self.adb_address_edit)
        form_layout.addRow("截图方法:", self.screenshot_method_edit)
        form_layout.addRow("输入方法:", self.input_method_edit)
        form_layout.addRow("配置:", self.config_edit)

        info_group.setLayout(form_layout)
        scroll_layout.addWidget(info_group)

        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout()

        # 计划任务设置
        self.schedule_enabled = QCheckBox("启用定时启动")

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("启动时间:"))
        self.schedule_time = QTimeEdit()
        self.schedule_time.setTime(QTime(8, 0))  # 默认早上8点
        time_layout.addWidget(self.schedule_time)
        time_layout.addStretch()

        # 命令设置
        command_layout = QFormLayout()
        self.pre_command_edit = QLineEdit()
        self.post_command_edit = QLineEdit()

        command_layout.addRow("启动前命令:", self.pre_command_edit)
        command_layout.addRow("启动后命令:", self.post_command_edit)

        advanced_layout.addWidget(self.schedule_enabled)
        advanced_layout.addLayout(time_layout)
        advanced_layout.addSpacing(10)
        advanced_layout.addLayout(command_layout)

        advanced_group.setLayout(advanced_layout)
        scroll_layout.addWidget(advanced_group)

        # 添加一些额外的空间
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 底部按钮
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")

        save_btn.clicked.connect(self.save_device)
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)

        main_layout.addLayout(buttons_layout)

    def search_devices(self):
        """在后台线程中搜索连接的设备"""
        self.search_btn.setEnabled(False)
        self.search_status.setText("正在搜索...")

        adb_path = self.adb_path_edit.text() or "adb"

        # 创建并启动搜索线程
        self.search_thread = DeviceSearchThread(adb_path)
        self.search_thread.devices_found.connect(self.on_devices_found)
        self.search_thread.search_error.connect(self.on_search_error)
        self.search_thread.finished.connect(self.on_search_completed)
        self.search_thread.start()

    def on_devices_found(self, devices):
        """处理找到的设备列表"""
        self.device_combo.clear()
        self.found_devices = devices

        if devices:
            for device in devices:
                self.device_combo.addItem(device.address)
            self.search_status.setText(f"找到 {len(devices)} 个设备")
        else:
            self.device_combo.addItem("未找到设备")
            self.search_status.setText("未找到设备")

    def on_search_error(self, error_msg):
        """处理搜索错误"""
        self.device_combo.clear()
        self.device_combo.addItem(f"搜索出错")
        self.search_status.setText(f"搜索出错: {error_msg}")

    def on_search_completed(self):
        """搜索完成后的清理工作"""
        self.search_btn.setEnabled(True)
        self.search_thread = None

    def device_selected(self, index):
        """当用户从下拉框选择设备时调用"""
        if 0 <= index < len(self.found_devices):
            device = self.found_devices[index]
            self.adb_address_edit.setText(device.address)
            self.adb_path_edit.setText(str(device.adb_path))
            self.screenshot_method_edit.setText(str(device.screencap_methods))
            self.input_method_edit.setText(str(device.input_methods))
            self.config_edit.setText(str(device.config))
            # 根据设备 ID 自动生成一个设备名称
            if not self.name_edit.text():
                self.name_edit.setText(f"设备 {device.address}")

    def save_device(self):
        """保存设备信息"""
        # 检查必填字段
        if not self.name_edit.text() or not self.adb_address_edit.text():
            return

        try:
            import json

            # 尝试解析配置文本为字典，如果解析失败则使用空字典
            try:
                config_text = self.config_edit.text()
                config_dict = json.loads(config_text) if config_text.strip() != "" else {}
            except json.JSONDecodeError as e:
                print("配置数据格式错误，无法解析为字典。", e)
                config_dict = {}

            device_config = DeviceConfig(
                device_name=self.name_edit.text(),
                adb_config=AdbDevice(
                    name=self.name_edit.text(),
                    adb_path=self.adb_path_edit.text(),
                    address=self.adb_address_edit.text(),
                    screencap_methods=int(self.screenshot_method_edit.text()),
                    input_methods=int(self.input_method_edit.text()),
                    config=config_dict
                ),
                schedule_enabled=self.schedule_enabled.isChecked(),
                schedule_time=[self.schedule_time.time().toString("hh:mm")],
                start_command=self.pre_command_edit.text(),
            )

            # 添加设备到配置中
            self.global_config.devices_config.devices.append(device_config)
            self.global_config.save_all_configs()
            # 关闭对话框
            self.accept()

        except Exception as e:
            print(f"保存设备时出错: {e}")