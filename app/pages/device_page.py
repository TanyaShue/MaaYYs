from PySide6.QtWidgets import (QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                               QHeaderView, QHBoxLayout, QPushButton, QTabWidget, QSplitter,
                               QTextEdit, QCheckBox, QWidget, QFormLayout, QLineEdit, QComboBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.components import CollapsibleBox
from app.models import Device, Resource


class DevicePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = Device.get_sample_devices()
        self.resources = Resource.get_sample_resources()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Add title
        title_label = QLabel("设备信息")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # Create a table to show all devices
        device_table = QTableWidget(len(self.devices), 5)
        device_table.setHorizontalHeaderLabels(["设备名称", "类型", "状态", "上次启动", "操作"])
        device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        device_table.verticalHeader().setVisible(False)
        device_table.setSelectionBehavior(QTableWidget.SelectRows)
        device_table.setObjectName("deviceTable")

        for row, device in enumerate(self.devices):
            device_table.setItem(row, 0, QTableWidgetItem(device.name))
            device_table.setItem(row, 1, QTableWidgetItem(device.device_type))

            # Add status with colored indicator
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(5, 2, 5, 2)

            status_indicator = QLabel()
            status_indicator.setFixedSize(10, 10)
            status_indicator.setObjectName("statusIndicator" + ("Normal" if device.status == "运行正常" else "Error"))

            status_text = QLabel(device.status)
            status_text.setObjectName("statusText")

            status_layout.addWidget(status_indicator)
            status_layout.addWidget(status_text)
            status_layout.addStretch()

            device_table.setCellWidget(row, 2, status_widget)

            # Last start time
            device_table.setItem(row, 3, QTableWidgetItem(device.last_start))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)

            view_btn = QPushButton("查看")
            view_btn.clicked.connect(lambda checked, name=device.name: self.show_device_detail(name))

            action_layout.addWidget(view_btn)
            action_layout.addStretch()

            device_table.setCellWidget(row, 4, action_widget)

        layout.addWidget(device_table)

        # Add a device detail section - will be shown when "查看" is clicked
        self.device_detail_widget = QWidget()
        self.device_detail_widget.hide()

        layout.addWidget(self.device_detail_widget)

    def show_device_detail(self, device_name):
        # Clear existing content in device detail widget
        if self.device_detail_widget.layout():
            QWidget().setLayout(self.device_detail_widget.layout())

        # Create new layout
        detail_layout = QVBoxLayout(self.device_detail_widget)

        # Device title
        device_title = QLabel(f"设备详情: {device_name}")
        device_title.setFont(QFont("Arial", 14, QFont.Bold))
        device_title.setObjectName("deviceDetailTitle")
        detail_layout.addWidget(device_title)

        # Create tabs
        tab_widget = QTabWidget()
        tab_widget.setObjectName("detailTabs")

        # Info tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        info_table = QTableWidget(5, 2)
        info_table.setHorizontalHeaderLabels(["属性", "值"])
        info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        info_table.verticalHeader().setVisible(False)
        info_table.setObjectName("infoTable")

        info_items = [
            ("设备名称", device_name),
            ("设备类型", "模拟器"),
            ("状态", "运行正常"),
            ("上次启动时间", "2025-02-26 11:45:14"),
            ("启动次数", "42")
        ]

        for row, (key, value) in enumerate(info_items):
            info_table.setItem(row, 0, QTableWidgetItem(key))
            info_table.setItem(row, 1, QTableWidgetItem(value))

        info_layout.addWidget(info_table)

        # Control tab with splitter
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)

        # Create a splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left side - resource selection
        resource_widget = QWidget()
        resource_layout = QVBoxLayout(resource_widget)

        resource_label = QLabel("资源选择")
        resource_label.setFont(QFont("Arial", 12, QFont.Bold))
        resource_label.setObjectName("resourceLabel")
        resource_layout.addWidget(resource_label)

        # Resource table with checkboxes
        resource_table = QTableWidget(len(self.resources), 3)
        resource_table.setHorizontalHeaderLabels(["启用", "资源名称", "操作"])
        resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        resource_table.verticalHeader().setVisible(False)
        resource_table.setObjectName("resourceTable")

        for row, resource in enumerate(self.resources):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(resource.enabled)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(5, 2, 5, 2)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            resource_table.setCellWidget(row, 0, checkbox_widget)

            # Resource name
            resource_table.setItem(row, 1, QTableWidgetItem(resource.name))

            # Buttons
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)

            run_btn = QPushButton("运行")

            settings_btn = QPushButton("设置")
            settings_btn.clicked.connect(lambda checked, r=resource: self.show_resource_settings(r))

            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)

            resource_table.setCellWidget(row, 2, button_widget)

        resource_layout.addWidget(resource_table)

        one_key_start_btn = QPushButton("一键启动")
        one_key_start_btn.setFixedHeight(40)
        one_key_start_btn.setObjectName("oneKeyButton")
        resource_layout.addWidget(one_key_start_btn)

        # Right side - settings panel (initially empty)
        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)

        settings_label = QLabel("资源设置")
        settings_label.setFont(QFont("Arial", 12, QFont.Bold))
        settings_label.setObjectName("settingsLabel")
        self.settings_layout.addWidget(settings_label)

        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        self.settings_layout.addWidget(self.settings_content)

        # Add widgets to splitter
        splitter.addWidget(resource_widget)
        splitter.addWidget(self.settings_widget)

        # Set initial sizes
        splitter.setSizes([400, 600])

        control_layout.addWidget(splitter)

        # Log tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setObjectName("logTextEdit")
        log_text.setText("""11:45:14
雷电模拟器-阴阳师1
启动成功
19:19:10
雷电模拟器-阴阳师1 运行正常, 这是一
长的日志信息, 用于测试SiLogItem组
动操行和显示效果。查看多行日志是
确显示和滚动。
00:00:00
雷电模拟器-阴阳师1
检测到异常
""")

        log_layout.addWidget(log_text)

        # Add tabs to widget
        tab_widget.addTab(info_tab, "基本信息")
        tab_widget.addTab(control_tab, "操作面板")
        tab_widget.addTab(log_tab, "日志面板")

        detail_layout.addWidget(tab_widget)

        # Show the widget
        self.device_detail_widget.show()

    def show_resource_settings(self, resource):
        # Clear existing settings content
        if self.settings_content.layout():
            QWidget().setLayout(self.settings_content.layout())

        # Create new layout
        content_layout = QVBoxLayout(self.settings_content)

        # Resource name
        resource_name = QLabel(f"{resource.name} 设置")
        resource_name.setFont(QFont("Arial", 12, QFont.Bold))
        resource_name.setObjectName("resourceSettingsTitle")
        content_layout.addWidget(resource_name)

        # Create collapsible boxes for each setting group
        for group in resource.settings:
            collapsible = CollapsibleBox(group.name)

            # Create form for settings
            form_widget = QWidget()
            form_layout = QFormLayout(form_widget)

            for setting in group.settings:
                if setting.type == "checkbox":
                    widget = QCheckBox()
                    widget.setChecked(setting.value)
                    form_layout.addRow(setting.name, widget)

                elif setting.type == "combobox":
                    widget = QComboBox()
                    widget.addItems(setting.options)
                    widget.setCurrentText(setting.value)
                    form_layout.addRow(setting.name, widget)

                elif setting.type == "input":
                    widget = QLineEdit(setting.value)
                    form_layout.addRow(setting.name, widget)

            collapsible.add_widget(form_widget)
            content_layout.addWidget(collapsible)

        # Add save button
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("saveSettingsButton")
        content_layout.addWidget(save_btn)

        # Add stretch to push everything to the top
        content_layout.addStretch()