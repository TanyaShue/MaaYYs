from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QLabel

from app.components.navigation_button import NavigationButton
from app.pages.home_page import HomePage
from app.pages.device_page import DevicePage
from app.pages.download_page import DownloadPage
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
        sidebar.setFixedWidth(200)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        # Add theme selector at top of sidebar
        theme_widget = QWidget()
        theme_widget.setObjectName("themeSelector")
        theme_layout = QHBoxLayout(theme_widget)

        theme_label = QLabel("主题:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["明亮", "深色"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)

        sidebar_layout.addWidget(theme_widget)

        # Add navigation buttons
        self.home_btn = NavigationButton("首页", "resources/icons/home.png")
        self.device_btn = NavigationButton("设备信息", "resources/icons/device.png")
        self.download_btn = NavigationButton("资源下载", "resources/icons/download.png")

        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.device_btn)
        sidebar_layout.addWidget(self.download_btn)
        sidebar_layout.addStretch()

        # Add bottom info button
        self.info_btn = NavigationButton("软件信息", "resources/icons/info.png")
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
            "device": DevicePage(),
            "download": DownloadPage(),
            "info": InfoPage()
        }

        # Connect navigation buttons
        self.home_btn.setChecked(True)
        self.home_btn.clicked.connect(lambda: self.show_page("home"))
        self.device_btn.clicked.connect(lambda: self.show_page("device"))
        self.download_btn.clicked.connect(lambda: self.show_page("download"))
        self.info_btn.clicked.connect(lambda: self.show_page("info"))

        # Initialize with home pages
        self.show_page("home")

    def show_page(self, page_name):
        # Update navigation button states
        self.home_btn.setChecked(page_name == "home")
        self.device_btn.setChecked(page_name == "device")
        self.download_btn.setChecked(page_name == "download")
        self.info_btn.setChecked(page_name == "info")

        # Clear existing content
        self.clear_content()

        # Show requested pages
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

    def change_theme(self, index):
        if index == 0:
            self.theme_manager.apply_theme("light")
        else:
            self.theme_manager.apply_theme("dark")