from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
                               QFrame, QScrollArea, QCheckBox, QLabel, QLineEdit, QSplitter, QTabWidget, QGroupBox)
from PySide6.QtCore import Qt
from qasync import QEventLoop  # 引入 qasync
import asyncio
import threading

from utils.config import load_default_config  # 导入配置模块
from utils.common import load_tasks_from_pipeline
from utils.logger import Logger  # 导入全局 Logger 单例
from tasks import TaskManager, MaaInstanceSingleton


class AppUI(QWidget):
    def __init__(self):
        super().__init__()
        self.adb_port_entry = None
        self.adb_path_entry = None
        self.logger = Logger()  # 全局 Logger 实例
        self.checkbox_vars = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MaaYYs")
        self.setGeometry(100, 100, 1000, 600)

        main_layout = QVBoxLayout(self)

        # 标签页
        tab_widget = QTabWidget(self)
        main_layout.addWidget(tab_widget)

        # 初始化 "开始" 和 "设置" 标签页
        self.create_start_tab(tab_widget)
        self.create_settings_tab(tab_widget)

    def create_start_tab(self, tab_widget):
        start_tab = QWidget()
        tab_widget.addTab(start_tab, "开始")

        start_layout = QHBoxLayout(start_tab)
        splitter = QSplitter(Qt.Horizontal)
        start_layout.addWidget(splitter)

        # 左侧部分
        left_frame = self.create_adb_settings_frame()
        splitter.addWidget(left_frame)

        # 中间部分
        middle_frame = self.create_task_selection_frame()
        splitter.addWidget(middle_frame)

        # 右侧部分
        right_frame = self.create_log_output_frame()
        splitter.addWidget(right_frame)

    def create_adb_settings_frame(self):
        frame = QFrame(self)
        layout = QVBoxLayout()

        adb_group = QGroupBox("ADB 设置")
        adb_layout = QVBoxLayout(adb_group)

        adb_layout.addWidget(QLabel("ADB 路径"))
        self.adb_path_entry = QLineEdit()
        adb_layout.addWidget(self.adb_path_entry)

        adb_layout.addWidget(QLabel("ADB 端口"))
        self.adb_port_entry = QLineEdit()
        adb_layout.addWidget(self.adb_port_entry)

        # 加载默认配置
        config = load_default_config()
        self.adb_path_entry.setText(config.get("adb_path", ""))
        self.adb_port_entry.setText(config.get("adb_port", ""))

        connect_button = self.create_button("连接", self.connect)
        adb_layout.addWidget(connect_button, alignment=Qt.AlignCenter)

        layout.addWidget(adb_group, alignment=Qt.AlignTop)
        frame.setLayout(layout)
        return frame

    def create_task_selection_frame(self):
        frame = QFrame(self)
        layout = QVBoxLayout()

        task_group = QGroupBox("任务选择")
        task_layout = QVBoxLayout(task_group)
        task_group.setFixedHeight(300)

        scroll_area = QScrollArea(self)
        task_widget = QWidget()
        scroll_area.setWidget(task_widget)
        scroll_area.setWidgetResizable(True)
        task_widget_layout = QVBoxLayout(task_widget)

        tasks = load_tasks_from_pipeline("../assets/resource/base/pipeline")
        for task_name in tasks:
            checkbox = QCheckBox(task_name)
            task_widget_layout.addWidget(checkbox)
            self.checkbox_vars[task_name] = checkbox

        task_layout.addWidget(scroll_area)
        layout.addWidget(task_group)

        execute_button = self.create_button("执行", lambda: start_async_task(self.execute_selected_options()))
        layout.addWidget(execute_button, alignment=Qt.AlignCenter)

        frame.setLayout(layout)
        return frame

    def create_log_output_frame(self):
        frame = QFrame(self)
        layout = QVBoxLayout()

        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.logger.set_log_output(self.log_output)
        frame.setLayout(layout)
        return frame

    def create_settings_tab(self, tab_widget):
        settings_tab = QWidget()
        tab_widget.addTab(settings_tab, "设置")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("设置项 1"))
        layout.addWidget(QLineEdit())
        layout.addWidget(QLabel("设置项 2"))
        layout.addWidget(QLineEdit())

        settings_tab.setLayout(layout)

    def create_button(self, text, callback):
        button = QPushButton(text)
        button.setFixedSize(100, 30)
        button.clicked.connect(callback)
        return button

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

    async def execute_selected_options(self):
        selected_tasks = [task for task, checkbox in self.checkbox_vars.items() if checkbox.isChecked()]

        if not selected_tasks:
            self.logger.add_log("未选择任何任务")
            return

        for task in selected_tasks:
            instance = await MaaInstanceSingleton.get_instance(None, None)
            instance.post_task(task)
            self.logger.add_log(f"执行任务: {task}")


def start_async_task(task):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = QEventLoop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        asyncio.ensure_future(task)
    else:
        loop.run_until_complete(task)

