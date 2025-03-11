from PySide6.QtCore import Qt, QTime, QThread, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLabel, QLineEdit, QPushButton, QComboBox,
                               QWidget, QCheckBox, QGroupBox, QScrollArea,
                               QTimeEdit, QMessageBox)
from maa.toolkit import Toolkit

from app.models.config.device_config import DeviceConfig, AdbDevice


class DeviceSearchThread(QThread):
    """用于后台搜索设备的线程"""
    devices_found = Signal(list)
    search_error = Signal(str)

    def __init__(self, adb_path):
        super().__init__()
        self.adb_path = adb_path

    def run(self):
        try:
            devices = Toolkit.find_adb_devices()
            self.devices_found.emit(devices)
        except Exception as e:
            self.search_error.emit(str(e))


class AddDeviceDialog(QDialog):
    def __init__(self, global_config, parent=None, edit_mode=False, device_config=None):
        super().__init__(parent)
        self.global_config = global_config
        self.found_devices = []
        self.search_thread = None
        self.edit_mode = edit_mode
        self.device_config = device_config
        self.schedule_time_widgets = []    # 存储各个时间组件
        self.time_container_layouts = []   # 存储各行容器的布局

        self.setWindowTitle("编辑设备" if edit_mode else "添加设备")
        self.setMinimumSize(500, 500)

        self.init_ui()

        # 根据模式填充数据或添加默认时间组件
        if edit_mode and device_config:
            self.fill_device_data()
        else:
            self.add_time_selection_widget()

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
        search_btn_layout = QHBoxLayout()
        self.search_btn = QPushButton("搜索设备")
        self.search_btn.clicked.connect(self.search_devices)
        self.search_status = QLabel("未搜索")
        search_btn_layout.addWidget(self.search_btn)
        search_btn_layout.addWidget(self.search_status)
        search_btn_layout.addStretch()
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
        self.adb_address_edit = QLineEdit()
        self.screenshot_method_edit = QLineEdit()
        self.input_method_edit = QLineEdit()
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

        # 定时启动区域
        self.schedule_layout = QVBoxLayout()
        schedule_header = QHBoxLayout()
        self.schedule_enabled = QCheckBox("启用定时启动")
        self.schedule_enabled.toggled.connect(self.toggle_schedule_widgets)
        schedule_header.addWidget(self.schedule_enabled)
        self.add_time_btn = QPushButton("+")
        self.add_time_btn.setFixedSize(24, 24)
        self.add_time_btn.clicked.connect(self.add_time_selection_widget)
        self.add_time_btn.setToolTip("添加启动时间")
        schedule_header.addWidget(self.add_time_btn)
        schedule_header.addStretch()
        self.schedule_layout.addLayout(schedule_header)

        # 使用一个容器控件管理所有时间组件
        self.time_container_widget = QWidget()
        self.time_rows_container = QVBoxLayout(self.time_container_widget)
        self.schedule_layout.addWidget(self.time_container_widget)

        # 初始化第一行容器
        self.add_new_time_container()

        advanced_layout.addLayout(self.schedule_layout)

        # 命令设置
        command_layout = QFormLayout()
        self.pre_command_edit = QLineEdit()
        self.post_command_edit = QLineEdit()
        command_layout.addRow("启动前命令:", self.pre_command_edit)
        command_layout.addRow("启动后命令:", self.post_command_edit)
        advanced_layout.addSpacing(10)
        advanced_layout.addLayout(command_layout)

        advanced_group.setLayout(advanced_layout)
        scroll_layout.addWidget(advanced_group)
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 底部按钮
        buttons_layout = QHBoxLayout()
        # 如果是编辑模式，添加删除按钮
        if self.edit_mode:
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(self.delete_device)
            buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self.save_device)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        main_layout.addLayout(buttons_layout)

    def toggle_schedule_widgets(self, enabled):
        """统一控制定时启动区域的使能状态"""
        self.add_time_btn.setEnabled(enabled)
        self.time_container_widget.setEnabled(enabled)

    def add_new_time_container(self):
        """创建并添加一行时间组件的容器"""
        container_widget = QWidget()
        container_layout = QHBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 5, 0, 0)
        container_layout.setSpacing(5)
        container_layout.setAlignment(Qt.AlignLeft)
        self.time_rows_container.addWidget(container_widget)
        self.time_container_layouts.append(container_layout)
        return container_layout

    def add_time_selection_widget(self):
        """添加一个时间选择组件到当前行容器中"""
        if self.schedule_time_widgets and len(self.schedule_time_widgets) % 4 == 0:
            current_container = self.add_new_time_container()
        else:
            current_container = self.time_container_layouts[-1]
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(2)
        time_edit = QTimeEdit()
        time_edit.setTime(QTime(8, 0))
        del_btn = QPushButton("-")
        del_btn.setFixedSize(20, 20)
        del_btn.clicked.connect(lambda: self.remove_time_widget(time_widget))
        del_btn.setToolTip("删除此启动时间")
        time_layout.addWidget(time_edit)
        time_layout.addWidget(del_btn)
        time_widget.setFixedWidth(100)
        current_container.addWidget(time_widget)
        self.schedule_time_widgets.append(time_widget)
        if len(self.schedule_time_widgets) == 1:
            del_btn.setEnabled(False)
            self.first_time_del_btn = del_btn
        elif len(self.schedule_time_widgets) > 1 and hasattr(self, 'first_time_del_btn'):
            self.first_time_del_btn.setEnabled(True)
        return time_widget

    def remove_time_widget(self, widget):
        """移除指定的时间选择组件，并重新整理布局"""
        if len(self.schedule_time_widgets) > 1:
            self.schedule_time_widgets.remove(widget)
            for container in self.time_container_layouts:
                for i in range(container.count()):
                    if container.itemAt(i).widget() == widget:
                        container.removeWidget(widget)
                        widget.deleteLater()
                        break
            self.reorganize_time_widgets()
            if len(self.schedule_time_widgets) == 1:
                last_widget = self.schedule_time_widgets[0]
                del_btn = last_widget.findChild(QPushButton)
                if del_btn:
                    del_btn.setEnabled(False)
                    self.first_time_del_btn = del_btn

    def reorganize_time_widgets(self):
        """清除所有旧容器后，重新按照每行最多4个组件组织时间组件"""
        for container in self.time_container_layouts:
            container_widget = container.parentWidget()
            self.time_rows_container.removeWidget(container_widget)
            container_widget.deleteLater()
        self.time_container_layouts = []
        current_container = self.add_new_time_container()
        for i, widget in enumerate(self.schedule_time_widgets):
            if i and i % 4 == 0:
                current_container = self.add_new_time_container()
            current_container.addWidget(widget)

    def fill_device_data(self):
        """将已有设备数据填充到表单中"""
        if not self.device_config:
            return
        # 填充基本信息
        self.name_edit.setText(self.device_config.device_name)
        self.adb_path_edit.setText(self.device_config.adb_config.adb_path)
        self.adb_address_edit.setText(self.device_config.adb_config.address)
        self.screenshot_method_edit.setText(str(self.device_config.adb_config.screencap_methods))
        self.input_method_edit.setText(str(self.device_config.adb_config.input_methods))
        import json
        config_str = json.dumps(self.device_config.adb_config.config)
        self.config_edit.setText(config_str)

        # 填充高级设置
        self.schedule_enabled.setChecked(self.device_config.schedule_enabled)
        self.toggle_schedule_widgets(self.device_config.schedule_enabled)

        # 清除已有的时间组件和容器
        if self.schedule_time_widgets:
            for widget in self.schedule_time_widgets:
                parent = widget.parentWidget().layout()
                parent.removeWidget(widget)
                widget.deleteLater()
            self.schedule_time_widgets.clear()
        for container in self.time_container_layouts:
            container_widget = container.parentWidget()
            self.time_rows_container.removeWidget(container_widget)
            container_widget.deleteLater()
        self.time_container_layouts = []
        self.add_new_time_container()

        # 添加已有的定时启动时间，若没有则添加一个默认
        if self.device_config.schedule_time:
            for time_str in self.device_config.schedule_time:
                parts = time_str.split(":")
                if len(parts) == 2:
                    time_widget = self.add_time_selection_widget()
                    time_edit = time_widget.findChild(QTimeEdit)
                    if time_edit:
                        time_edit.setTime(QTime(int(parts[0]), int(parts[1])))
        else:
            self.add_time_selection_widget()

        # 填充命令
        if hasattr(self.device_config, 'start_command'):
            self.pre_command_edit.setText(self.device_config.start_command)
        if hasattr(self.device_config, 'stop_command'):
            self.post_command_edit.setText(self.device_config.stop_command)

    def search_devices(self):
        self.search_btn.setEnabled(False)
        self.search_status.setText("正在搜索...")
        adb_path = self.adb_path_edit.text() or "adb"
        self.search_thread = DeviceSearchThread(adb_path)
        self.search_thread.devices_found.connect(self.on_devices_found)
        self.search_thread.search_error.connect(self.on_search_error)
        self.search_thread.finished.connect(self.on_search_completed)
        self.search_thread.start()

    def on_devices_found(self, devices):
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
        self.device_combo.clear()
        self.device_combo.addItem("搜索出错")
        self.search_status.setText(f"搜索出错: {error_msg}")

    def on_search_completed(self):
        self.search_btn.setEnabled(True)
        self.search_thread = None

    def device_selected(self, index):
        if 0 <= index < len(self.found_devices):
            device = self.found_devices[index]
            self.adb_address_edit.setText(device.address)
            self.adb_path_edit.setText(str(device.adb_path))
            self.screenshot_method_edit.setText(str(device.screencap_methods))
            self.input_method_edit.setText(str(device.input_methods))
            self.config_edit.setText(str(device.config))
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

            # 收集所有定时启动时间
            schedule_times = []
            for widget in self.schedule_time_widgets:
                time_edit = widget.findChild(QTimeEdit)
                if time_edit:
                    schedule_times.append(time_edit.time().toString("hh:mm"))

            if self.edit_mode and self.device_config:
                # 直接更新原有 DeviceConfig 的各项属性
                self.device_config.device_name = self.name_edit.text()
                self.device_config.adb_config.name = self.name_edit.text()
                self.device_config.adb_config.adb_path = self.adb_path_edit.text()
                self.device_config.adb_config.address = self.adb_address_edit.text()
                self.device_config.adb_config.screencap_methods = int(self.screenshot_method_edit.text())
                self.device_config.adb_config.input_methods = int(self.input_method_edit.text())
                self.device_config.adb_config.config = config_dict
                self.device_config.schedule_enabled = self.schedule_enabled.isChecked()
                self.device_config.schedule_time = schedule_times
                self.device_config.start_command = self.pre_command_edit.text()
                if hasattr(self.device_config, 'stop_command'):
                    self.device_config.stop_command = self.post_command_edit.text()
            else:
                new_config = DeviceConfig(
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
                    schedule_time=schedule_times,
                    start_command=self.pre_command_edit.text()
                )
                self.global_config.devices_config.devices.append(new_config)

            self.global_config.save_all_configs()
            self.accept()

        except Exception as e:
            print(f"保存设备时出错: {e}")

    def delete_device(self):
        """删除该设备"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除该设备吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                # 从全局配置中删除该设备，假设设备以 device_name 为唯一标识
                self.global_config.devices_config.devices = [
                    device for device in self.global_config.devices_config.devices
                    if device.device_name != self.device_config.device_name
                ]
                self.global_config.save_all_configs()
                self.accept()
            except Exception as e:
                print("删除设备时出错: ", e)
