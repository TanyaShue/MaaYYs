import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea,
                               QGridLayout, QSpacerItem, QSizePolicy, QTabWidget,
                               QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
                               QCheckBox, QComboBox, QLineEdit, QGroupBox, QFormLayout,
                               QSplitter)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont


class DeviceCard(QFrame):
    def __init__(self, device_name, device_type, status):
        super().__init__()
        self.setObjectName("deviceCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            #deviceCard {
                background-color: #2d2d30;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)

        layout = QVBoxLayout(self)

        # Device name label
        name_label = QLabel(device_name)
        name_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)

        # Device type label
        type_label = QLabel(device_type)
        type_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        layout.addWidget(type_label)

        # Status indicator
        status_color = "#4CAF50" if status == "运行正常" else "#F44336"
        status_layout = QHBoxLayout()
        status_indicator = QLabel()
        status_indicator.setFixedSize(10, 10)
        status_indicator.setStyleSheet(f"background-color: {status_color}; border-radius: 5px;")
        status_text = QLabel(status)
        status_text.setStyleSheet("color: #cccccc; font-size: 12px;")

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


class CollapsibleBox(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)

        self.toggle_button = QCheckBox(title)
        self.toggle_button.setStyleSheet("QCheckBox { font-weight: bold; }")

        self.toggle_button.stateChanged.connect(self.on_toggle)

        self.content_area = QWidget()
        self.content_area.setVisible(False)

        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 0, 0, 0)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_area)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def on_toggle(self, state):
        self.content_area.setVisible(state == Qt.Checked)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)


class NavigationButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(50)
        self.setCheckable(True)

        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))

        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 0;
                text-align: left;
                padding-left: 15px;
                color: #cccccc;
                background-color: #1e1e1e;
            }
            QPushButton:checked {
                background-color: #2d2d30;
                border-left: 4px solid #007acc;
                color: white;
            }
            QPushButton:hover {
                background-color: #333337;
            }
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设备管理系统")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #333337;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
            }
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QTableWidget {
                background-color: #252526;
                color: white;
                gridline-color: #3e3e42;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #333337;
                color: white;
                padding: 5px;
                border: none;
            }
            QTabWidget::pane {
                border: none;
                background-color: #252526;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 8px 12px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #252526;
                color: white;
            }
            QTextEdit {
                background-color: #252526;
                color: white;
                border: none;
            }
            QCheckBox {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QLineEdit {
                background-color: #333337;
                color: white;
                border: 1px solid #3e3e42;
                border-radius: 2px;
                padding: 4px;
            }
            QComboBox {
                background-color: #333337;
                color: white;
                border: 1px solid #3e3e42;
                border-radius: 2px;
                padding: 4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #3e3e42;
                border-left-style: solid;
            }
            QSplitter::handle {
                background-color: #3e3e42;
            }
            QSplitter::handle:horizontal {
                width: 1px;
            }
        """)

        # Create central widget
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)

        # Create navigation sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #1e1e1e;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        # Add navigation buttons
        self.home_btn = NavigationButton("首页", "icons/home.png")
        self.device_btn = NavigationButton("设备信息", "icons/device.png")
        self.download_btn = NavigationButton("资源下载", "icons/download.png")

        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.device_btn)
        sidebar_layout.addWidget(self.download_btn)
        sidebar_layout.addStretch()

        # Add bottom info button
        self.info_btn = NavigationButton("软件信息", "icons/info.png")
        sidebar_layout.addWidget(self.info_btn)

        main_layout.addWidget(sidebar)

        # Create stacked content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)

        main_layout.addWidget(self.content_widget)

        # Initialize device data
        self.devices = [
            {"name": "雷电模拟器-阴阳师1", "type": "模拟器", "status": "运行正常"},
            {"name": "夜神模拟器-战双", "type": "模拟器", "status": "运行正常"},
            {"name": "雷电模拟器-原神", "type": "模拟器", "status": "检测到异常"},
            {"name": "MuMu模拟器-明日方舟", "type": "模拟器", "status": "运行正常"},
            {"name": "BlueStacks-FGO", "type": "模拟器", "status": "运行正常"},
            {"name": "雷电模拟器-碧蓝航线", "type": "模拟器", "status": "检测到异常"}
        ]

        self.resources = [
            {"name": "战双软件件", "enabled": True, "settings": [
                {"name": "基本设置", "settings": [
                    {"type": "checkbox", "name": "启用自动战斗", "value": True},
                    {"type": "combobox", "name": "战斗难度", "value": "普通", "options": ["简单", "普通", "困难"]}
                ]},
                {"name": "高级设置", "settings": [
                    {"type": "input", "name": "每日战斗次数", "value": "10"},
                    {"type": "checkbox", "name": "自动使用体力药", "value": False}
                ]}
            ]},
            {"name": "阴阳师", "enabled": True, "settings": [
                {"name": "基本设置", "settings": [
                    {"type": "checkbox", "name": "自动接受邀请", "value": True},
                    {"type": "combobox", "name": "副本选择", "value": "御魂", "options": ["御魂", "觉醒", "探索"]}
                ]},
                {"name": "高级设置", "settings": [
                    {"type": "input", "name": "运行时间(分钟)", "value": "60"},
                    {"type": "checkbox", "name": "自动接收礼物", "value": True}
                ]}
            ]}
        ]

        # Connect navigation buttons
        self.home_btn.setChecked(True)
        self.home_btn.clicked.connect(lambda: self.show_page("home"))
        self.device_btn.clicked.connect(lambda: self.show_page("device"))
        self.download_btn.clicked.connect(lambda: self.show_page("download"))
        self.info_btn.clicked.connect(lambda: self.show_page("info"))

        # Initialize with home page
        self.show_page("home")

    def create_home_page(self):
        # Clear existing content
        self.clear_content()

        # Add title
        title_label = QLabel("设备管理系统")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.content_layout.addWidget(title_label)

        # Add devices section label
        devices_label = QLabel("设备信息")
        devices_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.content_layout.addWidget(devices_label)

        # Create scroll area for devices
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)

        # Add device cards to grid
        row, col = 0, 0
        max_col = 3

        for device in self.devices:
            device_card = DeviceCard(device["name"], device["type"], device["status"])
            grid_layout.addWidget(device_card, row, col)

            col += 1
            if col >= max_col:
                col = 0
                row += 1

        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

    def create_device_page(self):
        # Clear existing content
        self.clear_content()

        # Add title
        title_label = QLabel("设备信息")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.content_layout.addWidget(title_label)

        # Create a table to show all devices
        device_table = QTableWidget(len(self.devices), 5)
        device_table.setHorizontalHeaderLabels(["设备名称", "类型", "状态", "上次启动", "操作"])
        device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        device_table.verticalHeader().setVisible(False)
        device_table.setSelectionBehavior(QTableWidget.SelectRows)

        for row, device in enumerate(self.devices):
            device_table.setItem(row, 0, QTableWidgetItem(device["name"]))
            device_table.setItem(row, 1, QTableWidgetItem(device["type"]))

            # Add status with colored indicator
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(5, 2, 5, 2)

            status_color = "#4CAF50" if device["status"] == "运行正常" else "#F44336"
            status_indicator = QLabel()
            status_indicator.setFixedSize(10, 10)
            status_indicator.setStyleSheet(f"background-color: {status_color}; border-radius: 5px;")

            status_text = QLabel(device["status"])

            status_layout.addWidget(status_indicator)
            status_layout.addWidget(status_text)
            status_layout.addStretch()

            device_table.setCellWidget(row, 2, status_widget)

            # Last start time (placeholder)
            device_table.setItem(row, 3, QTableWidgetItem("2025-02-26 11:45:14"))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 2, 5, 2)

            view_btn = QPushButton("查看")
            view_btn.clicked.connect(lambda checked, name=device["name"]: self.show_device_detail(name))

            action_layout.addWidget(view_btn)
            action_layout.addStretch()

            device_table.setCellWidget(row, 4, action_widget)

        self.content_layout.addWidget(device_table)

        # Add a device detail section - will be shown when "查看" is clicked
        self.device_detail_widget = QWidget()
        self.device_detail_widget.hide()

        self.content_layout.addWidget(self.device_detail_widget)

    def show_device_detail(self, device_name):
        # Clear existing content in device detail widget
        if self.device_detail_widget.layout():
            QWidget().setLayout(self.device_detail_widget.layout())

        # Create new layout
        detail_layout = QVBoxLayout(self.device_detail_widget)

        # Device title
        device_title = QLabel(f"设备详情: {device_name}")
        device_title.setFont(QFont("Arial", 14, QFont.Bold))
        detail_layout.addWidget(device_title)

        # Create tabs
        tab_widget = QTabWidget()

        # Info tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        info_table = QTableWidget(5, 2)
        info_table.setHorizontalHeaderLabels(["属性", "值"])
        info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        info_table.verticalHeader().setVisible(False)

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
        resource_layout.addWidget(resource_label)

        # Resource table with checkboxes
        resource_table = QTableWidget(len(self.resources), 3)
        resource_table.setHorizontalHeaderLabels(["启用", "资源名称", "操作"])
        resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        resource_table.verticalHeader().setVisible(False)

        for row, resource in enumerate(self.resources):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(resource["enabled"])
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(5, 2, 5, 2)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            resource_table.setCellWidget(row, 0, checkbox_widget)

            # Resource name
            resource_table.setItem(row, 1, QTableWidgetItem(resource["name"]))

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
        resource_layout.addWidget(one_key_start_btn)

        # Right side - settings panel (initially empty)
        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)

        settings_label = QLabel("资源设置")
        settings_label.setFont(QFont("Arial", 12, QFont.Bold))
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
        resource_name = QLabel(f"{resource['name']} 设置")
        resource_name.setFont(QFont("Arial", 12, QFont.Bold))
        content_layout.addWidget(resource_name)

        # Create collapsible boxes for each setting group
        for group in resource["settings"]:
            collapsible = CollapsibleBox(group["name"])

            # Create form for settings
            form_widget = QWidget()
            form_layout = QFormLayout(form_widget)

            for setting in group["settings"]:
                if setting["type"] == "checkbox":
                    widget = QCheckBox()
                    widget.setChecked(setting["value"])
                    form_layout.addRow(setting["name"], widget)

                elif setting["type"] == "combobox":
                    widget = QComboBox()
                    widget.addItems(setting["options"])
                    widget.setCurrentText(setting["value"])
                    form_layout.addRow(setting["name"], widget)

                elif setting["type"] == "input":
                    widget = QLineEdit(setting["value"])
                    form_layout.addRow(setting["name"], widget)

            collapsible.add_widget(form_widget)
            content_layout.addWidget(collapsible)

        # Add save button
        save_btn = QPushButton("保存设置")
        content_layout.addWidget(save_btn)

        # Add stretch to push everything to the top
        content_layout.addStretch()

    def create_download_page(self):
        # Clear existing content
        self.clear_content()

        # Add title
        title_label = QLabel("资源下载")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.content_layout.addWidget(title_label)

        # Create download frame
        download_frame = QFrame()
        download_frame.setFrameShape(QFrame.StyledPanel)
        download_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        download_layout = QVBoxLayout(download_frame)

        # Resources table
        resources_label = QLabel("可用资源")
        resources_label.setFont(QFont("Arial", 14, QFont.Bold))
        download_layout.addWidget(resources_label)

        resources_table = QTableWidget(6, 4)
        resources_table.setHorizontalHeaderLabels(["资源名称", "版本", "大小", "操作"])
        resources_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        resources_table.verticalHeader().setVisible(False)

        resources = [
            ("雷电模拟器", "9.0.33", "500MB", "下载"),
            ("夜神模拟器", "7.0.5", "450MB", "下载"),
            ("MuMu模拟器", "12.0", "600MB", "下载"),
            ("阴阳师", "3.5.0", "2.1GB", "下载"),
            ("战双", "2.7.0", "3.5GB", "下载"),
            ("原神", "4.0.0", "15GB", "下载")
        ]

        for row, (name, version, size, action) in enumerate(resources):
            resources_table.setItem(row, 0, QTableWidgetItem(name))
            resources_table.setItem(row, 1, QTableWidgetItem(version))
            resources_table.setItem(row, 2, QTableWidgetItem(size))

            download_btn = QPushButton(action)
            resources_table.setCellWidget(row, 3, download_btn)

        download_layout.addWidget(resources_table)

        # Download queue
        queue_label = QLabel("下载队列")
        queue_label.setFont(QFont("Arial", 14, QFont.Bold))
        download_layout.addWidget(queue_label)

        queue_table = QTableWidget(2, 4)
        queue_table.setHorizontalHeaderLabels(["资源名称", "进度", "速度", "操作"])
        queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        queue_table.verticalHeader().setVisible(False)

        queue_items = [
            ("原神", "45%", "5.2MB/s", "暂停"),
            ("阴阳师", "12%", "3.8MB/s", "暂停")
        ]

        for row, (name, progress, speed, action) in enumerate(queue_items):
            queue_table.setItem(row, 0, QTableWidgetItem(name))
            queue_table.setItem(row, 1, QTableWidgetItem(progress))
            queue_table.setItem(row, 2, QTableWidgetItem(speed))

            action_btn = QPushButton(action)
            queue_table.setCellWidget(row, 3, action_btn)

        download_layout.addWidget(queue_table)

        # Add to main layout
        self.content_layout.addWidget(download_frame)

    def create_info_page(self):
        # Clear existing content
        self.clear_content()

        # Add title
        title_label = QLabel("软件信息")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.content_layout.addWidget(title_label)

        # Create info frame
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        info_layout = QVBoxLayout(info_frame)

        # Software title
        software_title = QLabel("设备管理系统")
        software_title.setFont(QFont("Arial", 20, QFont.Bold))
        software_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(software_title)

        # Version
        version_label = QLabel("版本: 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(version_label)

        # Description
        description_text = QTextEdit()
        description_text.setReadOnly(True)
        description_text.setStyleSheet("QTextEdit { border: none; }")
        description_text.setText("""设备管理系统是一款专为模拟器和游戏管理设计的工具软件。

主要功能:
• 一键管理多个模拟器实例
• 监控模拟器运行状态
• 便捷启动游戏资源
• 自动检测异常情况
• 资源下载与更新

该软件基于PySide6开发，支持Windows 10/11系统。""")

        info_layout.addWidget(description_text)

        # Developer info
        developer_label = QLabel("开发: Example Development Team")
        developer_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(developer_label)

        # Copyright
        copyright_label = QLabel("© 2025 版权所有")
        copyright_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(copyright_label)

        # Add to main layout
        self.content_layout.addWidget(info_frame)

    def clear_content(self):
        # Clear all widgets from content layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def show_page(self, page_name):
        # Update navigation button states
        self.home_btn.setChecked(page_name == "home")
        self.device_btn.setChecked(page_name == "device")
        self.download_btn.setChecked(page_name == "download")
        self.info_btn.setChecked(page_name == "info")

        # Show requested page
        if page_name == "home":
            self.create_home_page()
        elif page_name == "device":
            self.create_device_page()
        elif page_name == "download":
            self.create_download_page()
        elif page_name == "info":
            self.create_info_page()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())