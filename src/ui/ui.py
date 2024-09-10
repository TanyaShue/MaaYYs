from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
                                QFrame, QScrollArea, QCheckBox, QLabel, QLineEdit, QSplitter, QTabWidget, QGroupBox)
from PySide6.QtCore import Qt
from qasync import QEventLoop
from utils.config import load_default_config, load_config_tasks, get_task_entry  # 导入配置模块
from utils.logger import Logger  # 导入全局 Logger 单例
from tasks import TaskManager, MaaInstanceSingleton

  # 引入 qasync
import asyncio
import threading

from PySide6.QtCore import QThread, Signal

class Worker(QThread):
    log_signal = Signal(str)  # 用于发出日志消息的信号
    finished_signal = Signal()  # 用于任务完成的信号

    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        loop = asyncio.new_event_loop()  # 创建一个新的事件循环
        asyncio.set_event_loop(loop)  # 设置事件循环为当前线程的事件循环

        try:
            result = loop.run_until_complete(self.task_func(*self.args, **self.kwargs))  # 执行协程
            self.log_signal.emit(result)
        except Exception as e:
            self.log_signal.emit(f"任务执行失败: {str(e)}")
        finally:
            loop.close()
            self.finished_signal.emit()



class AppUI(QWidget):
    def __init__(self):
        super().__init__()
        self.log_output = None
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

        connect_button = self.create_button("连接", self.adb_connect)
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

        tasks = load_config_tasks()
        for task_name in tasks:
            checkbox = QCheckBox(task_name)
            task_widget_layout.addWidget(checkbox)
            self.checkbox_vars[task_name] = checkbox

        task_layout.addWidget(scroll_area)
        layout.addWidget(task_group)
        self.task_running = False

        # 将 execute_button 赋值给 self.execute_button
        self.execute_button = self.create_button("执行", self.on_execute_button_clicked)
        layout.addWidget(self.execute_button, alignment=Qt.AlignCenter)
        
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

    def adb_connect(self):
        adb_path = self.adb_path_entry.text()
        adb_port = self.adb_port_entry.text()

        self.logger.add_log(f"ADB路径: {adb_path}")
        self.logger.add_log(f"ADB端口: {adb_port}")
        self.logger.add_log("正在连接...")

        self.adb_worker = Worker(self.run_adb_task, adb_path, adb_port)
        self.adb_worker.log_signal.connect(self.logger.add_log)
        self.adb_worker.finished_signal.connect(self.on_adb_task_finished)
        self.adb_worker.start()

    async def run_adb_task(self, adb_path, adb_port):
        try:
            await TaskManager.main(adb_path, adb_port)  # 运行协程
            return "ADB 连接成功"
        except Exception as e:
            return f"ADB 连接失败: {str(e)}"


    def on_adb_task_finished(self):
        self.logger.add_log("ADB 任务结束")


    async def run_async_task(self, adb_path, adb_port):
        try:
            await TaskManager.main(adb_path, adb_port)
            self.logger.add_log("ADB 连接成功")
        except Exception as e:
            self.logger.add_log(f"ADB 连接失败: {str(e)}")

    def on_execute_button_clicked(self):
        if not self.task_running:
            self.task_running = True
            self.execute_button.setText("停止")

            self.task_worker = Worker(self.run_task_worker)
            self.task_worker.log_signal.connect(self.logger.add_log)
            self.task_worker.finished_signal.connect(self.on_task_finished)
            self.task_worker.start()
        else:
            self.task_running = False
            self.task_worker = Worker(self.stop_task_worker)
            self.task_worker.log_signal.connect(self.logger.add_log)
            self.task_worker.finished_signal.connect(self.on_task_finished)
            self.task_worker.start()
            self.logger.add_log("任务已停止")
            self.execute_button.setText("执行")

    async def run_task_worker(self):
        selected_tasks = [task for task, checkbox in self.checkbox_vars.items() if checkbox.isChecked()]

        if not selected_tasks:
            return "未选择任何任务"

        instance = await MaaInstanceSingleton.get_instance(None, None)  # 异步获取实例

        for task in selected_tasks:
            if not self.task_running:
                break
            await instance.run_task(get_task_entry(task))  # 异步运行任务

        return "任务执行完成"

    async def stop_task_worker(self):
        
        print("stop_task_worker")
        instance = await MaaInstanceSingleton.get_instance(None, None)  # 异步获取实例
        await instance.stop()

        return "任务执行完成"


    def on_task_finished(self):
        self.task_running = False
        self.execute_button.setText("执行")
        self.logger.add_log("所有任务执行完成")


    
