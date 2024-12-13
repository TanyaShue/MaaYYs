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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 子容器标题栏
        header_frame = QFrame()
        header_frame.setFixedHeight(24)
        header_frame.setObjectName("LogSubHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 0, 8, 0)

        self.name_label = QLabel(self.name)
        self.name_label.setObjectName("LogSubTitle")
        header_layout.addWidget(self.name_label)

        layout.addWidget(header_frame)

        # 日志文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("LogSubText")
        layout.addWidget(self.log_text)

        # 设置固定总高度
        self.setFixedHeight(124)

    def add_log(self, _message):
        message = _message.get("message", "")
        level = _message.get("level", "INFO")
        time = _message.get("time", datetime.now().strftime("%H:%M:%S"))
        formatted_message = f"[{time}]: {message}"  # 修正：直接使用 message
        self.log_text.append(formatted_message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


class LogContainer(QWidget):
    # 类级别的常量
    HEADER_HEIGHT = 28
    SUB_CONTAINER_HEIGHT = 124

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = False
        self.width_animation = None
        self.min_width_animation = None
        self.setFixedWidth(0)
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)
        self.sub_containers = {}
        self.total_height = 0
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("LogContainer")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        self.title_frame = QFrame()
        self.title_frame.setFixedHeight(self.HEADER_HEIGHT)
        self.title_frame.setObjectName("LogHeader")
        title_layout = QHBoxLayout(self.title_frame)
        title_layout.setContentsMargins(8, 0, 8, 0)

        self.title_label = QLabel("任务日志")
        self.title_label.setObjectName("LogTitle")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        main_layout.addWidget(self.title_frame)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("LogScrollArea")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 日志容器
        self.log_container = QWidget()
        self.log_container.setObjectName("LogInnerContainer")
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setSpacing(0)
        self.log_layout.setContentsMargins(4, 4, 4, 4)
        self.log_layout.setAlignment(Qt.AlignTop)

        self.log_layout.addStretch()

        self.scroll_area.setWidget(self.log_container)
        main_layout.addWidget(self.scroll_area)

    # [Previous methods remain unchanged...]
    def toggle_visibility(self):
        if self.width_animation and self.width_animation.state() == QPropertyAnimation.Running:
            return

        target_width = 280 if not self.expanded else 0

        if not self.expanded:
            self.show_all_components()

        self.width_animation = QPropertyAnimation(self, b"maximumWidth")
        self.width_animation.setDuration(250)
        self.width_animation.setStartValue(self.width())
        self.width_animation.setEndValue(target_width)
        self.width_animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.min_width_animation = QPropertyAnimation(self, b"minimumWidth")
        self.min_width_animation.setDuration(250)
        self.min_width_animation.setStartValue(self.width())
        self.min_width_animation.setEndValue(target_width)
        self.min_width_animation.setEasingCurve(QEasingCurve.InOutCubic)

        if self.expanded:
            self.width_animation.finished.connect(self.hide_all_components)

        self.width_animation.start()
        self.min_width_animation.start()

        self.expanded = not self.expanded

    def adjust_container_heights(self):
        container_count = len(self.sub_containers)
        if container_count == 0:
            return

        available_height = self.height() - self.HEADER_HEIGHT - 8
        height_per_container = max(100, available_height // container_count)

        for container in self.sub_containers.values():
            container.setFixedHeight(height_per_container)
            text_height = height_per_container - 24
            container.log_text.setFixedHeight(text_height)

    def hide_all_components(self):
        self.title_label.hide()
        self.scroll_area.hide()
        self.title_frame.hide()
        for container in self.sub_containers.values():
            container.hide()

    def show_all_components(self):
        self.title_label.show()
        self.scroll_area.show()
        self.title_frame.show()
        for container in self.sub_containers.values():
            container.show()

    def get_or_create_sub_container(self, name):
        if name not in self.sub_containers:
            sub_container = LogSubContainer(name)
            self.sub_containers[name] = sub_container
            self.log_layout.insertWidget(self.log_layout.count() - 1, sub_container)
            if not self.expanded:
                sub_container.hide()
            self.adjust_container_heights()
        return self.sub_containers[name]

    def add_log(self, container_name, message):
        sub_container = self.get_or_create_sub_container(container_name)
        sub_container.add_log(message)