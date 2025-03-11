from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PySide6.QtGui import QFont


class LogTab(QWidget):
    def __init__(self, device_config, parent=None):
        super().__init__(parent)
        self.device_config = device_config
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        log_label = QLabel("设备日志")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        log_label.setObjectName("sectionTitle")
        self.layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("logTextEdit")
        self.log_text.setText(
            f"""11:45:14
{self.device_config.device_name}
启动成功
19:19:10
{self.device_config.device_name} 运行正常, 这是一
长的日志信息, 用于测试SiLogItem组
动操行和显示效果。查看多行日志是
确显示和滚动。
00:00:00
{self.device_config.device_name}
检测到异常
"""
        )
        self.layout.addWidget(self.log_text)
