from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget,
    QScrollArea, QFrame, QComboBox, QCheckBox,
    QTimeEdit, QLineEdit, QPushButton, QSpinBox
)
from PySide6.QtGui import QFont
from app.utils.theme_manager import theme_manager


class SettingsPage(QWidget):
    """Settings page with categories on the left and content on the right"""

    def __init__(self):
        super().__init__()
        self.setObjectName("settingsPage")
        self.theme_manager = theme_manager
        self.current_theme = "light"
        self.initUI()

    def initUI(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left sidebar for categories
        self.categories_widget = QListWidget()
        self.categories_widget.setFixedWidth(200)
        self.categories_widget.setObjectName("settingsCategories")
        self.categories_widget.setFrameShape(QFrame.NoFrame)
        self.categories_widget.currentRowChanged.connect(self.scroll_to_section)

        # Add categories
        categories = [
            "切换配置", "定时执行", "性能设置", "运行设置",
            "连接设置", "启动设置", "远程控制", "界面设置",
            "外部通知", "热键设置", "更新设置"
        ]

        for category in categories:
            item = QListWidgetItem(category)
            self.categories_widget.addItem(item)

        # Right content area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setObjectName("settingsScrollArea")

        # Content widget
        self.content_widget = QWidget()
        self.content_widget.setObjectName("content_widget")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        # Page title
        self.page_title = QLabel("设置")
        self.page_title.setObjectName("pageTitle")
        self.content_layout.addWidget(self.page_title)

        # Sections for each category
        self.sections = {}

        # Create sections
        self.create_config_switch_section()
        self.create_scheduled_tasks_section()
        self.create_performance_section()
        self.create_operation_section()
        self.create_connection_section()
        self.create_startup_section()
        self.create_remote_control_section()
        self.create_interface_section()
        self.create_notifications_section()
        self.create_hotkey_section()
        self.create_update_section()

        # Add a spacer at the end
        self.content_layout.addStretch()

        # Set the content widget to the scroll area
        self.scroll_area.setWidget(self.content_widget)

        # Add widgets to main layout
        main_layout.addWidget(self.categories_widget)
        main_layout.addWidget(self.scroll_area)

        # Select the first category by default
        self.categories_widget.setCurrentRow(0)

    def create_section(self, title):
        """Create a new section with title and return its content layout"""
        section = QWidget()
        section.setObjectName(f"section_{title}")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 20)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)

        # Separator line
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        section_layout.addWidget(title_label)
        section_layout.addWidget(separator)

        # Content widget
        content = QWidget()
        content.setObjectName("contentCard")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        section_layout.addWidget(content)

        # Add to main content layout
        self.content_layout.addWidget(section)

        # Store section reference
        self.sections[title] = section

        return content_layout

    def create_config_switch_section(self):
        """Create the configuration switch section"""
        layout = self.create_section("切换配置")

        # Config selector row
        config_row = QHBoxLayout()
        config_row.setContentsMargins(0, 0, 0, 12)

        # Dropdown
        config_combo = QComboBox()
        config_combo.addItem("Default")
        config_combo.setFixedWidth(300)

        # Config name
        name_label = QLabel("配置名称")
        name_label.setObjectName("infoLabel")
        name_input = QLineEdit()
        name_input.setFixedWidth(300)

        # Add button
        add_button = QPushButton("添加")
        add_button.setObjectName("secondaryButton")
        add_button.setFixedWidth(80)

        # Add to layouts
        config_row.addWidget(config_combo)
        config_row.addStretch()

        name_row = QHBoxLayout()
        name_row.addWidget(name_label)
        name_row.addWidget(name_input)
        name_row.addWidget(add_button)
        name_row.addStretch()

        layout.addLayout(config_row)
        layout.addLayout(name_row)

    def create_scheduled_tasks_section(self):
        """Create the scheduled tasks section"""
        layout = self.create_section("定时执行")

        # Checkboxes row
        check_row = QHBoxLayout()
        force_startup = QCheckBox("强制定时启动")
        custom_config = QCheckBox("自定义配置选择")
        check_row.addWidget(force_startup)
        check_row.addWidget(custom_config)
        check_row.addStretch()
        layout.addLayout(check_row)

        # Time slots
        self.create_time_slot(layout, "定时 1", "22", "00", True)
        self.create_time_slot(layout, "定时 2", "03", "00", False)
        self.create_time_slot(layout, "定时 3", "06", "00", False)
        self.create_time_slot(layout, "定时 4", "04", "00", True)

    def create_time_slot(self, parent_layout, label_text, hour, minute, checked):
        """Create a time slot row with checkbox, label, and time edit"""
        row = QHBoxLayout()

        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(checked)

        # Label
        label = QLabel(label_text)
        label.setObjectName("infoLabel")
        label.setFixedWidth(80)

        # Time container
        time_container = QWidget()
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(4)

        # Hour input
        hour_input = QSpinBox()
        hour_input.setRange(0, 23)
        hour_input.setValue(int(hour))
        hour_input.setFixedWidth(60)

        # Separator
        separator = QLabel(":")
        separator.setFixedWidth(10)
        separator.setAlignment(Qt.AlignCenter)

        # Minute input
        minute_input = QSpinBox()
        minute_input.setRange(0, 59)
        minute_input.setValue(int(minute))
        minute_input.setFixedWidth(60)

        # Add to time container
        time_layout.addWidget(hour_input)
        time_layout.addWidget(separator)
        time_layout.addWidget(minute_input)

        # Add to row
        row.addWidget(checkbox)
        row.addWidget(label)
        row.addWidget(time_container)
        row.addStretch()

        parent_layout.addLayout(row)

    def create_performance_section(self):
        """Create the performance settings section"""
        layout = self.create_section("性能设置")

        # CPU usage setting
        cpu_row = QHBoxLayout()
        cpu_label = QLabel("使用 CPU 加速推理")
        cpu_label.setObjectName("infoLabel")
        cpu_combo = QComboBox()
        cpu_combo.addItem("不使用")
        cpu_combo.addItem("低强度使用")
        cpu_combo.addItem("中强度使用")
        cpu_combo.addItem("高强度使用")

        cpu_row.addWidget(cpu_label)
        cpu_row.addWidget(cpu_combo)
        cpu_row.addStretch()

        # Add option description
        cpu_desc = QLabel("根据设备CPU性能选择合适的加速级别，高性能设备可选择高强度")
        cpu_desc.setObjectName("resourceDescription")
        cpu_desc.setWordWrap(True)

        # Add to layout
        option_widget = QWidget()
        option_widget.setObjectName("optionWidget")
        option_layout = QVBoxLayout(option_widget)
        option_layout.addLayout(cpu_row)
        option_layout.addWidget(cpu_desc)

        layout.addWidget(option_widget)

    def create_operation_section(self):
        """Create the operation settings section"""
        layout = self.create_section("运行设置")

        # Basic settings
        auto_start = QCheckBox("系统启动时自动运行")
        auto_start.setObjectName("settingCheckBox")

        minimize_to_tray = QCheckBox("最小化到系统托盘")
        minimize_to_tray.setObjectName("settingCheckBox")

        # Description for auto start
        auto_start_desc = QLabel("设置系统启动时自动启动应用程序")
        auto_start_desc.setObjectName("resourceDescription")
        auto_start_desc.setContentsMargins(28, 0, 0, 10)

        # Description for minimize
        minimize_desc = QLabel("关闭窗口时最小化到系统托盘而非退出")
        minimize_desc.setObjectName("resourceDescription")
        minimize_desc.setContentsMargins(28, 0, 0, 10)

        layout.addWidget(auto_start)
        layout.addWidget(auto_start_desc)
        layout.addWidget(minimize_to_tray)
        layout.addWidget(minimize_desc)

    def create_connection_section(self):
        """Create the connection settings section"""
        layout = self.create_section("连接设置")

        # Connection timeout
        timeout_row = QHBoxLayout()
        timeout_label = QLabel("连接超时时间（秒）")
        timeout_label.setObjectName("infoLabel")
        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 120)
        timeout_spin.setValue(30)

        timeout_row.addWidget(timeout_label)
        timeout_row.addWidget(timeout_spin)
        timeout_row.addStretch()

        # Retry settings
        retry_row = QHBoxLayout()
        retry_label = QLabel("自动重试次数")
        retry_label.setObjectName("infoLabel")
        retry_spin = QSpinBox()
        retry_spin.setRange(0, 10)
        retry_spin.setValue(3)

        retry_row.addWidget(retry_label)
        retry_row.addWidget(retry_spin)
        retry_row.addStretch()

        layout.addLayout(timeout_row)
        layout.addLayout(retry_row)

    def create_startup_section(self):
        """Create the startup settings section"""
        layout = self.create_section("启动设置")

        startup_mode = QCheckBox("启动时自动连接设备")
        verify_device = QCheckBox("启动时验证设备状态")

        # Add descriptive text
        startup_desc = QLabel("应用启动时自动尝试连接上一次使用的设备")
        startup_desc.setObjectName("resourceDescription")
        startup_desc.setContentsMargins(28, 0, 0, 10)

        verify_desc = QLabel("启动时检查所有设备的连接状态")
        verify_desc.setObjectName("resourceDescription")
        verify_desc.setContentsMargins(28, 0, 0, 10)

        layout.addWidget(startup_mode)
        layout.addWidget(startup_desc)
        layout.addWidget(verify_device)
        layout.addWidget(verify_desc)

    def create_remote_control_section(self):
        """Create the remote control section"""
        layout = self.create_section("远程控制")

        enable_remote = QCheckBox("启用远程控制")
        require_auth = QCheckBox("要求远程认证")

        # Add warning text for security
        warning = QLabel("注意：启用远程控制可能存在安全风险，请确保使用安全的网络环境")
        warning.setObjectName("warningText")
        warning.setWordWrap(True)

        port_row = QHBoxLayout()
        port_label = QLabel("远程控制端口")
        port_label.setObjectName("infoLabel")
        port_spin = QSpinBox()
        port_spin.setRange(1024, 65535)
        port_spin.setValue(8080)

        port_row.addWidget(port_label)
        port_row.addWidget(port_spin)
        port_row.addStretch()

        layout.addWidget(enable_remote)
        layout.addWidget(require_auth)
        layout.addWidget(warning)
        layout.addLayout(port_row)

    def create_interface_section(self):
        """Create the interface settings section"""
        layout = self.create_section("界面设置")

        # Theme settings
        theme_row = QHBoxLayout()
        theme_label = QLabel("界面主题")
        theme_label.setObjectName("infoLabel")
        theme_combo = QComboBox()
        theme_combo.addItem("明亮主题")
        theme_combo.addItem("深色主题")

        if self.current_theme == "dark":
            theme_combo.setCurrentIndex(1)
        else:
            theme_combo.setCurrentIndex(0)

        theme_combo.currentIndexChanged.connect(self.toggle_theme)

        theme_row.addWidget(theme_label)
        theme_row.addWidget(theme_combo)
        theme_row.addStretch()

        # Language settings
        lang_row = QHBoxLayout()
        lang_label = QLabel("界面语言")
        lang_label.setObjectName("infoLabel")
        lang_combo = QComboBox()
        lang_combo.addItem("简体中文")
        lang_combo.addItem("English")

        lang_row.addWidget(lang_label)
        lang_row.addWidget(lang_combo)
        lang_row.addStretch()

        # Add note about restart
        note = QLabel("注：语言设置更改将在应用重启后生效")
        note.setObjectName("infoText")

        layout.addLayout(theme_row)
        layout.addLayout(lang_row)
        layout.addWidget(note)

    def create_notifications_section(self):
        """Create the notifications section"""
        layout = self.create_section("外部通知")

        enable_notify = QCheckBox("启用任务完成通知")
        sound_notify = QCheckBox("启用声音提醒")

        # Add descriptive text
        enable_desc = QLabel("任务完成时显示系统通知")
        enable_desc.setObjectName("resourceDescription")
        enable_desc.setContentsMargins(28, 0, 0, 10)

        sound_desc = QLabel("任务完成时播放提示音")
        sound_desc.setObjectName("resourceDescription")
        sound_desc.setContentsMargins(28, 0, 0, 10)

        layout.addWidget(enable_notify)
        layout.addWidget(enable_desc)
        layout.addWidget(sound_notify)
        layout.addWidget(sound_desc)

    def create_hotkey_section(self):
        """Create the hotkey settings section"""
        layout = self.create_section("热键设置")

        # Main hotkey
        main_row = QHBoxLayout()
        main_label = QLabel("主窗口热键")
        main_label.setObjectName("infoLabel")
        main_input = QLineEdit("Ctrl+Alt+D")

        main_row.addWidget(main_label)
        main_row.addWidget(main_input)
        main_row.addStretch()

        # Task hotkey
        task_row = QHBoxLayout()
        task_label = QLabel("任务管理热键")
        task_label.setObjectName("infoLabel")
        task_input = QLineEdit("Ctrl+Alt+T")

        task_row.addWidget(task_label)
        task_row.addWidget(task_input)
        task_row.addStretch()

        # Add instruction text
        instruction = QLabel("点击输入框，然后按下您想要设置的快捷键组合")
        instruction.setObjectName("instructionText")

        layout.addWidget(instruction)
        layout.addLayout(main_row)
        layout.addLayout(task_row)

    def create_update_section(self):
        """Create the update settings section"""
        layout = self.create_section("更新设置")

        auto_check = QCheckBox("自动检查更新")
        beta_updates = QCheckBox("接收测试版更新")

        # Add warning for beta updates
        beta_warning = QLabel("测试版可能包含不稳定功能，可能影响正常使用")
        beta_warning.setObjectName("warningText")
        beta_warning.setContentsMargins(28, 0, 0, 10)

        check_row = QHBoxLayout()
        check_button = QPushButton("立即检查更新")
        check_button.setObjectName("primaryButton")

        check_row.addWidget(check_button)
        check_row.addStretch()

        layout.addWidget(auto_check)
        layout.addWidget(beta_updates)
        layout.addWidget(beta_warning)
        layout.addLayout(check_row)

    def scroll_to_section(self, index):
        """Scroll to the selected section"""
        if index < 0 or index >= len(self.sections):
            return

        # Get the section widget based on the index
        section_title = self.categories_widget.item(index).text()
        if section_title in self.sections:
            section = self.sections[section_title]
            # Scroll to the section
            self.scroll_area.ensureWidgetVisible(section)

    def toggle_theme(self, index):
        """Toggle between light and dark themes"""
        if index == 0:  # Light theme
            self.theme_manager.apply_theme("light")
            self.current_theme = "light"
        else:  # Dark theme
            self.theme_manager.apply_theme("dark")
            self.current_theme = "dark"