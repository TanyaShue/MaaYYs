# -*- coding: UTF-8 -*-
from PySide6.QtWidgets import (
    QHBoxLayout, QGroupBox,
     QTableWidget, QTextEdit,
    QSplitter, QHeaderView, QWidget, QVBoxLayout, QPushButton, QLabel,
     QSizePolicy
)

from .containers.add_project_dialog import AddProjectDialog
from .core.task_project_manager import TaskProjectManager, _get_project_key
from .ui_controller import UIController
from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtGui import QFont, QIcon
from .containers import LogContainer, NavigationBar

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.nav_bar = None
        self.thread_pool = QThreadPool()
        self.controller = UIController(self.thread_pool)
        self.task_project_manager = TaskProjectManager()

        self.setWindowTitle('MaaYYs')
        self.setMinimumSize(1280, 720)

        # 加载样式
        self.controller.load_styles(self)

        # 创建主布局
        self.main_layout = QHBoxLayout(self)

        # 左侧导航栏
        self.left_nav_widget = self.init_navigation_bar()

        # 中间内容区域
        self.center_content = self.init_center_content()

        # 右侧日志容器
        self.log_container = self.init_log_container()
        # 启动日志线程
        self._start_log_thread()
        self.task_project_manager.start_monitoring()

        # 添加项目对话框
        self.add_project_dialog = AddProjectDialog(self.thread_pool,self)
        self.add_project_dialog.projectAdded.connect(self.on_project_added)

        # 设置布局
        self.main_layout.addWidget(self.left_nav_widget)
        self.main_layout.addWidget(self.center_content)
        self.main_layout.addWidget(self.log_container)

        self.setLayout(self.main_layout)

    def _start_log_thread(self):
        """启动日志线程，每秒获取一次日志"""
        self.log_timer = QTimer(self)  # 使用 QTimer 每秒触发
        self.log_timer.timeout.connect(self._fetch_and_print_log)
        self.log_timer.start(1000)  # 每 1000 毫秒触发

    def _fetch_and_print_log(self):
        """获取并打印日志，同时将已处理的日志条目删除"""
        try:
            log_data = self.task_project_manager.get_log()  # 获取日志数据
            for project_key, logs in list(log_data.items()):  # 使用 list 包装 keys 以支持在迭代时修改原始字典
                print(f"项目 {project_key} 的日志:")
                for project in self.controller.projects.projects:
                    if project_key == _get_project_key(project):  # 匹配项目
                        print(f"项目名称：{project.project_name}")
                        for log_entry in logs:
                            # 添加日志到日志容器
                            self.log_container.add_log(project.project_name, log_entry)

                        # 删除已处理的日志
                        del log_data[project_key]
        except Exception as e:
            print(f"日志处理出错: {e}")

    def show_add_project_dialog(self):
        self.add_project_dialog.show_dialog()

    def on_project_added(self, name, program, selected):
        print(f"添加了新项目: {name}, 程序: {program}, 选择: {selected.get('name', '')}")
        self.controller.add_project(name, program, selected)
        self.controller.load_device_table(self.table, self.details_container_splitter, self.info_title)

    def init_navigation_bar(self):
        """初始化导航栏"""
        self.nav_bar = NavigationBar()
        self.main_layout.addWidget(self.nav_bar)
        return self.nav_bar

    def init_center_content(self):
        """初始化中间内容区域，包括首页内容和分割器"""
        center_widget = QWidget()
        self.center_layout = QVBoxLayout(center_widget)
        self.center_layout.setSpacing(5)
        self.center_layout.setContentsMargins(10, 10, 10, 10)

        # 初始化首页内容
        self.init_home_page()

        return center_widget

    def init_home_page(self):
        """初始化首页"""
        # 创建首页内容部分
        home_widget = QWidget()
        home_layout = QVBoxLayout(home_widget)
        home_layout.setSpacing(5)
        home_layout.setContentsMargins(0, 0, 0, 0)

        # 添加内容
        title_container = self._create_title_section()
        table_container = self._create_table_section()
        info_title_container = self._create_info_title_section()
        details_container = self._create_details_section()

        home_layout.addWidget(title_container)
        home_layout.addWidget(table_container)
        home_layout.addWidget(info_title_container)
        home_layout.addWidget(details_container)

        # 加载设备表格
        self.controller.load_device_table(self.table, self.details_container_splitter, self.info_title)

        self.center_layout.addWidget(home_widget)

    def init_log_container(self):
        """初始化右侧日志容器"""
        self.log_container = LogContainer()
        return self.log_container

    def toggle_log_container(self):
        """切换日志容器的显示和隐藏"""
        print("切换日志容器的显示和隐藏")
        self.log_container.toggle_visibility()  # 使用 LogContainer 中的动画效果

    def _create_title_section(self):
        """创建标题部分"""
        title_container = QWidget()
        title_container.setFixedHeight(30)

        # 使用 QHBoxLayout 使标题居中、按钮在右侧
        title_layout = QHBoxLayout(title_container)
        title_layout.setSpacing(0)
        title_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标题
        title = QLabel('首页')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setStyleSheet("color: #2980b9;")
        title.setFixedHeight(25)

        # 创建“日志”按钮并设置大小
        log_button = QPushButton()
        log_button.setIcon(QIcon('assets/icons/svg_icons/icon_menu_close.svg'))
        log_button.setFixedWidth(100)
        log_button.setFixedHeight(30)  # 调整为适合的高度
        log_button.setObjectName('infoButton')
        log_button.clicked.connect(self.toggle_log_container)  # 连接点击事件

        # 创建“日志”按钮并设置大小
        add_project_button = QPushButton()
        add_project_button.setIcon(QIcon('assets/icons/svg_icons/icon_add_user.svg'))
        add_project_button.setFixedWidth(100)
        add_project_button.setFixedHeight(30)  # 调整为适合的高度
        add_project_button.setObjectName('infoButton')
        add_project_button.clicked.connect(self.show_add_project_dialog)  # 连接点击事件


        # 添加占位符，使标题居中
        title_layout.addStretch()
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 将“日志”按钮放在最右侧
        title_layout.addWidget(add_project_button)
        title_layout.addWidget(log_button)
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
        details_layout = QHBoxLayout(details_container)
        details_layout.setSpacing(0)
        details_layout.setContentsMargins(0, 0, 0, 0)

        # 初始化并添加分割器
        self.details_container_splitter = self.init_splitter(details_container.width())
        details_layout.addWidget(self.details_container_splitter)

        # 设置容器高度
        details_container.setFixedHeight(400)
        # 设置背景为蓝色
        # details_container.setStyleSheet("background-color: #2980b9;")

        return details_container

    def init_splitter(self, container_width):
        """初始化分割器"""
        # 创建 QSplitter 实例
        details_container_splitter = QSplitter(Qt.Horizontal)
        details_container_splitter.setFixedWidth(container_width)

        for title in ["任务选择", "任务设置"]:
            group = QGroupBox(title)
            layout = QVBoxLayout()
            group.setLayout(layout)
            group.setFixedWidth(400)
            details_container_splitter.addWidget(group)

        # 设置大小比例,使每个 QGroupBox 位于各自分割器的中间
        details_container_splitter.setSizes([container_width // 2, container_width // 2])
        details_container_splitter.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        return details_container_splitter