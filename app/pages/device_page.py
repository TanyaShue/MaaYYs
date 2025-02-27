from PySide6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTabWidget,
                               QSplitter, QTextEdit, QCheckBox, QWidget, QFormLayout,
                               QLineEdit, QComboBox, QGridLayout, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from app.components import CollapsibleBox
from app.models import Device, Resource


class DeviceCard(QFrame):
    """Custom widget to display device as a card"""

    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.device = device
        self.parent_page = parent
        self.setObjectName("deviceCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumWidth(300)
        self.setMinimumHeight(180)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Device name
        name_label = QLabel(self.device.name)
        name_label.setFont(QFont("Arial", 14, QFont.Bold))
        name_label.setObjectName("deviceCardName")
        layout.addWidget(name_label)

        # Device type
        type_label = QLabel(self.device.device_type)
        type_label.setObjectName("deviceCardType")
        layout.addWidget(type_label)

        # Status with indicator
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 5)

        status_indicator = QLabel()
        status_indicator.setFixedSize(12, 12)

        status_text = QLabel(self.device.status)
        status_layout.addWidget(status_indicator)
        status_layout.addWidget(status_text)
        status_layout.addStretch()

        layout.addWidget(status_widget)

        # Last start time
        start_time = QLabel(f"上次启动: {self.device.last_start}")
        layout.addWidget(start_time)

        # Add spacer
        layout.addStretch()

        # Action button
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 5, 0, 0)

        view_btn = QPushButton("查看详情")
        view_btn.setObjectName("viewDetailBtn")
        view_btn.clicked.connect(lambda: self.parent_page.show_device_detail(self.device.name))

        button_layout.addStretch()
        button_layout.addWidget(view_btn)

        layout.addWidget(button_widget)


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

        # Create a scroll area for the cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Container widget for the grid
        card_container = QWidget()
        self.card_grid = QGridLayout(card_container)
        self.card_grid.setContentsMargins(10, 10, 10, 10)
        self.card_grid.setSpacing(20)

        # Add device cards to the grid
        self.populate_device_cards()

        # Set the container as the scroll area widget
        scroll_area.setWidget(card_container)
        layout.addWidget(scroll_area)

        # Add a device detail section - will be shown when "查看详情" is clicked
        self.device_detail_widget = QWidget()
        self.device_detail_widget.hide()

        layout.addWidget(self.device_detail_widget)

    def populate_device_cards(self):
        # Clear existing cards if any
        while self.card_grid.count():
            item = self.card_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Define number of columns (can adjust based on window width if needed)
        cols = 3

        # Add cards to grid
        for index, device in enumerate(self.devices):
            row = index // cols
            col = index % cols

            card = DeviceCard(device, self)
            self.card_grid.addWidget(card, row, col)

    def show_device_detail(self, device_name):
        # Clear existing content in device detail widget
        if self.device_detail_widget.layout():
            QWidget().setLayout(self.device_detail_widget.layout())

        # Create new layout
        detail_layout = QVBoxLayout(self.device_detail_widget)

        # Header with back button
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        back_btn = QPushButton("← 返回设备列表")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(lambda: self.device_detail_widget.hide())

        # Device title
        device_title = QLabel(f"设备详情: {device_name}")
        device_title.setFont(QFont("Arial", 14, QFont.Bold))
        device_title.setObjectName("deviceDetailTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(device_title)
        header_layout.addStretch()

        detail_layout.addWidget(header_widget)

        # Create tabs
        tab_widget = QTabWidget()
        tab_widget.setObjectName("detailTabs")

        # Info tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)

        # Create a simple info card instead of a table
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")

        info_form = QFormLayout(info_frame)
        info_form.setContentsMargins(20, 20, 20, 20)
        info_form.setSpacing(15)

        info_items = [
            ("设备名称", device_name),
            ("设备类型", "模拟器"),
            ("状态", "运行正常"),
            ("上次启动时间", "2025-02-26 11:45:14"),
            ("启动次数", "42")
        ]

        for key, value in info_items:
            label = QLabel(key + ":")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            value_label = QLabel(value)
            info_form.addRow(label, value_label)

        info_layout.addWidget(info_frame)
        info_layout.addStretch()

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

        # Create cards for resources instead of a table
        resources_container = QWidget()
        resources_layout = QVBoxLayout(resources_container)
        resources_layout.setContentsMargins(0, 0, 0, 0)
        resources_layout.setSpacing(10)

        for resource in self.resources:
            resource_card = QFrame()
            resource_card.setObjectName("resourceCard")
            resource_card.setFrameShape(QFrame.StyledPanel)
            card_layout = QHBoxLayout(resource_card)

            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(resource.enabled)

            # Resource name
            name_label = QLabel(resource.name)
            name_label.setFont(QFont("Arial", 11))

            # Buttons
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)

            run_btn = QPushButton("运行")
            run_btn.setFixedWidth(60)

            settings_btn = QPushButton("设置")
            settings_btn.setFixedWidth(60)
            settings_btn.clicked.connect(lambda checked, r=resource: self.show_resource_settings(r))

            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)

            # Add all elements to card
            card_layout.addWidget(checkbox)
            card_layout.addWidget(name_label)
            card_layout.addStretch()
            card_layout.addWidget(button_widget)

            resources_layout.addWidget(resource_card)

        resource_layout.addWidget(resources_container)

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

        # Show the widget and hide the grid
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
            form_layout.setSpacing(15)

            for setting in group.settings:
                label = QLabel(setting.name)
                label.setFont(QFont("Arial", 10))

                if setting.type == "checkbox":
                    widget = QCheckBox()
                    widget.setChecked(setting.value)
                    form_layout.addRow(label, widget)

                elif setting.type == "combobox":
                    widget = QComboBox()
                    widget.addItems(setting.options)
                    widget.setCurrentText(setting.value)
                    form_layout.addRow(label, widget)

                elif setting.type == "input":
                    widget = QLineEdit(setting.value)
                    form_layout.addRow(label, widget)

            collapsible.add_widget(form_widget)
            content_layout.addWidget(collapsible)

        # Add save button
        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("saveSettingsButton")
        content_layout.addWidget(save_btn)

        # Add stretch to push everything to the top
        content_layout.addStretch()