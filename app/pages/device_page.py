from PySide6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTabWidget,
                               QSplitter, QTextEdit, QCheckBox, QWidget, QFormLayout,
                               QLineEdit, QComboBox, QGridLayout, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import os

from app.components import CollapsibleBox
from app.models.config.global_config import GlobalConfig
from app.models.config.device_config import DevicesConfig, DeviceConfig
from app.models.config.resource_config import ResourceConfig, SelectOption, BoolOption, InputOption


class DeviceCard(QFrame):
    """Custom widget to display device as a card"""

    def __init__(self, device_config, parent=None):
        super().__init__(parent)
        self.device_config = device_config
        self.parent_page = parent
        self.setObjectName("deviceCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumWidth(300)
        self.setMinimumHeight(150)
        self.setMaximumHeight(180)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Device name
        name_label = QLabel(self.device_config.device_name)
        name_label.setFont(QFont("Arial", 14, QFont.Bold))
        name_label.setObjectName("deviceCardName")
        layout.addWidget(name_label)

        # Device type
        type_label = QLabel(self.device_config.adb_config.name)
        type_label.setObjectName("deviceCardType")
        layout.addWidget(type_label)

        # Status with indicator
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 5)

        status_indicator = QLabel()
        status_indicator.setFixedSize(12, 12)

        # Determine status based on schedule_enabled
        status_text = "运行正常" if self.device_config.schedule_enabled else "未启用计划任务"
        status_label = QLabel(status_text)
        status_layout.addWidget(status_indicator)
        status_layout.addWidget(status_label)
        status_layout.addStretch()

        layout.addWidget(status_widget)

        # ADB address
        adb_address = QLabel(f"ADB地址: {self.device_config.adb_config.address}")
        layout.addWidget(adb_address)

        # Add spacer
        layout.addStretch()

        # Action button
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 5, 0, 0)

        view_btn = QPushButton("查看详情")
        view_btn.setObjectName("viewDetailBtn")
        view_btn.clicked.connect(lambda: self.parent_page.show_device_detail(self.device_config.device_name))

        button_layout.addStretch()
        button_layout.addWidget(view_btn)

        layout.addWidget(button_widget)


class DevicePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = GlobalConfig()
        self.init_ui()
        self.load_sample_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 大标题放在 QFrame 之外
        title_label = QLabel("设备信息")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        main_layout.addWidget(title_label)

        # 创建滚动区域，使用单个 QFrame 作为卡片容器
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        card_container = QFrame()  # 单一 QFrame 作为设备卡片容器
        card_container.setFrameShape(QFrame.StyledPanel)
        self.card_grid = QGridLayout(card_container)
        self.card_grid.setAlignment(Qt.AlignTop)
        self.card_grid.setContentsMargins(10, 10, 10, 10)
        self.card_grid.setSpacing(20)

        scroll_area.setWidget(card_container)
        main_layout.addWidget(scroll_area)

        # 设备详情区域（点击“查看详情”后显示）
        self.device_detail_widget = QWidget()
        self.device_detail_widget.hide()
        main_layout.addWidget(self.device_detail_widget)

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
        while self.card_grid.count():
            item = self.card_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            devices = self.global_config.get_devices_config().devices
            cols = 3
            for index, device in enumerate(devices):
                row = index // cols
                col = index % cols
                card = DeviceCard(device, self)
                self.card_grid.addWidget(card, row, col)
        except Exception as e:
            print(f"Error populating device cards: {e}")
            error_label = QLabel("无法加载设备配置")
            error_label.setAlignment(Qt.AlignCenter)
            self.card_grid.addWidget(error_label, 0, 0)

    def get_device_config(self, device_name):
        for device in self.global_config.get_devices_config().devices:
            if device.device_name == device_name:
                return device
        return None

    def show_device_detail(self, device_name):
        device_config = self.get_device_config(device_name)
        if not device_config:
            return

        if self.device_detail_widget.layout():
            QWidget().setLayout(self.device_detail_widget.layout())

        detail_layout = QVBoxLayout(self.device_detail_widget)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        back_btn = QPushButton("← 返回设备列表")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(lambda: self.device_detail_widget.hide())

        device_title = QLabel(f"设备详情: {device_name}")
        device_title.setFont(QFont("Arial", 14, QFont.Bold))
        device_title.setObjectName("deviceDetailTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(device_title)
        header_layout.addStretch()
        detail_layout.addWidget(header_widget)

        tab_widget = QTabWidget()
        tab_widget.setObjectName("detailTabs")

        # 基本信息 Tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_form = QFormLayout(info_frame)
        info_form.setContentsMargins(20, 20, 20, 20)
        info_form.setSpacing(15)

        info_items = [
            ("设备名称", device_config.device_name),
            ("设备类型", device_config.adb_config.name),
            ("ADB路径", device_config.adb_config.adb_path),
            ("ADB地址", device_config.adb_config.address),
            ("计划任务", "已启用" if device_config.schedule_enabled else "未启用"),
            ("启动命令", device_config.start_command or "无")
        ]
        for key, value in info_items:
            label = QLabel(key + ":")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            value_label = QLabel(value)
            info_form.addRow(label, value_label)

        info_layout.addWidget(info_frame)
        info_layout.addStretch()

        # 操作面板 Tab
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        splitter = QSplitter(Qt.Horizontal)

        resource_widget = QWidget()
        resource_layout = QVBoxLayout(resource_widget)
        resource_label = QLabel("资源选择")
        resource_label.setFont(QFont("Arial", 12, QFont.Bold))
        resource_label.setObjectName("resourceLabel")
        resource_layout.addWidget(resource_label)

        resources_container = QWidget()
        resources_layout = QVBoxLayout(resources_container)
        resources_layout.setContentsMargins(0, 0, 0, 0)
        resources_layout.setSpacing(10)

        configured_resources = device_config.resources
        for resource_config in configured_resources:
            resource_name = resource_config.resource_name
            full_resource_config = self.global_config.get_resource_config(resource_name)
            if not full_resource_config:
                continue

            resource_card = QFrame()
            resource_card.setObjectName("resourceCard")
            resource_card.setFrameShape(QFrame.StyledPanel)
            card_layout = QHBoxLayout(resource_card)

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            name_label = QLabel(resource_name)
            name_label.setFont(QFont("Arial", 11))
            task_count = QLabel(f"已选任务: {len(resource_config.selected_tasks)}")

            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)

            run_btn = QPushButton("运行")
            run_btn.setFixedWidth(60)
            settings_btn = QPushButton("设置")
            settings_btn.setFixedWidth(60)
            settings_btn.clicked.connect(
                lambda checked, r=resource_config, full_r=full_resource_config:
                self.show_resource_settings(r, full_r)
            )
            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)

            card_layout.addWidget(checkbox)
            card_layout.addWidget(name_label)
            card_layout.addWidget(task_count)
            card_layout.addStretch()
            card_layout.addWidget(button_widget)

            resources_layout.addWidget(resource_card)

        resource_layout.addWidget(resources_container)
        one_key_start_btn = QPushButton("一键启动")
        one_key_start_btn.setFixedHeight(40)
        one_key_start_btn.setObjectName("oneKeyButton")
        resource_layout.addWidget(one_key_start_btn)

        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)
        settings_label = QLabel("资源设置")
        settings_label.setFont(QFont("Arial", 12, QFont.Bold))
        settings_label.setObjectName("settingsLabel")
        self.settings_layout.addWidget(settings_label)
        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        self.settings_layout.addWidget(self.settings_content)

        splitter.addWidget(resource_widget)
        splitter.addWidget(self.settings_widget)
        splitter.setSizes([400, 600])
        control_layout.addWidget(splitter)

        # 日志面板 Tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setObjectName("logTextEdit")
        log_text.setText(f"""11:45:14
{device_name}
启动成功
19:19:10
{device_name} 运行正常, 这是一
长的日志信息, 用于测试SiLogItem组
动操行和显示效果。查看多行日志是
确显示和滚动。
00:00:00
{device_name}
检测到异常
""")
        log_layout.addWidget(log_text)

        tab_widget.addTab(info_tab, "基本信息")
        tab_widget.addTab(control_tab, "操作面板")
        tab_widget.addTab(log_tab, "日志面板")
        detail_layout.addWidget(tab_widget)

        self.device_detail_widget.show()

    def show_resource_settings(self, resource_config, full_resource_config):
        if self.settings_content.layout():
            QWidget().setLayout(self.settings_content.layout())

        content_layout = QVBoxLayout(self.settings_content)
        resource_name = QLabel(f"{resource_config.resource_name} 设置")
        resource_name.setFont(QFont("Arial", 12, QFont.Bold))
        resource_name.setObjectName("resourceSettingsTitle")
        content_layout.addWidget(resource_name)

        tasks_box = CollapsibleBox("任务选择")
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        for task in full_resource_config.resource_tasks:
            task_checkbox = QCheckBox(task.task_name)
            task_checkbox.setChecked(task.task_name in resource_config.selected_tasks)
            tasks_layout.addWidget(task_checkbox)
        tasks_box.add_widget(tasks_widget)
        content_layout.addWidget(tasks_box)

        options_box = CollapsibleBox("选项设置")
        options_widget = QWidget()
        options_layout = QFormLayout(options_widget)
        current_options = {opt.option_name: opt.value for opt in resource_config.options}
        for option in full_resource_config.options:
            label = QLabel(option.name)
            label.setFont(QFont("Arial", 10))
            if isinstance(option, SelectOption):
                widget = QComboBox()
                for choice in option.choices:
                    widget.addItem(choice.name, choice.value)
                if option.name in current_options:
                    index = widget.findData(current_options[option.name])
                    if index >= 0:
                        widget.setCurrentIndex(index)
                options_layout.addRow(label, widget)
            elif isinstance(option, BoolOption):
                widget = QCheckBox()
                widget.setChecked(current_options.get(option.name, option.default))
                options_layout.addRow(label, widget)
            elif isinstance(option, InputOption):
                widget = QLineEdit()
                widget.setText(str(current_options.get(option.name, option.default)))
                options_layout.addRow(label, widget)
        options_box.add_widget(options_widget)
        content_layout.addWidget(options_box)

        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("saveSettingsButton")
        content_layout.addWidget(save_btn)
        content_layout.addStretch()


