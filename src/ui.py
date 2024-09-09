from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
                               QFrame, QScrollArea, QCheckBox, QLabel, QLineEdit, QSplitter, QTabWidget, QGroupBox)
from PySide6.QtCore import Qt
from utils.config import load_default_config  # 导入配置模块
from utils.common import load_tasks_from_pipeline
from utils.logger import Logger  # 导入全局 Logger 单例
import asyncio
import threading
from tasks import TaskManager

class AppUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger()  # 获取全局 Logger 实例
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MaaYYs")
        self.setGeometry(100, 100, 1000, 600)

        # 主布局
        main_layout = QVBoxLayout(self)

        # 创建标签页
        tab_widget = QTabWidget(self)
        main_layout.addWidget(tab_widget)

        # 创建 "开始" 标签页
        start_tab = QWidget()
        tab_widget.addTab(start_tab, "开始")
        self.init_start_tab(start_tab)

        # 创建 "设置" 标签页
        settings_tab = QWidget()
        tab_widget.addTab(settings_tab, "设置")
        self.init_settings_tab(settings_tab)

    def init_start_tab(self, tab):
        # "开始" 标签页的布局
        start_layout = QHBoxLayout(tab)

        # 使用 QSplitter 分割布局
        splitter = QSplitter(Qt.Horizontal)
        start_layout.addWidget(splitter)

        # 左侧部分：ADB 设置和连接按钮
        left_frame = QFrame(self)
        left_layout = QVBoxLayout()

        # 使用 QGroupBox 分组并限制高度
        adb_group = QGroupBox("ADB 设置")
        adb_layout = QVBoxLayout(adb_group)

        adb_path_label = QLabel("ADB 路径")
        adb_layout.addWidget(adb_path_label)

        self.adb_path_entry = QLineEdit()
        adb_layout.addWidget(self.adb_path_entry)

        adb_port_label = QLabel("ADB 端口")
        adb_layout.addWidget(adb_port_label)

        self.adb_port_entry = QLineEdit()
        adb_layout.addWidget(self.adb_port_entry)

        config = load_default_config()
        self.adb_path_entry.setText(config.get("adb_path", ""))
        self.adb_port_entry.setText(config.get("adb_port", ""))

        connect_button = QPushButton("连接")
        connect_button.setFixedSize(100, 30)  # 设置固定大小
        connect_button.clicked.connect(self.connect)
        adb_layout.addWidget(connect_button, alignment=Qt.AlignCenter)  # 居中按钮

        left_layout.addWidget(adb_group, alignment=Qt.AlignTop)  # 将 ADB 设置靠上
        left_frame.setLayout(left_layout)
        splitter.addWidget(left_frame)

        # 中间部分：任务选择和执行按钮
        middle_frame = QFrame(self)
        middle_layout = QVBoxLayout()

        # 使用 QGroupBox 分组并限制高度
        task_group = QGroupBox("任务选择")
        task_layout = QVBoxLayout(task_group)
        task_group.setFixedHeight(300)  # 限制任务选择部分的高度

        scroll_area = QScrollArea(self)
        task_widget = QWidget()
        scroll_area.setWidget(task_widget)
        scroll_area.setWidgetResizable(True)
        task_widget_layout = QVBoxLayout(task_widget)

        tasks = load_tasks_from_pipeline("assets/resource/base/pipeline")
        self.checkbox_vars = {}

        for task_name in tasks:
            checkbox = QCheckBox(task_name)
            task_widget_layout.addWidget(checkbox)
            self.checkbox_vars[task_name] = checkbox

        task_layout.addWidget(scroll_area)
        middle_layout.addWidget(task_group)

        execute_button = QPushButton("执行")
        execute_button.setFixedSize(100, 30)  # 设置固定大小
        execute_button.clicked.connect(lambda: threading.Thread(target=self.execute_selected_options).start())
        middle_layout.addWidget(execute_button, alignment=Qt.AlignCenter)  # 居中按钮

        middle_frame.setLayout(middle_layout)
        splitter.addWidget(middle_frame)

        # 右侧部分：日志输出窗口（不限制高度）
        right_frame = QFrame(self)
        right_layout = QVBoxLayout()

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        right_layout.addWidget(self.log_output)

        self.logger.set_log_output(self.log_output)
        right_frame.setLayout(right_layout)
        splitter.addWidget(right_frame)

    def init_settings_tab(self, tab):
        # "设置" 标签页的布局
        settings_layout = QVBoxLayout()

        # 示例设置项
        settings_layout.addWidget(QLabel("设置项 1"))
        settings_layout.addWidget(QLineEdit())

        settings_layout.addWidget(QLabel("设置项 2"))
        settings_layout.addWidget(QLineEdit())

        tab.setLayout(settings_layout)

    def connect(self):
        adb_path = self.adb_path_entry.text()
        adb_port = self.adb_port_entry.text()

        self.logger.add_log(f"ADB路径: {adb_path}")
        self.logger.add_log(f"ADB端口: {adb_port}")
        self.logger.add_log("正在连接...")

        # 使用线程启动异步任务
        threading.Thread(target=self.run_async_task, args=(adb_path, adb_port)).start()

    def run_async_task(self, adb_path, adb_port):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(TaskManager.main(adb_path, adb_port))

    def execute_selected_options(self):
        selected_tasks = [task for task, checkbox in self.checkbox_vars.items() if checkbox.isChecked()]

        if not selected_tasks:
            self.logger.add_log("未选择任何任务")
            return

        self.logger.add_log(f"执行任务: {selected_tasks}")
        asyncio.run(TaskManager().test())

if __name__ == "__main__":
    app = QApplication([])
    ui = AppUI()
    ui.show()
    app.exec()
