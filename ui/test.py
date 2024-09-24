import logging
import threading

from maa.library import Library
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QCheckBox, QSplitter, QSizePolicy, QHeaderView
)
from PySide6.QtCore import Qt, QRunnable, Slot, QThreadPool
from src.config.config_models import Config, Task, Program, TaskProject, SelectedTask  # 确保根据你的实际路径引入 Config 类
from src.core.core import TaskProjectManager,log_thread


# 定义运行异步方法类
class TaskWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(TaskWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        # 正确的方式：调用 fn，并传递 self.args 和 self.kwargs
        self.fn(*self.args, **self.kwargs)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 加载配置类
        Config.json_path= '../assets/app_config.json'
        self.config = Config.from_json()  # 直接加载配置类
        # 加载样式文件
        self.load_styles()

        # 创建线程池
        self.thread_pool = QThreadPool()
        # 启动日志处理线程
        self.start_log_thread()
        # 创建主窗口
        self.setWindowTitle('MaaYYs')
        self.setMinimumSize(1000, 720)

        # 创建主布局
        self.main_layout = QHBoxLayout(self)

        # 左侧导航栏
        self.left_nav_layout = QVBoxLayout()
        self.init_navigation_bar()
        self.main_layout.addLayout(self.left_nav_layout)

        # 右侧页面内容区域
        self.right_layout = QVBoxLayout()

        # 使用Splitter分割区域
        self.splitter = QSplitter(Qt.Horizontal)

        # 初始页面为首页
        self.init_home_page()

        self.setLayout(self.main_layout)

    def load_styles(self):
        """加载样式文件"""
        with open('style.qss', 'r', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
    def start_log_thread(self):
        """启动日志处理线程"""
        task_manager = TaskProjectManager()  # 确保实例化任务管理器
        log_listener = threading.Thread(target=log_thread, args=(task_manager,))
        log_listener.daemon = True  # 设置为守护线程，主线程结束时自动结束
        log_listener.start()

    # 保存 Config 实例
    def save_json_data(self):
        Config.save_to_json(self.config)

    def init_navigation_bar(self):
        """动态创建左侧导航栏按钮"""
        nav_buttons = ['首页'] + [program.program_name for program in self.config.programs]
        for btn_text in nav_buttons:
            button = QPushButton(btn_text)
            button.setFixedHeight(50)
            button.setFixedWidth(50)
            button.setObjectName('navButton')

            self.left_nav_layout.addWidget(button)
        self.left_nav_layout.addStretch()

    def init_home_page(self):
        """初始化首页页面"""
        self.clear_right_layout()

        # 创建标题
        title = QLabel('首页')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setStyleSheet("color: #2980b9; margin: 10px 0;")
        self.right_layout.addWidget(title)

        # 创建设备表格
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['任务名称', '游戏名称', 'adb地址', 'adb端口', '运行状态', '操作'])
        self.right_layout.addWidget(self.table, 1)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置列宽度自适应内容
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # 使每列根据内容调整宽度

        # 动态填充设备表格
        self.load_device_table()

        # 自适应内容的列宽
        self.table.resizeColumnsToContents()

        # 设置每列的最小宽度
        self.table.setColumnWidth(0, 80)  # 任务名称
        self.table.setColumnWidth(1, 80)  # 游戏名称
        self.table.setColumnWidth(2, 200)  # adb地址
        self.table.setColumnWidth(3, 150)  # adb端口
        self.table.setColumnWidth(4, 100)  # 运行状态

        # 设置最后一列填充剩余空间
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.info_title = QLabel('详细信息')
        self.info_title.setAlignment(Qt.AlignCenter)
        self.info_title.setStyleSheet("color: #2980b9; margin-top: 15px;")
        self.right_layout.addWidget(self.info_title)

        # 初始化分割器
        self.init_splitter()
        self.main_layout.addLayout(self.right_layout)

    def init_splitter(self):
        """初始化分割器用于显示详细信息部分"""
        task_selection_group = QGroupBox("任务选择")
        task_settings_group = QGroupBox("任务设置")
        task_log_group = QGroupBox("任务日志")

        task_selection_layout = QVBoxLayout()
        task_selection_group.setLayout(task_selection_layout)

        task_settings_layout = QVBoxLayout()
        task_settings_group.setLayout(task_settings_layout)

        task_log_layout = QVBoxLayout()
        log_area = QTextEdit()
        log_area.setPlaceholderText("日志输出...")
        task_log_layout.addWidget(log_area)
        task_log_group.setLayout(task_log_layout)

        self.splitter.addWidget(task_selection_group)
        self.splitter.addWidget(task_settings_group)
        self.splitter.addWidget(task_log_group)

        self.splitter.setSizes([300, 400, 300])
        self.splitter.setFixedHeight(400)
        self.right_layout.addWidget(self.splitter)

    def load_device_table(self):
        """动态加载设备表格"""
        # 连接表格数据变化的信号到槽函数
        self.table.itemChanged.connect(self.on_table_item_changed)

        for task_projects_name, project in self.config.task_projects.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 任务名称
            task_name_item = QTableWidgetItem(task_projects_name)
            task_name_item.setData(Qt.UserRole, project)  # 绑定项目对象到表格单元格
            self.table.setItem(row, 0, task_name_item)

            # 游戏名称
            program_name_item = QTableWidgetItem(project.program_name)
            self.table.setItem(row, 1, program_name_item)

            # ADB 地址
            adb_address_item = QTableWidgetItem(project.adb_config['adb_address'])
            adb_address_item.setData(Qt.UserRole, ('adb_address', project))  # 绑定 ADB 地址字段到单元格
            self.table.setItem(row, 2, adb_address_item)

            # ADB 端口
            adb_port_item = QTableWidgetItem(project.adb_config['adb_port'])
            adb_port_item.setData(Qt.UserRole, ('adb_port', project))  # 绑定 ADB 端口字段到单元格
            self.table.setItem(row, 3, adb_port_item)

            # 运行状态
            status_item = QTableWidgetItem('正在执行')
            # status_item.setData(Qt.UserRole, ('status', project))  # 假设你有运行状态字段
            self.table.setItem(row, 4, status_item)

            # 创建一个 QWidget 容器（用于操作按钮）
            container_widget = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            button_task_connect = QPushButton('连接')
            button_task_connect.setObjectName('runButton')
            button_task_connect.clicked.connect(lambda _, p=project,bu=button_task_connect: self.run_task(p,bu))
            layout.addWidget(button_task_connect)

            button_info = QPushButton('查看详情')
            button_info.setObjectName('infoButton')
            button_info.clicked.connect(lambda _, p=task_projects_name: self.show_device_details(p))
            layout.addWidget(button_info)

            save_button = QPushButton("保存更改")
            save_button.setObjectName('saveButton')
            save_button.clicked.connect(self.save_json_data)
            layout.addWidget(save_button)

            container_widget.setLayout(layout)
            self.table.setCellWidget(row, 5, container_widget)

            self.table.setRowHeight(row, 50)

        self.table.resizeColumnsToContents()

    def on_table_item_changed(self, item):
        """处理表格内容变化，更新 project 对象"""
        data = item.data(Qt.UserRole)

        if isinstance(data, tuple) and len(data) == 2:
            field_name, project = data
            new_value = item.text()

            # 更新 project 对象中的值
            if field_name in project.adb_config:
                project.adb_config[field_name] = new_value
            elif field_name == 'status':  # 假设你有其他字段
                project.status = new_value
        # self.save_json_data()
        # 你可以选择在这里调用 `save_json_data()`，实时保存变更

    def clear_right_layout(self):
        """清空右侧布局中的内容"""
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def run_task(self, project: TaskProject,button_task_connect):

        button_task_connect.setText("正在连接")

        # 创建 TaskProjectManager 实例
        task_manager = TaskProjectManager()

        # 传递 task_manager 实例和 project 对象
        task = TaskWorker(task_manager.create_tasker_process, project)

        # 启动线程
        self.thread_pool.start(task)

        button_task_connect.setText("已连接")

    def show_device_details(self, task_projects_name):

        self.info_title.setText(f"详细信息:  {task_projects_name}")

        task_projects = self.config.task_projects[task_projects_name]

        program =self.config.get_program_by_name(task_projects.program_name)

        if not program:
            print("程序不存在")
            return

        # 清空之前的布局
        task_selection_group = self.splitter.widget(0)
        task_selection_layout = task_selection_group.layout()
        self.clear_layout(task_selection_layout)

        for task in program.tasks:
            selected_task = task_projects.get_selected_task_by_name(task.task_name)
            task_row = QHBoxLayout()
            checkbox = QCheckBox(task.task_name)
            checkbox.setChecked(selected_task.is_selected)
            checkbox.stateChanged.connect(lambda state, selected_t=selected_task,program_task=task,task_p=task_projects: self.update_task_selection(selected_t, program_task, state,task_p))
            task_row.addWidget(checkbox)

            set_button = QPushButton('设置')
            set_button.clicked.connect(lambda _ ,selected_t=selected_task: self.set_task_parameters(selected_t))
            task_row.addWidget(set_button)

            task_selection_layout.addLayout(task_row)

        if program.tasks:
            self.set_task_parameters(task_projects.selected_tasks[0])

    def update_task_selection(self, selected_task, program_task:Task, state,task_p:TaskProject):

        if selected_task:
            selected_task.is_selected=state==Qt.CheckState.Checked.value
        else:
            new_task=SelectedTask(program_task.task_name,False,program_task.parameters)
            task_p.selected_tasks.append(new_task)

    def set_task_parameters(self, selected_task:SelectedTask):
        """清空布局"""
        task_settings_group = self.splitter.widget(1)
        task_settings_layout = task_settings_group.layout()
        self.clear_layout(task_settings_layout)
        parameters = selected_task.task_parameters

        # 动态生成任务参数输入框
        for param_name, param_value in parameters.items():
            param_layout = QHBoxLayout()
            label = QLabel(param_name)
            line_edit = QLineEdit(str(param_value))

            # 将输入框的内容变化绑定到 selected_task 的参数上
            line_edit.textChanged.connect(
                lambda text, name=param_name: self.update_task_parameter(selected_task, name, text))

            param_layout.addWidget(label)
            param_layout.addWidget(line_edit)
            task_settings_layout.addLayout(param_layout)

    def update_task_parameter(self, selected_task: SelectedTask, param_name: str, new_value: str):
        """更新任务参数的值"""
        # 更新 selected_task 的参数值
        selected_task.task_parameters[param_name] = new_value


    def clear_layout(self, layout):
        """清空布局中的所有小部件"""
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    # 如果是布局项，递归清空其子布局
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        self.clear_layout(sub_layout)  # 递归调用
        layout.update()  # 更新布局

if __name__ == '__main__':
    # 配置日志记录
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s][%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
