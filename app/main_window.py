import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QToolButton, QLabel, QFrame, QScrollArea
)

from app.components.navigation_button import NavigationButton
from app.pages.device_page import DeviceListPage
from app.pages.download_page import DownloadPage
from app.pages.home_page import HomePage
from app.pages.info_page import InfoPage
from app.pages.device_info_page import DeviceInfoPage
from app.models.config.global_config import global_config
from app.pages.add_device_dialog import AddDeviceDialog
from app.utils.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设备管理系统")
        self.setMinimumSize(1200, 800)
        devices_config_path = "assets/config/devices.json"
        # 如果文件不存在，先创建该文件并写入 "{}"
        if not os.path.exists(devices_config_path):
            # 确保父目录存在
            os.makedirs(os.path.dirname(devices_config_path), exist_ok=True)
            with open(devices_config_path, "w", encoding="utf-8") as f:
                f.write("{}")

        global_config.load_devices_config(devices_config_path)

        resource_dir = "assets/resource/"
        global_config.load_all_resources_from_directory(resource_dir)

        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.theme_manager.apply_theme("light")  # Default theme

        # Create central widget
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)

        # Create navigation sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(60)  # Slightly wider for labels
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setAlignment(Qt.AlignTop)


        # Add navigation buttons (icon only)
        self.home_btn = NavigationButton("首页", "assets/icons/home.svg")
        self.device_btn = NavigationButton("设备信息", "assets/icons/browser.svg")
        self.download_btn = NavigationButton("资源下载", "assets/icons/apps-add.svg")

        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.device_btn)
        sidebar_layout.addWidget(self.download_btn)

        # Add separator between system and devices
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("sidebarSeparator")
        sidebar_layout.addWidget(separator)


        # Device buttons container (scrollable)
        self.device_buttons_container = QWidget()
        self.device_buttons_layout = QVBoxLayout(self.device_buttons_container)
        self.device_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.device_buttons_layout.setSpacing(0)

        # Scrollable area for devices
        device_scroll_area = QScrollArea()
        device_scroll_area.setWidgetResizable(True)
        device_scroll_area.setFrameShape(QFrame.NoFrame)
        device_scroll_area.setWidget(self.device_buttons_container)
        sidebar_layout.addWidget(device_scroll_area)

        # Add device button
        self.add_device_btn = NavigationButton("添加设备", "assets/icons/apps-add.svg")
        self.add_device_btn.clicked.connect(self.open_add_device_dialog)
        sidebar_layout.addWidget(self.add_device_btn)

        sidebar_layout.addStretch()

        # Add bottom info button
        self.info_btn = NavigationButton("软件信息", "assets/icons/info.svg")
        sidebar_layout.addWidget(self.info_btn)

        # Theme toggle button
        self.theme_btn = QToolButton()
        self.theme_btn.setIcon(QIcon("assets/icons/theme.svg"))
        self.theme_btn.setIconSize(QSize(24, 24))
        self.theme_btn.setFixedSize(48, 48)
        self.theme_btn.setToolTip("切换主题")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.current_theme = "light"

        sidebar_layout.addWidget(self.theme_btn)
        main_layout.addWidget(sidebar)

        # Create content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)

        main_layout.addWidget(self.content_widget)

        # Initialize pages
        self.pages = {
            "home": HomePage(),
            # "device": DeviceListPage(),
            "download": DownloadPage(),
            "info": InfoPage()
        }

        # Device pages will be created dynamically
        self.device_pages = {}

        # Connect navigation buttons
        self.home_btn.setChecked(True)
        self.home_btn.clicked.connect(lambda: self.show_page("home"))
        self.device_btn.clicked.connect(lambda: self.show_page("device"))
        self.download_btn.clicked.connect(lambda: self.show_page("download"))
        self.info_btn.clicked.connect(lambda: self.show_page("info"))

        # Connect signals
        self.pages["home"].device_added.connect(self.refresh_device_list)

        # Initialize with home page
        self.show_page("home")

        # Load devices
        self.load_devices()

    def load_devices(self):
        """Load devices from config and create navigation buttons"""
        # Clear existing device buttons
        while self.device_buttons_layout.count():
            item = self.device_buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get devices from global config
        devices = global_config.get_devices_config().devices

        # Create a button for each device
        for device in devices:
            device_btn = NavigationButton(device.device_name, "assets/icons/browser.svg")
            device_btn.clicked.connect(lambda checked, name=device.device_name: self.show_device_page(name))
            self.device_buttons_layout.addWidget(device_btn)

            # Create device page if it doesn't exist
            if device.device_name not in self.device_pages:
                self.device_pages[device.device_name] = DeviceInfoPage(device.device_name)

    def show_device_page(self, device_name):
        """Show the info page for a specific device"""
        # Uncheck all navigation buttons
        self.home_btn.setChecked(False)
        self.device_btn.setChecked(False)
        self.download_btn.setChecked(False)
        self.info_btn.setChecked(False)

        # Uncheck all device buttons except the selected one
        for i in range(self.device_buttons_layout.count()):
            item = self.device_buttons_layout.itemAt(i)
            if item.widget():
                btn = item.widget()
                btn.setChecked(btn.toolTip() == device_name)

        # Clear existing content
        self.clear_content()

        # Create the page if it doesn't exist
        if device_name not in self.device_pages:
            self.device_pages[device_name] = DeviceInfoPage(device_name)

        # Show the device page
        self.content_layout.addWidget(self.device_pages[device_name])
        self.device_pages[device_name].show()

    def show_page(self, page_name):
        # Update navigation button states
        self.home_btn.setChecked(page_name == "home")
        self.device_btn.setChecked(page_name == "device")
        self.download_btn.setChecked(page_name == "download")
        self.info_btn.setChecked(page_name == "info")

        # Uncheck all device buttons
        for i in range(self.device_buttons_layout.count()):
            item = self.device_buttons_layout.itemAt(i)
            if item.widget():
                item.widget().setChecked(False)

        # Clear existing content
        self.clear_content()

        # Show requested page
        if page_name in self.pages:
            self.content_layout.addWidget(self.pages[page_name])
            self.pages[page_name].show()

    def open_add_device_dialog(self):
        """Open add device dialog and refresh device list after adding"""
        dialog = AddDeviceDialog(global_config, self)
        if dialog.exec_():
            # Reload devices after adding a new one
            self.load_devices()
            # Notify others that a device was added
            self.pages["home"].device_added.emit()

    def refresh_device_list(self):
        """Refresh the device list in the navigation bar"""
        self.load_devices()
        self.pages["device"].refresh_device_list()

    def clear_content(self):
        # Clear all widgets from content layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                self.content_layout.removeWidget(widget)

    def toggle_theme(self):
        if self.current_theme == "light":
            self.theme_manager.apply_theme("dark")
            self.current_theme = "dark"
            self.theme_btn.setToolTip("切换到明亮主题")
        else:
            self.theme_manager.apply_theme("light")
            self.current_theme = "light"
            self.theme_btn.setToolTip("切换到深色主题")