import json
from maa.library import Library
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QCheckBox, QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, QRunnable, Slot, QThreadPool


class TaskWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(TaskWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        self.fn(*self.args, **self.kwargs)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MaaYYs')
        self.setMinimumSize(1000, 720)

        self.load_json_data()

        # 加载样式文件
        self.load_styles()

        # 创建线程池
        self.thread_pool = QThreadPool()

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
        with open('../ui/style.qss', 'r',encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def load_json_data(self):
        """从文件加载 JSON 数据"""
        with open('../assets/app_config.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def save_json_data(self):
        """保存 JSON 数据到文件"""
        with open('../assets/app_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        print("数据已保存到 ../assets/app_config.json 文件")

    def init_navigation_bar(self):
        """动态创建左侧导航栏按钮"""
        nav_buttons = ['首页'] + list([program['program_name'] for program in self.data['programs']])
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
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #34495e; color: white; }")
        self.right_layout.addWidget(self.table, 1)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 动态填充设备表格
        self.load_device_table()

        # 调整列宽度自适应内容
        self.table.resizeColumnsToContents()

        self.info_title = QLabel('详细信息')
        self.info_title.setAlignment(Qt.AlignCenter)
        self.info_title.setStyleSheet("color: #2980b9; margin-top: 15px;")
        self.right_layout.addWidget(self.info_title)

        # 初始化分割器
        self.init_splitter()
        self.main_layout.addLayout(self.right_layout)

    def load_device_table(self):
        """动态加载设备表格"""
        for project_key, project in self.data['task_projects'].items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(project_key))
            self.table.setItem(row, 1, QTableWidgetItem(project['program_name']))
            self.table.setItem(row, 2, QTableWidgetItem(project['adb_config']['adb_address']))
            self.table.setItem(row, 3, QTableWidgetItem(project['adb_config']['adb_port']))
            self.table.setItem(row, 4, QTableWidgetItem('正在执行'))

            # 创建一个 QWidget 容器
            container_widget = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            button_run = QPushButton('运行')
            button_run.setObjectName('runButton')
            button_run.clicked.connect(lambda _, p=project_key: self.run_task(p))
            layout.addWidget(button_run)

            button_info = QPushButton('查看详情')
            button_info.setObjectName('infoButton')
            button_info.clicked.connect(lambda _, p=project_key: self.show_device_details(p))
            layout.addWidget(button_info)

            save_button = QPushButton("保存更改")
            save_button.setObjectName('saveButton')
            save_button.clicked.connect(self.save_json_data)
            layout.addWidget(save_button)

            container_widget.setLayout(layout)
            self.table.setCellWidget(row, 5, container_widget)

            self.table.setRowHeight(row, 50)

        self.table.resizeColumnsToContents()

    def clear_right_layout(self):
        """清空右侧布局中的内容"""
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

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

    def run_task(self, project_key):
        from src.core.core import task_manager_connect

        task = TaskWorker(task_manager_connect, project_key)
        self.thread_pool.start(task)

    def show_device_details(self, project_key):
        self.info_title.setText(f"详细信息:  {project_key}")

        project = self.data['task_projects'][project_key]
        program_name = project['program_name']
        program = next((p for p in self.data['programs'] if p['program_name'] == program_name), None)

        if not program:
            return
        task_selection_group = self.splitter.widget(0)
        task_selection_layout = task_selection_group.layout()

        self.clear_layout(task_selection_layout)

        for task in program['tasks']:
            task_row = QHBoxLayout()
            selected_task = next((t for t in project['selected_tasks'] if t['task_name'] == task['task_name']), None)
            is_selected = selected_task is not None and selected_task['is_selected']

            checkbox = QCheckBox(task['task_name'])
            checkbox.setChecked(is_selected)
            checkbox.stateChanged.connect(lambda state, t=task: self.update_task_selection(project_key, t, state))
            task_row.addWidget(checkbox)

            set_button = QPushButton('设置')
            set_button.clicked.connect(lambda _, t=task: self.set_task_parameters(project_key, t))
            task_row.addWidget(set_button)

            task_selection_layout.addLayout(task_row)

        if project['selected_tasks']:
            self.set_task_parameters(project_key, project['selected_tasks'][0])

    def update_task_selection(self, project_key, task, state):
        project = self.data['task_projects'][project_key]
        selected_task = next((t for t in project['selected_tasks'] if t['task_name'] == task['task_name']), None)
        if selected_task:
            selected_task['is_selected'] = state == Qt.CheckState.Checked.value
        else:
            project['selected_tasks'].append({'task_name': task['task_name'], 'is_selected': state == Qt.CheckState.Checked.value})

    def set_task_parameters(self, project_key, task):
        """设置任务参数"""
        task_settings_group = self.splitter.widget(1)
        task_settings_layout = task_settings_group.layout()

        # 清空任务参数
        self.clear_layout(task_settings_layout)

        project = self.data['task_projects'][project_key]
        program_name = project['program_name']

        # 获取程序对应的任务
        program = next((p for p in self.data['programs'] if p['program_name'] == program_name), None)

        if not program:
            return

        # 查找选中的任务
        selected_task = next((t for t in project['selected_tasks'] if t['task_name'] == task['task_name']), None)

        if selected_task:
            parameters = selected_task['task_parameters']
        else:
            # 如果没有选中的任务，则使用默认参数
            default_task = next((t for t in program['tasks'] if t['task_name'] == task['task_name']), None)
            parameters = default_task['parameters'] if default_task else {}

        # 动态生成任务参数输入框
        for param_name, param_value in parameters.items():
            param_layout = QHBoxLayout()
            label = QLabel(param_name)
            line_edit = QLineEdit(str(param_value))

            # 使用默认参数机制确保正确绑定每个参数名和值
            line_edit.textChanged.connect(
                lambda value, p=param_name: self.update_task_param(project_key, task, p, value)
            )

            param_layout.addWidget(label)
            param_layout.addWidget(line_edit)
            task_settings_layout.addLayout(param_layout)

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
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
