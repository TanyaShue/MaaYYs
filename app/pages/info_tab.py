from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtGui import QFont


class InfoTab(QWidget):
    def __init__(self, device_config, parent=None):
        super().__init__(parent)
        self.device_config = device_config
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # 基本信息标题
        info_title = QLabel("基本信息")
        info_title.setFont(QFont("Arial", 12, QFont.Bold))
        info_title.setObjectName("sectionTitle")
        self.layout.addWidget(info_title)

        # 基本信息表格
        self.info_table = QTableWidget(6, 2)
        self.info_table.setObjectName("infoTable")
        self.info_table.setHorizontalHeaderLabels(["属性", "值"])
        self.info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.info_table.setAlternatingRowColors(True)
        self.info_table.setFrameShape(QTableWidget.NoFrame)

        info_items = [
            ("设备名称", self.device_config.device_name),
            ("设备类型", self.device_config.adb_config.name),
            ("ADB路径", self.device_config.adb_config.adb_path),
            ("ADB地址", self.device_config.adb_config.address),
            ("计划任务", "已启用" if self.device_config.schedule_enabled else "未启用"),
            ("启动命令", self.device_config.start_command or "无")
        ]

        for row, (key, value) in enumerate(info_items):
            self.info_table.setItem(row, 0, QTableWidgetItem(key))
            self.info_table.setItem(row, 1, QTableWidgetItem(value))
            self.info_table.setRowHeight(row, 35)

        self.layout.addWidget(self.info_table)
        self.layout.addStretch()
