import logging
import threading

from PySide6.QtCore import Qt, QRunnable, Slot, QThreadPool, QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QCheckBox, QSplitter, QHeaderView, QComboBox,
    QFormLayout
)

from src.utils.config_programs import *
from src.utils.config_projects import *
from src.core.core import TaskProjectManager, log_thread


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

        self.projects_json_path = '../assets/config/projects.json'
        self.projects = ProjectsJson.load_from_file(self.projects_json_path)  # 直接加载配置类

        self.programs_json_path = '../assets/config/programs.json'
        self.programs = ProgramsJson.load_from_file(self.programs_json_path)  # 直接加载配置类

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
        with open('./ui/style.qss', 'r', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def start_log_thread(self):
        """启动日志处理线程"""
        task_manager = TaskProjectManager()
        log_listener = threading.Thread(target=log_thread, args=(task_manager,))
        log_listener.daemon = True
        log_listener.start()

    # 保存 Config 实例
    def save_json_data(self):
        self.projects.save_to_file(self.projects_json_path)
        self.programs.save_to_file(self.programs_json_path)

    def init_navigation_bar(self):
        """动态创建左侧导航栏按钮"""
        nav_buttons = ['首页'] + [program.program_name for program in self.programs.programs]
        for btn_text in nav_buttons:
            button = QPushButton(btn_text)
            button.setFixedHeight(50)
            button.setFixedWidth(50)
            button.setObjectName('navButton')

            self.left_nav_layout.addWidget(button)
        self.left_nav_layout.addStretch()

    def init_home_page(self):
        """初始化首页页面，包含四个垂直排列的部分"""
        self.clear_right_layout()

        # 创建一个用于承载所有组件的垂直容器
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        # 设置样式表，添加阴影和圆角效果
        container_widget.setStyleSheet("""
            #homeContainer {
                background-color: white;  /* 背景颜色 */
                border-radius: 15px;      /* 圆角半径 */
                padding: 10px;            /* 内边距 */
            }
        """)

        # 设置垂直容器中的组件之间的间隔（减少间隔）
        container_layout.setSpacing(5)

        # 设置主容器的四周内边距（可根据需要调整）
        container_layout.setContentsMargins(10, 10, 10, 10)

        # 1. 首页标签容器
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(0)  # 组件之间无间距
        title_layout.setContentsMargins(0, 0, 0, 0)  # 设置内边距为0

        title = QLabel('首页')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setStyleSheet("color: #2980b9; margin: 10px 0;")
        title_layout.addWidget(title)

        # 2. 表格容器
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setSpacing(0)  # 组件之间无间距
        table_layout.setContentsMargins(0, 0, 0, 0)  # 设置内边距为0

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['任务名称', '游戏名称', 'adb地址', 'adb端口', '运行状态', '操作'])
        table_layout.addWidget(self.table)

        # 将组件依次添加到容器
        container_layout.addWidget(title_container)  # 首页标签
        container_layout.addWidget(table_container)  # 表格

        # 设置列宽度自适应内容
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.load_device_table()
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 280)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 100)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        # 3. 详细信息标签容器
        info_title_container = QWidget()
        info_title_layout = QVBoxLayout(info_title_container)
        info_title_layout.setSpacing(0)  # 无间距
        info_title_layout.setContentsMargins(0, 0, 0, 0)  # 设置内边距为0

        self.info_title = QLabel('详细信息')
        self.info_title.setAlignment(Qt.AlignCenter)
        self.info_title.setStyleSheet("color: #2980b9; margin-top: 15px;")
        info_title_layout.addWidget(self.info_title)

        # 4. 详细信息容器
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setSpacing(0)  # 无间距
        details_layout.setContentsMargins(0, 0, 0, 0)  # 设置内边距为0
        self.init_splitter()  # 初始化详细信息分割器

        # 添加组件到布局
        container_layout.addWidget(info_title_container)  # 详细信息标签
        container_layout.addWidget(details_container)  # 详细信息
        details_layout.addWidget(self.splitter)

        # 将主容器布局添加到右侧主布局
        self.right_layout.addWidget(container_widget)
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
        log_area.setReadOnly(True)
        task_log_group.setLayout(task_log_layout)

        self.splitter.addWidget(task_selection_group)
        self.splitter.addWidget(task_settings_group)
        self.splitter.addWidget(task_log_group)

        self.splitter.setSizes([300, 400, 300])
        self.splitter.setFixedHeight(400)
        # self.right_layout.addWidget(self.splitter)

    def load_device_table(self):
        """动态加载设备表格"""
        # 连接表格数据变化的信号到槽函数
        self.table.itemChanged.connect(self.on_table_item_changed)

        for project in self.projects.projects:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 任务名称
            task_name_item = QTableWidgetItem(project.project_name)
            task_name_item.setData(Qt.UserRole, project)  # 绑定项目对象到表格单元格
            self.table.setItem(row, 0, task_name_item)

            # 游戏名称
            program_name_item = QTableWidgetItem(project.program_name)
            self.table.setItem(row, 1, program_name_item)

            # ADB 地址
            adb_address_item = QTableWidgetItem(project.adb_config.adb_path)
            adb_address_item.setData(Qt.UserRole, ('adb_path', project))  # 绑定 ADB 路径字段到单元格
            self.table.setItem(row, 2, adb_address_item)

            # ADB 端口
            adb_port_item = QTableWidgetItem(project.adb_config.adb_address)
            adb_port_item.setData(Qt.UserRole, ('adb_address', project))  # 绑定 ADB 端口字段到单元格
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

            button_task_connect = QPushButton('一键启动')
            button_task_connect.setObjectName('runButton')
            button_task_connect.clicked.connect(lambda _, p=project,bu=button_task_connect: self.run_task(p,bu))
            layout.addWidget(button_task_connect)

            button_info = QPushButton('查看详情')
            button_info.setObjectName('infoButton')
            button_info.clicked.connect(lambda _, p=project: self.show_device_details(p))
            layout.addWidget(button_info)

            container_widget.setLayout(layout)
            self.table.setCellWidget(row, 5, container_widget)

            self.table.setRowHeight(row, 50)

        self.table.resizeColumnsToContents()

    def on_table_item_changed(self, item):
        """处理表格内容变化，更新 project 对象"""
        data = item.data(Qt.UserRole)

        if data is None:
            return

        # 获取项目对象
        if isinstance(data, tuple):
            field, project = data
        else:
            project = data  # 如果只有项目对象，没有字段信息

        # 根据单元格的列索引更新对应的项目对象属性
        if item.column() == 2:  # ADB 地址
            adb_path = item.text()
            project.adb_config.adb_path = adb_path  # 更新项目的 ADB 路径

        elif item.column() == 3:  # ADB 端口
            adb_address = item.text()
            project.adb_config.adb_address = adb_address  # 更新项目的 ADB 端口

        self.projects.save_to_file(self.projects_json_path)

    def clear_right_layout(self):
        """清空右侧布局中的内容"""
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def run_task(self, project, button_task_connect: QPushButton):
        """
        启动任务，更新UI，并确保在异步线程中执行
        """
        # 更新UI状态
        button_task_connect.setText("正在连接")
        button_task_connect.setEnabled(False)

        # 创建 TaskProjectManager 实例
        task_manager = TaskProjectManager()

        # 定义实际任务执行逻辑
        def execute_task():
            try:
                # 启动连接任务（可以扩展为实际的连接逻辑）
                task_manager.create_tasker_process(project)

                project_run_data = project.get_project_run_data(self.programs)

                # 发送任务到设备
                task_manager.send_task(project, project_run_data)

                # 成功连接和发送任务后更新UI
                self.update_button_state(button_task_connect, "已连接", True)

            except Exception as e:
                logging.error(f"任务启动失败: {e}")
                # 如果有错误，重置按钮状态，并弹出错误提示
                self.update_button_state(button_task_connect, "连接失败", True)

        # 使用线程池执行任务
        task = TaskWorker(execute_task)
        self.thread_pool.start(task)

    def update_button_state(self, button: QPushButton, text: str, enabled: bool):
        """
        更新按钮的文本和可用状态
        """
        button.setText(text)
        button.setEnabled(enabled)

    def show_device_details(self, project: Project):
        # 更新详细信息标题
        self.info_title.setText(f"详细信息: {project.project_name}")

        # 获取对应的 program
        program = self.programs.get_program_by_name(project.program_name)
        if not program:
            return

        # 清空之前的布局
        task_selection_group = self.splitter.widget(0)
        task_selection_layout = task_selection_group.layout()
        self.clear_layout(task_selection_layout)

        # 记录所有复选框
        self.checkboxes = []

        # 动态添加任务复选框和设置按钮
        for task in program.program_tasks:
            task_row = QHBoxLayout()

            # 添加任务复选框
            checkbox = QCheckBox(task.task_name)
            checkbox.setChecked(True if task.task_name in project.selected_tasks else False)

            # 记录复选框
            self.checkboxes.append(checkbox)

            # 定义处理复选框状态变化的函数
            def on_checkbox_state_changed(state, task_name=task.task_name):
                if state == Qt.CheckState.Checked.value:  # 勾选状态
                    if task_name not in project.selected_tasks:
                        project.selected_tasks.append(task_name)
                else:  # 未勾选状态
                    if task_name in project.selected_tasks:
                        project.selected_tasks.remove(task_name)

                # 保存到文件
                self.projects.save_to_file(self.projects_json_path)

            # 连接复选框状态变化信号到自定义函数
            checkbox.stateChanged.connect(on_checkbox_state_changed)
            task_row.addWidget(checkbox)

            # 添加设置按钮
            set_button = QPushButton('设置')
            set_button.clicked.connect(lambda _, selected_t=task: self.set_task_parameters(selected_t, program,project))
            task_row.addWidget(set_button)

            # 添加发送任务按钮
            execute_button = QPushButton('执行')

            # 将当前任务传递给点击事件
            execute_button.clicked.connect(lambda _, selected_t=task: self.send_single_task(selected_t, project))

            task_row.addWidget(execute_button)

            # 将任务行添加到布局
            task_selection_layout.addLayout(task_row)

        # 添加“全选”和“开始”按钮
        button_container = QHBoxLayout()

        # 添加全选按钮
        self.select_all_state = False  # 初始状态为未全选
        select_all_button = QPushButton("全选")
        select_all_button.setObjectName('runButton')

        # 定义全选/清空按钮的行为
        def toggle_select_all():
            if not self.select_all_state:
                # 全选所有任务
                for checkbox in self.checkboxes:
                    checkbox.setChecked(True)
                select_all_button.setText("清空")
                self.select_all_state = True
            else:
                # 清空所有任务的选择
                for checkbox in self.checkboxes:
                    checkbox.setChecked(False)
                select_all_button.setText("全选")
                self.select_all_state = False

        # 连接全选按钮的点击事件
        select_all_button.clicked.connect(toggle_select_all)
        button_container.addWidget(select_all_button)

        # 添加开始按钮
        start_button = QPushButton("开始")
        start_button.setObjectName('runButton')
        start_button.clicked.connect(lambda _, p=project, bu=start_button: self.run_task(p, bu))
        button_container.addWidget(start_button)

        # 将按钮布局添加到主布局
        task_selection_layout.addLayout(button_container)

    def set_task_parameters(self, selected_task, program, project):
        """动态生成任务的参数设置界面"""
        task_settings_group = self.splitter.widget(1)
        task_settings_layout = task_settings_group.layout()
        self.clear_layout(task_settings_layout)

        # 获取对应任务的 option
        options = program.get_task_by_name(selected_task.task_name).option
        setting = program.option.options

        # 使用 QFormLayout 来对齐标签和输入框，使得布局更加整齐
        form_layout = QFormLayout()
        if not options:
            label = QLabel("该任务无参数设置项")
            form_layout.addRow(label)
            task_settings_layout.addLayout(form_layout)
            return

        for option in options:
            sett = setting.get(option)

            # 优先从 project.option 获取参数，如果不存在则使用 sett 的值
            project_option = next((opt for opt in project.option.options if opt.option_name == option), None)

            # 动态生成 QLineEdit、QComboBox 或 QCheckBox，并绑定其值到 project.option
            if sett.type == 'input' and sett.input:
                self.create_input_option(form_layout, project, project_option, sett, option)

            elif sett.type == 'select' and sett.select:
                self.create_select_option(form_layout, project, project_option, sett, option)

            elif sett.type == 'boole':
                self.create_boole_option(form_layout, project, project_option, sett, option)

            else:
                print(f"Unknown or missing attributes for option: {option}")

        # 将生成的表单布局添加到主布局中
        task_settings_layout.addLayout(form_layout)

    def create_input_option(self, layout, project, project_option, sett, option_name):
        """创建 input 类型的参数设置控件"""
        label = QLabel(sett.input.name)

        # 获取默认值，优先从 project.option 获取
        default_value = project_option.option_value if project_option and project_option.option_type == 'input' else sett.input.default
        line_edit = QLineEdit(str(default_value))

        # 将输入框的内容变化绑定到 project.option
        line_edit.textChanged.connect(
            lambda text, name=option_name: self.update_project_option(project, name, 'input', text)
        )

        layout.addRow(label, line_edit)
        print(f"Input Option: name={sett.input.name}, default={default_value}")

    def create_select_option(self, layout, project, project_option, sett, option_name):
        """创建 select 类型的参数设置控件"""
        label = QLabel(option_name)
        combo_box = QComboBox()

        # 获取默认选中值，优先从 project.option 获取
        selected_value = project_option.option_value if project_option and project_option.option_type == 'select' else \
        sett.select[0].name

        # 添加下拉选项并设置默认选中项
        for select_option in sett.select:
            combo_box.addItem(select_option.name)
            if select_option.name == selected_value:
                combo_box.setCurrentText(select_option.name)

        # 处理下拉框选择事件
        combo_box.currentTextChanged.connect(
            lambda text, name=option_name: self.update_project_option(project, name, 'select', text)
        )

        layout.addRow(label, combo_box)

    def create_boole_option(self, layout, project, project_option, sett, option_name):
        """创建 boole 类型的参数设置控件"""
        label = QLabel(option_name)
        check_box = QCheckBox()

        # 获取 BooleOption 对象，优先从 project_option 获取
        if project_option and project_option.option_type == 'boole':
            boole_option = project_option.option_value
        else:
            boole_option = sett.boole

        # 如果 boole_option 是 BooleOption 类型，则取其 default 属性
        boole_value = boole_option.default if isinstance(boole_option, BooleOption) else boole_option
        check_box.setChecked(boole_value)

        # 处理复选框状态改变事件，更新 BooleOption 中的 default 属性
        check_box.stateChanged.connect(
            lambda state, name=option_name: self.update_project_option(project, name, 'boole', bool(state))
        )

        layout.addRow(label, check_box)

    # 更新 project.option 的方法
    def update_project_option(self, project, option_name, option_type, option_value):
        # 查找或创建 project.option 中的相应选项
        project_option = next((opt for opt in project.option.options if opt.option_name == option_name), None)

        if project_option:
            # 更新现有选项
            project_option.option_value = option_value
        else:
            # 如果选项不存在，创建新选项并添加到 project.option 中
            new_option = Option(option_name=option_name, option_type=option_type, option_value=option_value)
            project.option.options.append(new_option)

        self.projects.save_to_file(self.projects_json_path)


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

    def send_single_task(self, selected_task, project):
        """
        发送单个任务到设备
        """
        try:
            # 创建 TaskProjectManager 实例
            task_manager = TaskProjectManager()
            task_manager.create_tasker_process(project)

            # 获取项目运行数据，但只包含单个任务
            project_run_data = project.get_project_all_run_data(self.programs)

            # 过滤掉非选中的任务，只保留当前点击的任务
            filtered_tasks = [task for task in project_run_data.project_run_tasks if task.task_name == selected_task.task_name]

            if not filtered_tasks:
                logging.error(f"任务 {selected_task.task_name} 不在选中任务中")
                return

            # 创建仅包含当前任务的 ProjectRunData
            single_task_run_data = ProjectRunData(project_run_tasks=filtered_tasks)

            # 发送任务到设备
            task_manager.send_task(project, single_task_run_data)

            logging.info(f"任务 {selected_task.task_name} 已成功发送")

        except Exception as e:
            logging.error(f"发送任务 {selected_task.task_name} 失败: {e}")
