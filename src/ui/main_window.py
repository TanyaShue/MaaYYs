from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
     QLabel, QTableWidget, QTextEdit,
    QSplitter, QHeaderView
)
from .ui_controller import UIController



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = UIController()

        self.setWindowTitle('MaaYYs')
        self.setMinimumSize(1440, 720)

        # 加载样式
        self.controller.load_styles(self)

        # 创建主布局
        self.main_layout = QHBoxLayout(self)

        # 左侧导航栏
        self.left_nav_widget = self.init_navigation_bar()

        # 右侧布局
        self.right_layout = QVBoxLayout()

        # 分割器
        self.splitter = QSplitter(Qt.Horizontal)

        # 初始化首页
        self.init_home_page()

        self.setLayout(self.main_layout)

    def init_navigation_bar(self):
        """初始化导航栏"""
        left_nav_widget = QWidget()
        left_nav_layout = QVBoxLayout(left_nav_widget)
        # 创建导航按钮
        nav_buttons = ['首页'] + [program.program_name for program in self.controller.programs.programs]
        for btn_text in nav_buttons:
            button = QPushButton(btn_text)
            button.setFixedHeight(50)
            button.setObjectName('navButton')
            left_nav_layout.addWidget(button)

        left_nav_layout.addStretch()

        # 添加刷新按钮
        refresh_button = QPushButton('刷新资源')
        refresh_button.setFixedHeight(50)
        refresh_button.setObjectName('refreshButton')
        refresh_button.clicked.connect(self.controller.refresh_resources)
        left_nav_layout.addWidget(refresh_button)

        self.main_layout.addWidget(left_nav_widget)
        return left_nav_widget

    def init_home_page(self):
        """初始化首页"""
        self.clear_right_layout()

        # 创建主容器部件
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setSpacing(5)
        container_layout.setContentsMargins(10, 10, 10, 10)

        # 添加标题
        title_container = self._create_title_section()
        container_layout.addWidget(title_container)

        # 中间内容和任务日志分割器
        main_splitter = QSplitter(Qt.Horizontal)

        # 左侧内容部分
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 添加表格、信息标题和详细信息
        table_container = self._create_table_section()
        info_title_container = self._create_info_title_section()
        details_container = self._create_details_section()

        left_layout.addWidget(table_container)
        left_layout.addWidget(info_title_container)
        left_layout.addWidget(details_container)

        main_splitter.addWidget(left_widget)

        # 右侧任务日志部分
        log_container = self._create_log_section()
        main_splitter.addWidget(log_container)

        # 设置初始大小比例
        main_splitter.setSizes([800, 200])

        # 将分割器添加到容器布局中
        container_layout.addWidget(main_splitter)

        self.right_layout.addWidget(container_widget)
        self.main_layout.addLayout(self.right_layout)

        # 加载设备表格数据
        self.controller.load_device_table(self.table, self.splitter, self.info_title)

    def _create_title_section(self):
        """创建标题部分"""
        title_container = QWidget()
        title_container.setFixedHeight(30)
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(0)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel('首页')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setStyleSheet("color: #2980b9;")
        title.setFixedHeight(25)  # 设置固定高度为 40 像素
        title_layout.addWidget(title)

        return title_container

    def _create_table_section(self):
        """创建表格部分"""
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setSpacing(0)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['任务名称', '游戏名称', 'adb地址', 'adb端口', '运行状态', '操作'])
        self.table.itemChanged.connect(self.controller.on_table_item_changed)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)

        table_layout.addWidget(self.table)
        return table_container

    def _create_info_title_section(self):
        """创建信息标题部分"""
        info_title_container = QWidget()
        info_title_layout = QVBoxLayout(info_title_container)
        info_title_layout.setSpacing(0)
        info_title_layout.setContentsMargins(0, 0, 0, 0)

        self.info_title = QLabel('详细信息')
        self.info_title.setAlignment(Qt.AlignCenter)
        self.info_title.setStyleSheet("color: #2980b9; margin-top: 15px;")
        info_title_layout.addWidget(self.info_title)

        return info_title_container

    def _create_details_section(self):
        """创建详细信息部分"""
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setSpacing(0)
        details_layout.setContentsMargins(0, 0, 0, 0)

        self.init_splitter()
        details_layout.addWidget(self.splitter)

        return details_container

    def _create_log_section(self):
        """创建任务日志部分"""
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setSpacing(0)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_group = QGroupBox("任务日志")
        log_group_layout = QVBoxLayout(log_group)

        log_area = QTextEdit()
        log_area.setPlaceholderText("日志输出...")
        log_area.setReadOnly(True)
        log_area.setMinimumWidth(200)  # 设置初始最小宽度

        log_group_layout.addWidget(log_area)
        log_group.setLayout(log_group_layout)

        log_layout.addWidget(log_group)
        log_container.setLayout(log_layout)

        return log_container

    def init_splitter(self):
        """初始化分割器"""
        for title in ["任务选择", "任务设置"]:
            group = QGroupBox(title)
            layout = QVBoxLayout()
            group.setLayout(layout)
            self.splitter.addWidget(group)

        # 设置 splitter 的大小比例
        self.splitter.setSizes([500, 500])
        self.splitter.setFixedHeight(400)

    def clear_right_layout(self):
        """清空右侧布局"""
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)


