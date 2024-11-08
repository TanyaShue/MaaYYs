# -*- coding: UTF-8 -*-
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QTextEdit


class LogContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = False
        self.setMinimumWidth(0)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 10, 10, 10)
        title_layout.setSpacing(0)

        self.title_label = QLabel("任务日志")
        title_layout.addWidget(self.title_label)
        main_layout.addWidget(title_frame)

        log_area = QTextEdit()
        log_area.setPlaceholderText("日志输出...")
        log_area.setReadOnly(True)
        main_layout.addWidget(log_area)

    def toggle_log_container(self):
        target_width = 300 if not self.expanded else 0
        self.width_anim = QPropertyAnimation(self, b"minimumWidth")
        self.width_anim.setDuration(300)
        self.width_anim.setStartValue(self.minimumWidth())
        self.width_anim.setEndValue(target_width)
        self.width_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.expanded = not self.expanded
        self.width_anim.start()