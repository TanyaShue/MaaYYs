# -*- coding: UTF-8 -*-
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QFrame, QStyle, QLabel, QScrollArea


class NavButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._full_text = text
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(text)

    def setText(self, text):
        self._full_text = text if text else self._full_text
        super().setText("")  # 默认不显示文本

    def showFullText(self, show=True):
        super().setText(self._full_text if show else "")


class NavigationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = False
        self.setFixedWidth(64)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部标题区域
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        self.menu_btn = NavButton("菜单")
        self.menu_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogHelpButton))
        self.menu_btn.setIconSize(QSize(22, 22))
        self.menu_btn.clicked.connect(self.toggle_navigation)
        title_layout.addWidget(self.menu_btn)

        self.title_label = QLabel("MaaYYs")
        self.title_label.hide()
        title_layout.addWidget(self.title_label)

        main_layout.addWidget(title_frame)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        nav_container = QWidget()
        self.nav_layout = QVBoxLayout(nav_container)
        self.nav_layout.setSpacing(2)
        self.nav_layout.setContentsMargins(0, 10, 0, 10)

        self.add_nav_button("首页", "SP_DialogOkButton")
        for program in ["阴阳师"]:
            self.add_nav_button(program, "SP_ComputerIcon")
        self.nav_layout.addStretch()
        self.add_nav_button("刷新资源", "SP_BrowserReload")

        scroll.setWidget(nav_container)
        main_layout.addWidget(scroll)

        # 存储按钮引用
        self.buttons = [
            widget for i in range(self.nav_layout.count())
            if isinstance(widget := self.nav_layout.itemAt(i).widget(), NavButton)
        ]

    def add_nav_button(self, text, icon_name):
        button = NavButton(text)
        icon = self.style().standardIcon(getattr(QStyle, icon_name))
        button.setIcon(icon)
        button.setIconSize(QSize(22, 22))
        button.clicked.connect(lambda: button.setChecked(False))
        self.nav_layout.addWidget(button)
        return button

    def toggle_navigation(self):
        target_width = 240 if not self.expanded else 64
        self.width_anim = QPropertyAnimation(self, b"minimumWidth")
        self.width_anim.setDuration(300)
        self.width_anim.setStartValue(self.width())
        self.width_anim.setEndValue(target_width)
        self.width_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.expanded = not self.expanded

        if self.expanded:
            self.title_label.show()
            for button in self.buttons:
                button.showFullText(True)
        else:
            self.title_label.hide()
            for button in self.buttons:
                button.showFullText(False)

        self.width_anim.start()
