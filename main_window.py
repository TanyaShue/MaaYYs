from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QApplication
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from app import MainPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("我的 PySide6 程序")
        self.setGeometry(100, 100, 800, 600) # 设置窗口初始位置和大小

        # 加载 QSS 样式
        self.load_stylesheet("ui/style.qss")

        # 创建主布局 - 水平布局 (导航栏 + 内容区域)
        main_layout = QHBoxLayout()

        # 创建导航栏
        self.navigation_bar = NavigationBar()
        main_layout.addWidget(self.navigation_bar)

        # 创建堆叠窗口部件，用于页面切换
        self.content_area = QStackedWidget()
        main_layout.addWidget(self.content_area)

        # 设置主窗口的中央部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 初始化页面并添加到堆叠窗口 (这里先留空，稍后添加页面)
        self.init_pages()

        # 连接导航栏按钮信号到页面切换函数
        self.navigation_bar.button_clicked.connect(self.switch_page)

    def load_stylesheet(self, qss_path):
        """加载 QSS 样式表文件"""
        app_style = QApplication.instance().styleSheet()
        qss_file_path = Path(__file__).parent.parent / qss_path  # 假设 qss 文件在 ui 目录下
        try:
            with open(qss_file_path, "r",encoding="utf-8") as file:
                app_style += file.read()
                print("QSS 文件内容加载成功:")  # 添加成功加载提示
                # print(app_style) # 打印加载的样式表 (可以取消注释来查看)
        except FileNotFoundError:
            print(f"QSS file not found: {qss_file_path}")
        QApplication.instance().setStyleSheet(app_style)


    def init_pages(self):
        """初始化页面"""
        # 这里先添加一些空的 Widget 作为占位页面
        self.home_page = MainPage()
        self.settings_page = QWidget()
        self.display_page = QWidget()
        self.shortcut_page = QWidget()
        self.assistant_page = QWidget()
        self.data_page = QWidget()
        self.about_page = QWidget()

        self.content_area.addWidget(self.home_page)
        self.content_area.addWidget(self.settings_page)
        self.content_area.addWidget(self.display_page)
        self.content_area.addWidget(self.shortcut_page)
        self.content_area.addWidget(self.assistant_page)
        self.content_area.addWidget(self.data_page)
        self.content_area.addWidget(self.about_page)

        # 可以设置初始显示的页面，例如第一个页面
        self.content_area.setCurrentWidget(self.home_page)


    def switch_page(self, button_name):
        """切换页面"""
        if button_name == "首页":
            self.content_area.setCurrentWidget(self.home_page)
        elif button_name == "常规设置":
            self.content_area.setCurrentWidget(self.settings_page)
        elif button_name == "显示设置":
            self.content_area.setCurrentWidget(self.display_page)
        elif button_name == "快捷方式":
            self.content_area.setCurrentWidget(self.shortcut_page)
        elif button_name == "快捷助手":
            self.content_area.setCurrentWidget(self.assistant_page)
        elif button_name == "回数据设置":
            self.content_area.setCurrentWidget(self.data_page)
        elif button_name == "关于我们":
            self.content_area.setCurrentWidget(self.about_page)
        # ... 可以继续添加更多页面的切换逻辑
        else:
            print(f"未知的按钮名称: {button_name}")


class NavigationBar(QWidget):
    """导航栏组件"""
    button_clicked = Signal(str) # 定义按钮点击信号

    def __init__(self):
        super().__init__()
        self.setObjectName("NavigationBar") # 设置 objectName 以便在 QSS 中选择

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0) # 移除边距
        layout.setSpacing(0) # 移除按钮之间的间距

        # 导航按钮
        self.buttons = {}
        button_names = ["首页", "常规设置", "显示设置", "快捷方式", "快捷助手", "回数据设置", "关于我们"] # 导航按钮名称列表
        for name in button_names:
            button = QPushButton(name)
            button.clicked.connect(lambda checked, name=name: self.button_clicked.emit(name)) # 使用 lambda 传递按钮名称
            self.buttons[name] = button
            layout.addWidget(button)

        layout.addStretch() # 底部添加弹性空间，让按钮靠顶部排列
        self.setLayout(layout)
        self.setFixedWidth(150) # 设置导航栏固定宽度 (可以根据需要调整)