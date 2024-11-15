# -*- coding: UTF-8 -*-
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel,
    QTextEdit, QScrollArea, QHBoxLayout
)
from datetime import datetime


class LogSubContainer(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 子容器标题栏
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 4px; }")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)

        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.name_label)

        layout.addWidget(header_frame)

        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #ffffff;
            }
        """)
        layout.addWidget(self.log_text)

    def add_log(self, message):
        """添加日志条目"""
        timestamp = message.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        formatted_message = message.get("message", "")
        self.log_text.append(formatted_message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


class LogContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = False
        self.width_animation = None
        self.min_width_animation = None
        self.setFixedWidth(0)
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)
        self.sub_containers = {}  # 存储子日志容器
        self.setup_ui()

    def setup_ui(self):
        # 设置主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        self.title_frame = QFrame()
        self.title_frame.setStyleSheet("""
            QFrame { 
                background-color: #e0e0e0;
                border-left: 1px solid #ccc;
            }
        """)
        title_layout = QVBoxLayout(self.title_frame)
        title_layout.setContentsMargins(10, 10, 10, 10)
        title_layout.setSpacing(0)

        self.title_label = QLabel("任务日志")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(self.title_label)
        main_layout.addWidget(self.title_frame)

        # 使用QScrollArea包装日志区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
                border-left: 1px solid #ccc;
            }
        """)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 创建一个容器widget来存放所有子日志容器
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setSpacing(10)
        self.log_layout.setContentsMargins(10, 10, 10, 10)
        self.log_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.log_container)
        main_layout.addWidget(self.scroll_area)

        # 设置整体样式
        self.setStyleSheet("""
            LogContainer {
                background-color: #f5f5f5;
            }
        """)

        # 初始状态下设置为隐藏
        self.hide_all_components()

    def hide_all_components(self):
        """隐藏所有组件"""
        self.title_label.hide()
        self.scroll_area.hide()
        self.title_frame.hide()
        for container in self.sub_containers.values():
            container.hide()

    def show_all_components(self):
        """显示所有组件"""
        self.title_label.show()
        self.scroll_area.show()
        self.title_frame.show()
        for container in self.sub_containers.values():
            container.show()

    def toggle_visibility(self):
        """切换日志容器的可见性"""
        if self.width_animation and self.width_animation.state() == QPropertyAnimation.Running:
            return

        target_width = 400 if not self.expanded else 0

        # 如果要展开，先显示所有组件
        if not self.expanded:
            self.show_all_components()

        # 创建动画
        self.width_animation = QPropertyAnimation(self, b"maximumWidth")
        self.width_animation.setDuration(300)
        self.width_animation.setStartValue(self.width())
        self.width_animation.setEndValue(target_width)
        self.width_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # 同时设置最小宽度的动画
        self.min_width_animation = QPropertyAnimation(self, b"minimumWidth")
        self.min_width_animation.setDuration(300)
        self.min_width_animation.setStartValue(self.width())
        self.min_width_animation.setEndValue(target_width)
        self.min_width_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # 如果是收起动画，在动画结束时隐藏组件
        if self.expanded:
            self.width_animation.finished.connect(self.hide_all_components)

        # 开始动画
        self.width_animation.start()
        self.min_width_animation.start()

        self.expanded = not self.expanded

    def get_or_create_sub_container(self, name):
        """获取或创建子日志容器"""
        if name not in self.sub_containers:
            sub_container = LogSubContainer(name)
            self.sub_containers[name] = sub_container
            self.log_layout.addWidget(sub_container)
            if not self.expanded:
                sub_container.hide()
        return self.sub_containers[name]

    def add_log(self, container_name, message):
        """向指定的子日志容器添加日志"""
        sub_container = self.get_or_create_sub_container(container_name)
        sub_container.add_log(message)