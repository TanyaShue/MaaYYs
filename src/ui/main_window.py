from PySide6.QtWidgets import (
    QHBoxLayout, QGroupBox,
     QTableWidget, QTextEdit,
    QSplitter, QHeaderView, QWidget, QVBoxLayout, QPushButton, QLabel,
     QSizePolicy
)
from .ui_controller import UIController
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from .containers import LogContainer, NavigationBar

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.nav_bar = None
        self.controller = UIController()

        self.setWindowTitle('MaaYYs')
        self.setMinimumSize(1440, 720)

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

        # 设置布局
        self.main_layout.addWidget(self.left_nav_widget)
        self.main_layout.addWidget(self.center_content)
        self.main_layout.addWidget(self.log_container)

        self.setLayout(self.main_layout)

    def init_navigation_bar(self):
        """初始化导航栏"""
        self.nav_bar = NavigationBar()
        self.main_layout.addWidget(self.nav_bar)
        return self.nav_bar

    def init_center_content(self):
        """初始化中间内容区域，包括首页内容和分割器"""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setSpacing(5)
        center_layout.setContentsMargins(10, 10, 10, 10)

        # 初始化首页内容
        self.init_home_page(center_layout)

        return center_widget

    def init_home_page(self,center_layout):
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

        # self.details_container_splitter.addWidget(home_widget)
        # self.details_container_splitter.setSizes([800, 0])  # 设置默认宽度

        # 加载设备表格
        self.controller.load_device_table(self.table, self.details_container_splitter, self.info_title)

        center_layout.addWidget(home_widget)

    def init_log_container(self):
        """初始化右侧日志容器"""
        self.log_container = LogContainer()
        self.log_container.setFixedWidth(0)  # 初始化为隐藏状态
        return self.log_container

    def toggle_log_container(self):
        """切换日志容器的显示和隐藏"""
        target_width = 300 if self.log_container.width() == 0 else 0
        self.log_container.toggle_log_container()  # 使用 LogContainer 中的动画效果
        self.log_container.setFixedWidth(target_width)  # 切换固定宽度


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
        log_button = QPushButton('日志')
        log_button.setFixedWidth(100)
        log_button.setFixedHeight(30)  # 调整为适合的高度
        log_button.setObjectName('infoButton')
        log_button.clicked.connect(self.toggle_log_container)  # 连接点击事件

        # 添加占位符，使标题居中
        title_layout.addStretch()
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 将“日志”按钮放在最右侧
        title_layout.addWidget(log_button)

        return title_container

    # def toggle_log_container(self):
    #     """切换日志容器的显示和隐藏"""
    #     print("toggle_log_container")  # 用于调试
    #
    #     # 确保日志容器已添加到分割器
    #     if self.log_container not in [self.main_splitter.widget(i) for i in range(self.main_splitter.count())]:
    #         self.main_splitter.addWidget(self.log_container)
    #
    #     # 调用动画函数来控制显示和隐藏
    #     self.animate_log_container(show=not self.log_container.isVisible())

    # def animate_log_container(self, show=True):
    #     """使用 QPropertyAnimation 创建从右侧滑动的效果"""
    #     if self.log_animation:
    #         self.log_animation.stop()
    #
    #     log_container_width = 300
    #     main_splitter_width = self.main_splitter.width()
    #
    #     # 计算目标左侧宽度
    #     target_left_width = main_splitter_width - log_container_width if show else main_splitter_width
    #
    #     # 设置 log_container 的滑动动画
    #     slide_animation = QPropertyAnimation(self.log_container, b"geometry")
    #     slide_animation.setDuration(400)
    #
    #     # 获取当前位置
    #     current_geometry = self.log_container.geometry()
    #
    #     if show:
    #         # 从已设置好的起始位置开始动画
    #         start_rect = current_geometry
    #         end_rect = QRect(target_left_width, current_geometry.y(),
    #                          log_container_width, current_geometry.height())
    #     else:
    #         start_rect = current_geometry
    #         end_rect = QRect(main_splitter_width, current_geometry.y(),
    #                          log_container_width, current_geometry.height())
    #
    #     slide_animation.setStartValue(start_rect)
    #     slide_animation.setEndValue(end_rect)
    #     slide_animation.setEasingCurve(QEasingCurve.OutCubic)
    #
    #     # 设置 splitter 的大小动画
    #     sizes_animation = QPropertyAnimation(self.main_splitter, b"dummy_property")
    #     sizes_animation.setDuration(400)
    #     sizes_animation.setEasingCurve(QEasingCurve.OutCubic)
    #     sizes_animation.setStartValue(0.0)
    #     sizes_animation.setEndValue(1.0)
    #
    #     current_sizes = self.main_splitter.sizes()
    #     start_left = current_sizes[0]
    #
    #     # 在大小动画的过程中更新 splitter 的大小分布
    #     def update_splitter_sizes(progress):
    #         if show:
    #             # 显示时，左侧宽度逐渐减小
    #             left_width = int(start_left - (progress * log_container_width))
    #             right_width = int(progress * log_container_width)
    #         else:
    #             # 隐藏时，左侧宽度逐渐增加
    #             left_width = int(start_left + (progress * log_container_width))
    #             right_width = int((1 - progress) * log_container_width)
    #
    #         # 确保宽度和不超过 splitter 总宽度
    #         total_width = left_width + right_width
    #         if total_width > main_splitter_width:
    #             left_width = int(left_width * main_splitter_width / total_width)
    #             right_width = int(right_width * main_splitter_width / total_width)
    #
    #         self.main_splitter.setSizes([left_width, right_width])
    #
    #     sizes_animation.valueChanged.connect(update_splitter_sizes)
    #
    #     # 使用动画组
    #     self.log_animation = QParallelAnimationGroup()
    #     self.log_animation.addAnimation(slide_animation)
    #     self.log_animation.addAnimation(sizes_animation)
    #
    #     # 动画结束后的处理
    #     def on_animation_finished():
    #         if not show:
    #             self.log_container.setVisible(False)
    #             # 使用动画的最终状态，避免突变
    #             self.main_splitter.setSizes([main_splitter_width, 0])
    #         else:
    #             # 使用最终计算的值，避免突变
    #             self.log_container.setVisible(True)
    #             self.log_container.setGeometry(end_rect)
    #             self.main_splitter.setSizes([target_left_width, log_container_width])
    #
    #     self.log_animation.finished.connect(on_animation_finished)
    #     self.log_animation.start()
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

        # 初始化并添加分割器
        self.details_container_splitter = self.init_splitter()
        details_layout.addWidget(self.details_container_splitter)

        # 设置容器高度
        details_container.setFixedHeight(400)
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
        log_area.setMinimumWidth(180)  # 设置最小宽度

        log_group_layout.addWidget(log_area)
        log_layout.addWidget(log_group)

        # 设置大小策略
        log_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        # 设置固定宽度
        log_container.setFixedWidth(200)

        return log_container

    def init_splitter(self):
        """初始化分割器"""
        # 创建 QSplitter 实例
        details_container_splitter = QSplitter(Qt.Horizontal)

        for title in ["任务选择", "任务设置"]:
            group = QGroupBox(title)
            layout = QVBoxLayout()
            group.setLayout(layout)
            details_container_splitter.addWidget(group)

        # 设置大小比例
        details_container_splitter.setSizes([500, 500])
        details_container_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        return details_container_splitter

    def clear_right_layout(self):
        """清空右侧布局"""
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
