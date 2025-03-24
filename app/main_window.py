import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QScrollArea
)

from app.components.navigation_button import NavigationButton
from app.models.config.global_config import global_config
from app.pages.device_info_page import DeviceInfoPage
from app.pages.download_page import DownloadPage
from app.pages.home_page import HomePage
from app.pages.info_page import InfoPage
from app.pages.settings_page import SettingsPage
from app.utils.theme_manager import theme_manager
from app.widgets.add_device_dialog import AddDeviceDialog
from core.tasker_manager import task_manager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设备管理系统")
        self.setMinimumSize(1200, 800)

        # Track the currently active button and page
        self.current_page = "home"
        self.current_device = None
        self.current_button_id = None  # Track the unique button ID

        self.load_config()
        # Initialize theme manager
        self.theme_manager = theme_manager
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

        # Add home button
        self.home_btn = NavigationButton("首页", "assets/icons/home.svg")
        sidebar_layout.addWidget(self.home_btn)

        # Add separator after home button
        separator_top = QFrame()
        separator_top.setFrameShape(QFrame.HLine)
        separator_top.setFrameShadow(QFrame.Sunken)
        separator_top.setObjectName("sidebarSeparator")
        sidebar_layout.addWidget(separator_top)

        # Device buttons container (scrollable)
        self.device_buttons_container = QWidget()
        self.device_buttons_container.setObjectName("deviceButtonsContainer")
        self.device_buttons_layout = QVBoxLayout(self.device_buttons_container)
        self.device_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.device_buttons_layout.setSpacing(0)
        self.device_buttons_layout.setAlignment(Qt.AlignTop)

        # Scrollable area for devices - initially not shown
        self.device_scroll_area = QScrollArea()
        self.device_scroll_area.setObjectName("deviceScrollArea")
        self.device_scroll_area.setWidgetResizable(True)
        self.device_scroll_area.setFrameShape(QFrame.NoFrame)
        self.device_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.device_scroll_area.setWidget(self.device_buttons_container)
        sidebar_layout.addWidget(self.device_scroll_area)

        # Add separator after device scroll area
        separator_middle = QFrame()
        separator_middle.setFrameShape(QFrame.HLine)
        separator_middle.setFrameShadow(QFrame.Sunken)
        separator_middle.setObjectName("sidebarSeparator")
        sidebar_layout.addWidget(separator_middle)

        # Add device button (non-checkable) - right after the device list
        self.add_device_btn = NavigationButton("添加设备", "assets/icons/apps-add.svg")
        self.add_device_btn.setCheckable(False)  # Make it non-checkable
        self.add_device_btn.clicked.connect(self.open_add_device_dialog)
        sidebar_layout.addWidget(self.add_device_btn)

        # Add resource download button after the add device button (moved from above)
        self.download_btn = NavigationButton("资源下载", "assets/icons/updata_res.svg")
        sidebar_layout.addWidget(self.download_btn)

        # Add separator before bottom buttons
        separator_bottom = QFrame()
        separator_bottom.setFrameShape(QFrame.HLine)
        separator_bottom.setFrameShadow(QFrame.Sunken)
        separator_bottom.setObjectName("sidebarSeparator")
        sidebar_layout.addStretch()  # Push bottom buttons to the bottom
        sidebar_layout.addWidget(separator_bottom)

        # Add bottom buttons
        # Add settings button
        self.settings_btn = NavigationButton("设置", "assets/icons/settings.svg")
        sidebar_layout.addWidget(self.settings_btn)

        # Add info button
        self.info_btn = NavigationButton("软件信息", "assets/icons/info.svg")
        sidebar_layout.addWidget(self.info_btn)

        main_layout.addWidget(sidebar)

        # Create content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 15, 15, 15)

        main_layout.addWidget(self.content_widget)

        # Initialize pages
        self.pages = {
            "home": HomePage(),
            "download": DownloadPage(),
            "info": InfoPage(),
            "settings": SettingsPage()
        }

        # Device pages will be created dynamically
        self.device_pages = {}

        # Connect navigation buttons
        self.home_btn.setChecked(True)
        self.home_btn.clicked.connect(lambda: self.show_page("home"))
        self.download_btn.clicked.connect(lambda: self.show_page("download"))
        self.settings_btn.clicked.connect(lambda: self.show_page("settings"))
        self.info_btn.clicked.connect(lambda: self.show_page("info"))

        # Connect signals
        self.pages["home"].device_added.connect(self.refresh_device_list)

        # Initialize with home page
        self.show_page("home")

        # Load devices
        self.load_devices()

        # Update scroll area visibility
        self.update_scroll_area_visibility()

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
        for i, device in enumerate(devices):
            device_btn = NavigationButton(device.device_name, "assets/icons/browser.svg")
            # Ensure the same style is applied
            device_btn.setObjectName("navButton")
            # Store a unique identifier for each button - combination of name and index
            device_btn_id = f"{device.device_name}_{i}"
            device_btn.setProperty("device_btn_id", device_btn_id)
            device_btn.clicked.connect(lambda checked, btn_id=device_btn_id, name=device.device_name:
                                       self.show_device_page(name, btn_id))
            # If this is the current device and has the current button ID, check the button
            if self.current_device == device.device_name and self.current_button_id == device_btn_id:
                device_btn.setChecked(True)
            self.device_buttons_layout.addWidget(device_btn)

            # Create device page if it doesn't exist
            if device.device_name not in self.device_pages:
                self.device_pages[device.device_name] = DeviceInfoPage(device.device_name)

        # Update scroll area visibility based on device count
        self.update_scroll_area_visibility()

    def update_scroll_area_visibility(self):
        """Update the visibility of the scroll area based on device count"""
        devices = global_config.get_devices_config().devices

        # 更精确地计算窗口中固定元素的高度
        button_height = 60  # 每个按钮的高度
        separator_height = 2  # 每个分隔线的高度

        # 计算固定元素占用的总高度
        fixed_elements = [
            button_height,  # 首页按钮
            separator_height,  # 首页按钮下方的分隔线
            separator_height,  # 设备列表下方的分隔线
            button_height,  # 添加设备按钮
            button_height,  # 资源下载按钮
            separator_height,  # 底部分隔线
            button_height,  # 设置按钮
            button_height  # 软件信息按钮
        ]

        fixed_height = sum(fixed_elements)
        # 添加上下边距
        window_margin = 20  # 预留一些边距空间

        # 计算可用于设备列表的最大高度
        available_height = self.height() - fixed_height - window_margin
        required_height = len(devices) * button_height  # 每个按钮是60px高

        # 只有在有设备时才显示滚动区域
        if len(devices) > 0:
            self.device_scroll_area.setVisible(True)

            # 如果设备较少，则设置准确高度以避免空白
            if required_height < available_height:
                self.device_scroll_area.setFixedHeight(required_height)
            else:
                # 允许滚动区域使用可用空间
                self.device_scroll_area.setFixedHeight(available_height)
        else:
            # 没有设备时隐藏滚动区域
            self.device_scroll_area.setVisible(False)
            self.device_scroll_area.setFixedHeight(0)

    def resizeEvent(self, event):
        """Handle resize events to update scroll area visibility"""
        super().resizeEvent(event)
        self.update_scroll_area_visibility()

    def show_device_page(self, device_name, button_id=None):
        """Show the info page for a specific device"""
        # Update current page tracker
        self.current_page = None
        self.current_device = device_name
        self.current_button_id = button_id

        # Uncheck all navigation buttons
        self.home_btn.setChecked(False)
        self.download_btn.setChecked(False)
        self.settings_btn.setChecked(False)
        self.info_btn.setChecked(False)

        # Uncheck all device buttons except the selected one
        for i in range(self.device_buttons_layout.count()):
            item = self.device_buttons_layout.itemAt(i)
            if item.widget():
                btn = item.widget()
                # Use the unique button_id to set checked state, not just name
                if button_id:
                    btn.setChecked(btn.property("device_btn_id") == button_id)
                else:
                    # Fallback for compatibility with existing code
                    btn.setChecked(btn.toolTip() == device_name and i == 0)

        # Clear existing content
        self.clear_content()

        # Create the page if it doesn't exist
        if device_name not in self.device_pages:
            self.device_pages[device_name] = DeviceInfoPage(device_name)

        # Show the device page
        self.content_layout.addWidget(self.device_pages[device_name])
        self.device_pages[device_name].show()

    def show_page(self, page_name):
        # Update current page tracker
        self.current_page = page_name
        self.current_device = None

        # Update navigation button states
        self.home_btn.setChecked(page_name == "home")
        self.download_btn.setChecked(page_name == "download")
        self.settings_btn.setChecked(page_name == "settings")
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
        # Create and show the dialog
        dialog = AddDeviceDialog(global_config, self)

        # Execute the dialog
        result = dialog.exec_()

        if result:
            # Reload devices after adding a new one
            self.load_devices()
            # Notify others that a device was added
            self.pages["home"].device_added.emit()

        # Restore the current page/device selection after dialog closes
        if self.current_device and self.current_button_id:
            # Re-select the current device using unique button ID
            for i in range(self.device_buttons_layout.count()):
                item = self.device_buttons_layout.itemAt(i)
                if item.widget() and item.widget().property("device_btn_id") == self.current_button_id:
                    item.widget().setChecked(True)
        elif self.current_device:
            # Fallback if we don't have a button ID (for compatibility)
            for i in range(self.device_buttons_layout.count()):
                item = self.device_buttons_layout.itemAt(i)
                if item.widget() and item.widget().toolTip() == self.current_device:
                    item.widget().setChecked(True)
                    break  # Only check the first matching button
        else:
            # Re-select the current page
            if self.current_page == "home":
                self.home_btn.setChecked(True)
            elif self.current_page == "download":
                self.download_btn.setChecked(True)
            elif self.current_page == "settings":
                self.settings_btn.setChecked(True)
            elif self.current_page == "info":
                self.info_btn.setChecked(True)

    def refresh_device_list(self):
        """Refresh the device list in the navigation bar"""
        self.load_devices()

    def clear_content(self):
        # Clear all widgets from content layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                self.content_layout.removeWidget(widget)

    @staticmethod
    def load_config():
        devices_config_path = "assets/config/devices.json"
        # 如果文件不存在，先创建该文件并写入 "{}"
        if not os.path.exists(devices_config_path):
            # 确保父目录存在
            os.makedirs(os.path.dirname(devices_config_path), exist_ok=True)
            with open(devices_config_path, "w", encoding="utf-8") as f:
                f.write("{}")

        global_config.load_devices_config(devices_config_path)

        resource_dir = "assets/resource/"
        # 如果目录不存在，则创建
        if not os.path.exists(resource_dir):
            os.makedirs(resource_dir)

        global_config.load_all_resources_from_directory(resource_dir)

        task_manager.setup_all_device_scheduled_tasks()

    def show_previous_device_or_home(self, deleted_device_name):
        """
        Navigate to another device page or home page after a device is deleted

        Args:
            deleted_device_name: The name of the device that was deleted
        """
        try:
            # Remove the device page from device_pages dictionary if it exists
            if deleted_device_name in self.device_pages:
                self.device_pages[deleted_device_name].deleteLater()
                del self.device_pages[deleted_device_name]

            # Get all remaining devices
            devices = global_config.get_devices_config().devices

            # Refresh the device list in the sidebar
            self.refresh_device_list()

            if devices:
                # Show the first device in the list
                device_names = [device.device_name for device in devices]
                self.show_device_page(device_names[0])
            else:
                # No devices left, show home page
                self.show_page("home")

        except Exception as e:
            # If anything goes wrong, just show the home page
            print(f"Error navigating after device deletion: {e}")
            self.show_page("home")