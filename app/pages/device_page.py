from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
                               QFrame, QTableWidget, QTableWidgetItem,
                               QHeaderView, QWidget, QMessageBox)

from app.models.config.global_config import global_config
from app.pages.device_detail_page import DeviceDetailPage


class DeviceListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = global_config
        self.device_detail_page = None
        self.init_ui()
        self.load_config_data()

    def init_ui(self):
        """初始化UI组件"""
        layout = QVBoxLayout(self)

        # 页面标题
        title_label = QLabel("设备信息")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # 设备信息面板
        self.devices_frame = QFrame()
        self.devices_frame.setFrameShape(QFrame.StyledPanel)
        self.devices_frame.setObjectName("devicesFrame")
        devices_layout = QVBoxLayout(self.devices_frame)
        devices_layout.setContentsMargins(15, 15, 15, 15)

        # 设备列表标题
        devices_label = QLabel("设备列表")
        devices_label.setFont(QFont("Arial", 14, QFont.Bold))
        devices_label.setObjectName("sectionTitle")
        devices_layout.addWidget(devices_label)

        # 设备表格
        self.device_table = QTableWidget()
        self.device_table.setObjectName("deviceTable")
        self.device_table.setColumnCount(6)
        self.device_table.setHorizontalHeaderLabels(["设备名称", "类型", "状态", "ADB地址", "计划任务", "操作"])
        self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.device_table.verticalHeader().setVisible(False)
        self.device_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.device_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.device_table.setAlternatingRowColors(True)
        devices_layout.addWidget(self.device_table)

        layout.addWidget(self.devices_frame)

        # 初始化设备详情页面（隐藏状态）
        self.device_detail_page = DeviceDetailPage()
        self.device_detail_page.back_signal.connect(self.show_device_list)
        layout.addWidget(self.device_detail_page)
        self.device_detail_page.hide()

    def load_config_data(self):
        """加载配置数据"""
        try:
            self.populate_device_table()
        except Exception as e:
            print(f"Error loading config files: {e}")
            QMessageBox.critical(self, "加载失败", f"加载配置文件失败: {e}")

    def populate_device_table(self):
        """填充设备表格"""
        # 清空现有表格内容
        self.device_table.clearContents()
        self.device_table.setRowCount(0)

        try:
            devices = self.global_config.get_devices_config().devices
            self.device_table.setRowCount(len(devices))

            for row, device in enumerate(devices):
                # 设备名称
                self.device_table.setItem(row, 0, QTableWidgetItem(device.device_name))

                # 设备类型
                self.device_table.setItem(row, 1, QTableWidgetItem(device.adb_config.name))

                # 状态（带颜色指示器）
                status_widget = QWidget()
                status_layout = QHBoxLayout(status_widget)
                status_layout.setContentsMargins(5, 2, 5, 2)

                status_text = "运行正常" if device.schedule_enabled else "未启用计划任务"
                status_color = "#4CAF50" if device.schedule_enabled else "#F44336"

                status_indicator = QLabel()
                status_indicator.setFixedSize(10, 10)
                status_indicator.setStyleSheet(f"background-color: {status_color}; border-radius: 5px;")

                status_label = QLabel(status_text)

                status_layout.addWidget(status_indicator)
                status_layout.addWidget(status_label)
                status_layout.addStretch()

                self.device_table.setCellWidget(row, 2, status_widget)

                # ADB地址
                self.device_table.setItem(row, 3, QTableWidgetItem(device.adb_config.address))

                # 计划任务
                plan_status = "已启用" if device.schedule_enabled else "未启用"
                self.device_table.setItem(row, 4, QTableWidgetItem(plan_status))

                # 操作按钮
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 2, 5, 2)

                view_btn = QPushButton("查看")
                view_btn.setObjectName("viewButton")
                view_btn.setFixedWidth(80)
                view_btn.clicked.connect(lambda checked, name=device.device_name: self.show_device_detail(name))

                action_layout.addWidget(view_btn)
                action_layout.addStretch()

                self.device_table.setCellWidget(row, 5, action_widget)

            # 调整行高
            for row in range(self.device_table.rowCount()):
                self.device_table.setRowHeight(row, 40)

        except Exception as e:
            print(f"Error populating device table: {e}")
            QMessageBox.critical(self, "错误", f"填充设备表格失败: {e}")

    def show_device_detail(self, device_name):
        """显示设备详情页面"""
        device_config = self.global_config.get_device_config(device_name)
        if not device_config:
            QMessageBox.warning(self, "错误", f"设备 '{device_name}' 未找到")
            return

        # 隐藏设备列表，显示详情页面
        self.devices_frame.hide()
        self.device_detail_page.set_device_config(device_config)
        self.device_detail_page.show()

    def show_device_list(self):
        """显示设备列表页面"""
        self.device_detail_page.hide()
        self.devices_frame.show()
        # 刷新设备列表
        self.populate_device_table()

    def refresh_device_list(self):
        """刷新设备列表"""
        self.populate_device_table()