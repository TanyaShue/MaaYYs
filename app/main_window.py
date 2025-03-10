from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QToolButton

from app.components.navigation_button import NavigationButton
from app.pages.device_page import DeviceListPage
from app.pages.download_page import DownloadPage
from app.pages.home_page import HomePage
from app.pages.info_page import InfoPage
from app.utils.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设备管理系统")
        self.setMinimumSize(1000, 600)

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
        sidebar.setFixedWidth(48)  # Fixed width for icon-only sidebar
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setAlignment(Qt.AlignTop)  # Align to top



        # Add navigation buttons (icon only)
        self.home_btn = NavigationButton("首页", "assets/icons/home.svg")
        self.device_btn = NavigationButton("设备信息", "assets/icons/browser.svg")
        self.download_btn = NavigationButton("资源下载", "assets/icons/apps-add.svg")

        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.device_btn)
        sidebar_layout.addWidget(self.download_btn)
        sidebar_layout.addStretch()

        # Add bottom info button
        self.info_btn = NavigationButton("软件信息", "assets/icons/info.svg")
        sidebar_layout.addWidget(self.info_btn)
        # Theme toggle button instead of dropdown
        self.theme_btn = QToolButton()
        self.theme_btn.setIcon(QIcon("assets/icons/theme.svg"))  # You need this icon
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
            "device": DeviceListPage(),
            "download": DownloadPage(),
            "info": InfoPage()
        }

        # Connect navigation buttons
        self.home_btn.setChecked(True)
        self.home_btn.clicked.connect(lambda: self.show_page("home"))
        self.device_btn.clicked.connect(lambda: self.show_page("device"))
        self.download_btn.clicked.connect(lambda: self.show_page("download"))
        self.info_btn.clicked.connect(lambda: self.show_page("info"))
        self.pages["home"].device_added.connect(self.pages["device"].refresh_device_list)
        # Initialize with home page
        self.show_page("home")

    def show_page(self, page_name):
        # Update navigation button states
        self.home_btn.setChecked(page_name == "home")
        self.device_btn.setChecked(page_name == "device")
        self.download_btn.setChecked(page_name == "download")
        self.info_btn.setChecked(page_name == "info")

        # Clear existing content
        self.clear_content()

        # Show requested page
        if page_name in self.pages:
            self.content_layout.addWidget(self.pages[page_name])
            self.pages[page_name].show()

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