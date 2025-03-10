from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QPushButton, \
    QHeaderView


class DownloadPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 页面标题
        title_label = QLabel("资源下载")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # 下载信息面板
        download_frame = QFrame()
        download_frame.setFrameShape(QFrame.StyledPanel)
        download_layout = QVBoxLayout(download_frame)

        # 可用资源表
        resources_label = QLabel("可用资源")
        resources_label.setFont(QFont("Arial", 14, QFont.Bold))
        resources_label.setObjectName("sectionTitle")
        download_layout.addWidget(resources_label)

        resources_table = QTableWidget(6, 4)
        resources_table.setHorizontalHeaderLabels(["资源名称", "版本", "大小", "操作"])
        resources_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        resources_table.verticalHeader().setVisible(False)

        resources = [
            ("雷电模拟器", "9.0.33", "500MB", "下载"),
            ("夜神模拟器", "7.0.5", "450MB", "下载"),
            ("MuMu模拟器", "12.0", "600MB", "下载"),
            ("阴阳师", "3.5.0", "2.1GB", "下载"),
            ("战双", "2.7.0", "3.5GB", "下载"),
            ("原神", "4.0.0", "15GB", "下载")
        ]
        for row, (name, version, size, action) in enumerate(resources):
            resources_table.setItem(row, 0, QTableWidgetItem(name))
            resources_table.setItem(row, 1, QTableWidgetItem(version))
            resources_table.setItem(row, 2, QTableWidgetItem(size))
            download_btn = QPushButton(action)
            resources_table.setCellWidget(row, 3, download_btn)
        download_layout.addWidget(resources_table)

        # 下载队列表
        queue_label = QLabel("下载队列")
        queue_label.setFont(QFont("Arial", 14, QFont.Bold))
        queue_label.setObjectName("sectionTitle")
        download_layout.addWidget(queue_label)

        queue_table = QTableWidget(2, 4)
        queue_table.setHorizontalHeaderLabels(["资源名称", "进度", "速度", "操作"])
        queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        queue_table.verticalHeader().setVisible(False)

        queue_items = [
            ("原神", "45%", "5.2MB/s", "暂停"),
            ("阴阳师", "12%", "3.8MB/s", "暂停")
        ]
        for row, (name, progress, speed, action) in enumerate(queue_items):
            queue_table.setItem(row, 0, QTableWidgetItem(name))
            queue_table.setItem(row, 1, QTableWidgetItem(progress))
            queue_table.setItem(row, 2, QTableWidgetItem(speed))
            action_btn = QPushButton(action)
            queue_table.setCellWidget(row, 3, action_btn)
        download_layout.addWidget(queue_table)

        layout.addWidget(download_frame)
