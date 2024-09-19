from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('设备管理')
        self.setMinimumSize(800, 600)  # 设置窗口最小大小

        # 创建主布局
        self.main_layout = QHBoxLayout(self)

        # 左侧导航栏
        self.left_nav_layout = QVBoxLayout()
        nav_buttons = ['首页', '阴阳师', '明日方舟', '程序3', '程序4']
        for btn_text in nav_buttons:
            button = QPushButton(btn_text)
            button.setFixedHeight(50)  # 固定按钮高度
            button.setFixedWidth(100)
            self.left_nav_layout.addWidget(button)
            button.clicked.connect(self.handle_nav_click)  # 添加点击事件
        self.left_nav_layout.addStretch()  # 增加伸缩空间，让按钮靠上排列
        self.main_layout.addLayout(self.left_nav_layout)

        # 右侧页面内容区域
        self.right_layout = QVBoxLayout()
        self.table = None

        # 初始页面为首页
        self.init_home_page()

        self.setLayout(self.main_layout)

    def init_home_page(self):
        """初始化首页页面"""
        # 清空右侧布局
        self.clear_right_layout()

        # 创建标题
        title = QLabel('首页')
        title.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(title)

        # 创建设备表格
        self.table = QTableWidget(4, 6)
        self.table.setHorizontalHeaderLabels(['名称', '自动化程序名称', 'adb地址', 'adb端口', '运行状态', '操作'])

        # 添加数据到表格中
        devices = ['阴阳师1', '阴阳师2', '阴阳师3', '阴阳师4']
        for row, device_name in enumerate(devices):
            self.table.setItem(row, 0, QTableWidgetItem(device_name))
            self.table.setItem(row, 1, QTableWidgetItem('阴阳师'))
            self.table.setItem(row, 2, QTableWidgetItem('xxxx'))
            self.table.setItem(row, 3, QTableWidgetItem('xxxx'))
            self.table.setItem(row, 4, QTableWidgetItem('正在执行'))

            # 添加操作按钮
            button = QPushButton('查看详情')
            button.clicked.connect(lambda _, d=device_name: self.show_device_details(d))  # 绑定事件并传递设备名称
            self.table.setCellWidget(row, 5, button)

        self.right_layout.addWidget(self.table)

        # 设置详细信息的最小高度
        self.detail_container = QWidget()
        self.detail_container.setMinimumHeight(400)
        self.detail_layout = QHBoxLayout(self.detail_container)

        # 初始化为空
        self.detail_layout.addWidget(QLabel("选择设备以查看详情..."))

        self.right_layout.addWidget(self.detail_container)

        self.main_layout.addLayout(self.right_layout)

    def clear_right_layout(self):
        """清空右侧布局中的内容"""
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

    def show_device_details(self, device_name):
        """在下方展示设备详情，而不是跳转页面"""
        # 清空详细信息区域
        for i in reversed(range(self.detail_layout.count())):
            widget = self.detail_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # 左侧：任务选择
        task_selection = QGroupBox("任务选择")
        task_layout = QVBoxLayout()
        task_list = ['任务1', '任务2', '任务3']
        for task in task_list:
            task_row = QHBoxLayout()

            # 添加复选框
            checkbox = QCheckBox(task)
            task_row.addWidget(checkbox)

            # 添加设置按钮
            set_button = QPushButton('设置')
            set_button.clicked.connect(lambda _, t=task: self.set_task_parameters(t))
            task_row.addWidget(set_button)

            task_layout.addLayout(task_row)
        task_selection.setLayout(task_layout)

        # 中间：任务设置
        self.task_settings_group = QGroupBox("任务设置")
        self.settings_layout = QVBoxLayout()
        self.settings_layout.addWidget(QLabel(f"请选择任务以设置参数"))
        self.task_settings_group.setLayout(self.settings_layout)

        # 右侧：任务日志
        task_log = QGroupBox("任务日志")
        log_layout = QVBoxLayout()
        log_area = QTextEdit()
        log_area.setPlaceholderText("日志输出...")
        log_layout.addWidget(log_area)
        task_log.setLayout(log_layout)

        # 将三部分添加到详细信息布局
        self.detail_layout.addWidget(task_selection)
        self.detail_layout.addWidget(self.task_settings_group)
        self.detail_layout.addWidget(task_log)

    def set_task_parameters(self, task_name):
        """设置任务参数"""
        # 清空任务设置区域
        for i in reversed(range(self.settings_layout.count())):
            widget = self.settings_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # 更新任务设置区域的内容
        # self.settings_layout.addWidget(QLabel(f"设置 {task_name} 的参数"))
        self.settings_layout.addWidget(QLineEdit(f"{task_name} 参数1"))
        self.settings_layout.addWidget(QLineEdit(f"{task_name} 参数2"))
        self.settings_layout.addWidget(QLineEdit(f"{task_name} 参数3"))

    def handle_nav_click(self):
        """处理左侧导航栏按钮点击事件"""
        button = self.sender()
        page_name = button.text()

        if page_name == '首页':
            self.init_home_page()
        else:
            self.show_device_details(page_name)


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
