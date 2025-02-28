from PySide6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTabWidget,
                               QSplitter, QTextEdit, QCheckBox, QWidget, QFormLayout,
                               QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.models.config.global_config import GlobalConfig
from app.models.config.resource_config import ResourceConfig, SelectOption, BoolOption, InputOption


class DevicePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = GlobalConfig()
        self.init_ui()
        self.load_sample_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 页面标题
        title_label = QLabel("设备信息")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # 设备信息面板（使用框架包装，提升视觉层次）
        self.devices_frame = QFrame()
        self.devices_frame.setFrameShape(QFrame.StyledPanel)
        self.devices_frame.setObjectName("devicesFrame")
        devices_layout = QVBoxLayout(self.devices_frame)
        devices_layout.setContentsMargins(15, 15, 15, 15)

        # 设备列表标题
        devices_label = QLabel("设备列表")
        devices_label.setFont(QFont("Arial", 14, QFont.Bold))
        devices_label.setObjectName("sectionTitle")
        devices_layout.addWidget(devices_label)

        # 设备表格
        self.device_table = QTableWidget()
        self.device_table.setObjectName("deviceTable")
        self.device_table.setColumnCount(6)
        self.device_table.setHorizontalHeaderLabels(["设备名称", "类型", "状态", "ADB地址", "计划任务", "操作"])
        self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.device_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.device_table.setAlternatingRowColors(True)
        devices_layout.addWidget(self.device_table)

        layout.addWidget(self.devices_frame)

        # 设备详情区域（使用框架包装，提升视觉层次）
        self.device_detail_frame = QFrame()
        self.device_detail_frame.setFrameShape(QFrame.StyledPanel)
        self.device_detail_frame.setObjectName("deviceDetailFrame")
        self.device_detail_frame.hide()

        self.device_detail_layout = QVBoxLayout(self.device_detail_frame)
        self.device_detail_layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(self.device_detail_frame)

    def load_sample_data(self):
        try:
            devices_config_path = "assets/config/devices.json"
            self.global_config.load_devices_config(devices_config_path)

            resource_dir = "assets/resource"
            self.global_config.load_all_resources_from_directory(resource_dir)

            self.populate_device_table()
        except Exception as e:
            print(f"Error loading config files: {e}")

    def populate_device_table(self):
        # 清空现有表格内容
        self.device_table.clearContents()
        self.device_table.setRowCount(0)

        try:
            devices = self.global_config.get_devices_config().devices
            self.device_table.setRowCount(len(devices))

            for row, device in enumerate(devices):
                # 设备名称
                self.device_table.setItem(row, 0, QTableWidgetItem(device.device_name))

                # 设备类型
                self.device_table.setItem(row, 1, QTableWidgetItem(device.adb_config.name))

                # 状态（带颜色指示器）
                status_widget = QWidget()
                status_layout = QHBoxLayout(status_widget)
                status_layout.setContentsMargins(5, 2, 5, 2)

                status_text = "运行正常" if device.schedule_enabled else "未启用计划任务"
                status_color = "#4CAF50" if device.schedule_enabled else "#F44336"

                status_indicator = QLabel()
                status_indicator.setFixedSize(10, 10)
                status_indicator.setStyleSheet(f"background-color: {status_color}; border-radius: 5px;")

                status_label = QLabel(status_text)

                status_layout.addWidget(status_indicator)
                status_layout.addWidget(status_label)
                status_layout.addStretch()

                self.device_table.setCellWidget(row, 2, status_widget)

                # ADB地址
                self.device_table.setItem(row, 3, QTableWidgetItem(device.adb_config.address))

                # 计划任务
                plan_status = "已启用" if device.schedule_enabled else "未启用"
                self.device_table.setItem(row, 4, QTableWidgetItem(plan_status))

                # 操作按钮
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 2, 5, 2)

                view_btn = QPushButton("查看")
                view_btn.setObjectName("viewButton")
                view_btn.setFixedWidth(80)
                view_btn.clicked.connect(lambda checked, name=device.device_name: self.show_device_detail(name))

                action_layout.addWidget(view_btn)
                action_layout.addStretch()

                self.device_table.setCellWidget(row, 5, action_widget)

            # 调整行高
            for row in range(self.device_table.rowCount()):
                self.device_table.setRowHeight(row, 40)

        except Exception as e:
            print(f"Error populating device table: {e}")

    def get_device_config(self, device_name):
        for device in self.global_config.get_devices_config().devices:
            if device.device_name == device_name:
                return device
        return None

    def show_device_detail(self, device_name):
        device_config = self.get_device_config(device_name)
        if not device_config:
            return

        # 清除现有内容
        if self.device_detail_layout.count() > 0:
            for i in reversed(range(self.device_detail_layout.count())):
                item = self.device_detail_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()

        # 设备标题和返回按钮
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        back_btn = QPushButton("← 返回设备列表")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.hide_device_detail)

        device_title = QLabel(f"设备详情: {device_name}")
        device_title.setFont(QFont("Arial", 14, QFont.Bold))
        device_title.setObjectName("deviceDetailTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(device_title)
        header_layout.addStretch()
        self.device_detail_layout.addWidget(header_widget)

        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setObjectName("detailTabs")

        # 基本信息 Tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_layout.setContentsMargins(15, 15, 15, 15)

        # 基本信息标题
        info_title = QLabel("基本信息")
        info_title.setFont(QFont("Arial", 12, QFont.Bold))
        info_title.setObjectName("sectionTitle")
        info_layout.addWidget(info_title)

        # 基本信息表格
        info_table = QTableWidget(6, 2)
        info_table.setObjectName("infoTable")
        info_table.setHorizontalHeaderLabels(["属性", "值"])
        info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        info_table.verticalHeader().setVisible(False)
        info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        info_table.setAlternatingRowColors(True)
        info_table.setFrameShape(QFrame.NoFrame)

        info_items = [
            ("设备名称", device_config.device_name),
            ("设备类型", device_config.adb_config.name),
            ("ADB路径", device_config.adb_config.adb_path),
            ("ADB地址", device_config.adb_config.address),
            ("计划任务", "已启用" if device_config.schedule_enabled else "未启用"),
            ("启动命令", device_config.start_command or "无")
        ]

        for row, (key, value) in enumerate(info_items):
            info_table.setItem(row, 0, QTableWidgetItem(key))
            info_table.setItem(row, 1, QTableWidgetItem(value))
            info_table.setRowHeight(row, 35)

        info_layout.addWidget(info_table)
        info_layout.addStretch()

        # 操作面板 Tab（使用分隔器）
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        control_layout.setContentsMargins(15, 15, 15, 15)

        # 创建分隔器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("controlSplitter")

        # 左侧 - 资源选择
        resource_widget = QWidget()
        resource_layout = QVBoxLayout(resource_widget)
        resource_layout.setContentsMargins(0, 0, 10, 0)

        resource_label = QLabel("资源选择")
        resource_label.setFont(QFont("Arial", 12, QFont.Bold))
        resource_label.setObjectName("sectionTitle")
        resource_layout.addWidget(resource_label)

        # 资源表格（带复选框）
        configured_resources = device_config.resources
        resource_table = QTableWidget(len(configured_resources), 3)
        resource_table.setObjectName("resourceTable")
        resource_table.setHorizontalHeaderLabels(["启用", "资源名称", "操作"])
        resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        resource_table.verticalHeader().setVisible(False)
        resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        resource_table.setAlternatingRowColors(True)
        resource_table.setFrameShape(QFrame.NoFrame)

        for row, resource_config in enumerate(configured_resources):
            resource_name = resource_config.resource_name
            full_resource_config = self.global_config.get_resource_config(resource_name)
            if not full_resource_config:
                continue

            # 复选框
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(5, 2, 5, 2)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            resource_table.setCellWidget(row, 0, checkbox_widget)

            # 资源名称（包含已选任务数）
            name_item = QTableWidgetItem(f"{resource_name} (已选任务: {len(resource_config.selected_tasks)})")
            resource_table.setItem(row, 1, name_item)

            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)

            run_btn = QPushButton("运行")
            run_btn.setFixedWidth(60)
            run_btn.setObjectName("runButton")

            settings_btn = QPushButton("设置")
            settings_btn.setFixedWidth(60)
            settings_btn.setObjectName("settingsButton")
            settings_btn.clicked.connect(
                lambda checked, r=resource_config, full_r=full_resource_config:
                self.show_resource_settings(r, full_r)
            )

            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)

            resource_table.setCellWidget(row, 2, button_widget)
            resource_table.setRowHeight(row, 35)

        resource_layout.addWidget(resource_table)

        one_key_start_btn = QPushButton("一键启动")
        one_key_start_btn.setFixedHeight(40)
        one_key_start_btn.setObjectName("oneKeyButton")
        resource_layout.addWidget(one_key_start_btn)

        # 右侧 - 设置面板（初始为空）
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_frame.setObjectName("settingsFrame")
        self.settings_layout = QVBoxLayout(settings_frame)
        self.settings_layout.setContentsMargins(15, 15, 15, 15)

        settings_label = QLabel("资源设置")
        settings_label.setFont(QFont("Arial", 12, QFont.Bold))
        settings_label.setObjectName("sectionTitle")
        self.settings_layout.addWidget(settings_label)

        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        self.settings_layout.addWidget(self.settings_content)
        self.settings_layout.addStretch()

        # 将两部分添加到分隔器
        splitter.addWidget(resource_widget)
        splitter.addWidget(settings_frame)

        # 设置初始大小
        splitter.setSizes([400, 600])

        control_layout.addWidget(splitter)

        # 日志 Tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(15, 15, 15, 15)

        log_label = QLabel("设备日志")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        log_label.setObjectName("sectionTitle")
        log_layout.addWidget(log_label)

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

        # 添加选项卡到控件
        tab_widget.addTab(info_tab, "基本信息")
        tab_widget.addTab(control_tab, "操作面板")
        tab_widget.addTab(log_tab, "日志面板")

        self.device_detail_layout.addWidget(tab_widget)

        # 显示设备详情框架，隐藏设备列表框架
        self.devices_frame.hide()
        self.device_detail_frame.show()

    def hide_device_detail(self):
        # 隐藏设备详情，显示设备列表
        self.device_detail_frame.hide()
        self.devices_frame.show()

    def show_resource_settings(self, resource_config, full_resource_config):
        # 清除现有设置内容
        if self.settings_content.layout():
            QWidget().setLayout(self.settings_content.layout())

        # 创建新布局
        content_layout = QVBoxLayout(self.settings_content)

        # 资源名称
        resource_name = QLabel(f"{resource_config.resource_name} 设置")
        resource_name.setFont(QFont("Arial", 12, QFont.Bold))
        resource_name.setObjectName("resourceSettingsTitle")
        content_layout.addWidget(resource_name)

        # 为每个设置组创建可折叠框
        # 任务选择
        tasks_frame = QFrame()
        tasks_frame.setFrameShape(QFrame.StyledPanel)
        tasks_frame.setObjectName("tasksFrame")
        tasks_layout = QVBoxLayout(tasks_frame)

        tasks_title = QLabel("任务选择")
        tasks_title.setFont(QFont("Arial", 11, QFont.Bold))
        tasks_layout.addWidget(tasks_title)

        tasks_widget = QWidget()
        tasks_inner_layout = QVBoxLayout(tasks_widget)
        for task in full_resource_config.resource_tasks:
            task_checkbox = QCheckBox(task.task_name)
            task_checkbox.setChecked(task.task_name in resource_config.selected_tasks)
            tasks_inner_layout.addWidget(task_checkbox)
        tasks_layout.addWidget(tasks_widget)
        content_layout.addWidget(tasks_frame)

        # 选项设置
        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.StyledPanel)
        options_frame.setObjectName("optionsFrame")
        options_layout = QVBoxLayout(options_frame)

        options_title = QLabel("选项设置")
        options_title.setFont(QFont("Arial", 11, QFont.Bold))
        options_layout.addWidget(options_title)

        options_widget = QWidget()
        options_form_layout = QFormLayout(options_widget)
        options_form_layout.setVerticalSpacing(10)

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
                options_form_layout.addRow(label, widget)
            elif isinstance(option, BoolOption):
                widget = QCheckBox()
                widget.setChecked(current_options.get(option.name, option.default))
                options_form_layout.addRow(label, widget)
            elif isinstance(option, InputOption):
                widget = QLineEdit()
                widget.setText(str(current_options.get(option.name, option.default)))
                options_form_layout.addRow(label, widget)
        options_layout.addWidget(options_widget)
        content_layout.addWidget(options_frame)

        # 添加保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("saveSettingsButton")
        save_btn.setFixedHeight(40)
        content_layout.addWidget(save_btn)

        # 添加拉伸以将所有内容推到顶部
        content_layout.addStretch()