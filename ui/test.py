import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QTextEdit, QCheckBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.scripts.pyside_tool import project


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('设备管理')
        self.setMinimumSize(800, 600)  # 设置窗口最小大小

        # 加载JSON数据
        self.load_json_data()

        # 创建主布局
        self.main_layout = QHBoxLayout(self)

        # 左侧导航栏
        self.left_nav_layout = QVBoxLayout()
        self.init_navigation_bar()  # 动态创建导航栏
        self.main_layout.addLayout(self.left_nav_layout)

        # 右侧页面内容区域
        self.right_layout = QVBoxLayout()

        # 使用Splitter分割区域并设置初始大小
        self.splitter = QSplitter(Qt.Horizontal)

        # 初始页面为首页
        self.init_home_page()

        # 添加保存按钮
        self.save_button = QPushButton("保存更改")
        self.save_button.clicked.connect(self.save_json_data)  # 点击保存 JSON
        self.main_layout.addWidget(self.save_button)


        self.setLayout(self.main_layout)

    # 添加 run_selected_tasks 方法
    def run_selected_tasks(self):
        """打印所有选择的任务"""
        selected_tasks = []
        for project_key, project in self.data['task_projects'].items():
            for task in project['selected_tasks']:
                if task['is_selected']:
                    selected_tasks.append(task['task_name'])

        print("选中的任务:", selected_tasks)

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
        nav_buttons = ['首页'] + list(self.data['task_projects'].keys())
        for btn_text in nav_buttons:
            button = QPushButton(btn_text)
            button.setFixedHeight(50)  # 固定按钮高度
            button.setFixedWidth(100)
            self.left_nav_layout.addWidget(button)
            button.clicked.connect(self.handle_nav_click)  # 添加点击事件
        self.left_nav_layout.addStretch()  # 增加伸缩空间，让按钮靠上排列

    def init_home_page(self):
        """初始化首页页面"""
        self.clear_right_layout()

        # 创建标题
        title = QLabel('首页')
        title.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(title)

        # 创建设备表格
        self.table = QTableWidget(0, 6)  # 初始化为空
        self.table.setHorizontalHeaderLabels(['任务名称', '游戏名称', 'adb地址', 'adb端口', '运行状态', '操作'])
        self.right_layout.addWidget(self.table)

        # 动态填充设备表格
        self.load_device_table()

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

            # 添加操作按钮
            button = QPushButton('查看详情')
            button.clicked.connect(lambda _, p=project_key: self.show_device_details(p))  # 绑定事件并传递设备信息
            self.table.setCellWidget(row, 5, button)

    def clear_right_layout(self):
        """清空右侧布局中的内容"""
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

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

        # 将三个部分添加到 Splitter 中
        self.splitter.addWidget(task_selection_group)
        self.splitter.addWidget(task_settings_group)
        self.splitter.addWidget(task_log_group)

        # 设置初始大小比例：任务选择 30%，任务设置 40%，日志输出 30%
        self.splitter.setSizes([300, 400, 300])

        self.right_layout.addWidget(self.splitter)

    def show_device_details(self, project_key):
        """展示设备详情"""
        project = self.data['task_projects'][project_key]
        # print(project)
        # 通过 program_name 找到对应的 program
        program_name = project['program_name']
        program = next((p for p in self.data['programs'] if p['program_name'] == program_name), None)

        if not program:
            return
        task_selection_group = self.splitter.widget(0)
        task_selection_layout = task_selection_group.layout()

        # 清空之前的任务选择
        self.clear_layout(task_selection_layout)

        # 创建新的任务选择部分
        for task in program['tasks']:
            task_row = QHBoxLayout()

            # 检查任务是否在 selected_tasks 中
            selected_task = next((t for t in project['selected_tasks'] if t['task_name'] == task['task_name']), None)
            is_selected = selected_task is not None and selected_task['is_selected']

            # 添加复选框
            checkbox = QCheckBox(task['task_name'])
            checkbox.setChecked(is_selected)  # 根据 selected_tasks 设置选中状态

            # 这里的 `t=task` 将每个 task 绑定到当前循环的值，避免 lambda 闭包问题
            checkbox.stateChanged.connect(lambda state, t=task: self.update_task_selection(project_key, t, state))
            task_row.addWidget(checkbox)

            # 添加设置按钮
            set_button = QPushButton('设置')

            # 同样，确保 `t=task` 绑定当前 task
            set_button.clicked.connect(lambda _, t=task: self.set_task_parameters(project_key, t))
            task_row.addWidget(set_button)

            task_selection_layout.addLayout(task_row)

        # 处理任务设置，显示第一个任务的参数
        if project['selected_tasks']:
            self.set_task_parameters(project_key, project['selected_tasks'][0])

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

    def update_task_selection(self, project_key, task, state):
        """更新任务选择状态"""
        project = self.data['task_projects'][project_key]
        selected_task = next((t for t in project['selected_tasks'] if t['task_name'] == task['task_name']), None)

        if selected_task:
            selected_task['is_selected'] = state == Qt.Checked
        else:
            # 如果该任务不在 selected_tasks 中，则添加
            new_task = {
                'task_name': task['task_name'],
                'is_selected': state == Qt.Checked,
                'task_parameters': task['parameters']
            }
            project['selected_tasks'].append(new_task)

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
            line_edit.textChanged.connect(
                lambda value, p=param_name: self.update_task_param(project_key, task, p, value))
            param_layout.addWidget(label)
            param_layout.addWidget(line_edit)
            task_settings_layout.addLayout(param_layout)

    def update_task_param(self, project_key, task, param_name, value):
        """更新任务参数"""
        project = self.data['task_projects'][project_key]
        selected_task = next((t for t in project['selected_tasks'] if t['task_name'] == task['task_name']), None)

        if selected_task:
            selected_task['task_parameters'][param_name] = value
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
