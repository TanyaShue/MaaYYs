# -*- coding: UTF-8 -*-
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QTextEdit


class LogContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = False
        # 初始化时完全收起
        self.setFixedWidth(0)
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 10, 10, 10)
        title_layout.setSpacing(0)

        self.title_label = QLabel("任务日志")
        title_layout.addWidget(self.title_label)
        main_layout.addWidget(title_frame)

        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setPlaceholderText("日志输出...")
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        # 初始状态隐藏所有子组件
        self.title_label.hide()
        self.log_area.hide()

    def toggle_log_container(self):
        # 设置目标宽度
        target_width = 300 if not self.expanded else 0

        # 创建宽度动画
        self.width_anim = QPropertyAnimation(self, b"maximumWidth")
        self.width_anim.setDuration(300)
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(target_width)
        self.width_anim.setEasingCurve(QEasingCurve.OutCubic)

        # 同步最小宽度动画
        self.min_width_anim = QPropertyAnimation(self, b"minimumWidth")
        self.min_width_anim.setDuration(300)
        self.min_width_anim.setStartValue(self.width())
        self.min_width_anim.setEndValue(target_width)
        self.min_width_anim.setEasingCurve(QEasingCurve.OutCubic)

        # 切换展开状态
        self.expanded = not self.expanded

        # 根据展开状态显示/隐藏组件
        if self.expanded:
            self.title_label.show()
            self.log_area.show()
        else:
            # 在动画结束时隐藏组件
            self.width_anim.finished.connect(lambda: self.title_label.hide())
            self.width_anim.finished.connect(lambda: self.log_area.hide())

        # 启动动画
        self.width_anim.start()
        self.min_width_anim.start()