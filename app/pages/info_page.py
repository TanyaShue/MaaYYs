from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class InfoPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 页面标题
        title_label = QLabel("软件信息")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # 信息面板
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QVBoxLayout(info_frame)

        # 软件名称
        software_title = QLabel("设备管理系统")
        software_title.setFont(QFont("Arial", 20, QFont.Bold))
        software_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(software_title)

        # 版本信息
        version_label = QLabel("版本: 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(version_label)

        # 软件描述
        description_text = QTextEdit()
        description_text.setReadOnly(True)
        description_text.setText(
            "设备管理系统是一款专为模拟器和游戏管理设计的工具软件。\n\n"
            "主要功能:\n"
            "• 一键管理多个模拟器实例\n"
            "• 监控模拟器运行状态\n"
            "• 便捷启动游戏资源\n"
            "• 自动检测异常情况\n"
            "• 资源下载与更新\n\n"
            "该软件基于PySide6开发，支持Windows 10/11系统。"
        )
        info_layout.addWidget(description_text)

        # 开发者信息
        developer_label = QLabel("开发: Example Development Team")
        developer_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(developer_label)

        # 版权信息
        copyright_label = QLabel("© 2025 版权所有")
        copyright_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(copyright_label)

        layout.addWidget(info_frame)
