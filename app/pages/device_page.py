from PySide6.QtWidgets import (QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTabWidget,
                               QSplitter, QTextEdit, QCheckBox, QWidget, QFormLayout,
                               QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame, QScrollArea, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from app.components.collapsible_widget import CollapsibleWidget, DraggableContainer
from app.models.config.device_config import OptionConfig, Resource
from app.models.config.global_config import GlobalConfig
from app.models.config.resource_config import ResourceConfig, SelectOption, BoolOption, InputOption
from core.tasker_manager import task_manager, TaskerManager


class DevicePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = GlobalConfig()
        self.init_ui()
        self.load_config_data()
        self.manager:TaskerManager=task_manager
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

        # 设备详情区域
        self.device_detail_frame = QFrame()
        self.device_detail_frame.setFrameShape(QFrame.StyledPanel)
        self.device_detail_frame.setObjectName("deviceDetailFrame")
        self.device_detail_frame.hide()

        self.device_detail_layout = QVBoxLayout(self.device_detail_frame)
        self.device_detail_layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(self.device_detail_frame)

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

    def get_device_config(self, device_name):
        """根据设备名称获取设备配置"""
        devices_config = self.global_config.get_devices_config()
        if not devices_config:
            return None

        for device in devices_config.devices:
            if device.device_name == device_name:
                return device
        return None

    def show_device_detail(self, device_name):
        """显示设备详情"""
        device_config = self.get_device_config(device_name)
        if not device_config:
            QMessageBox.warning(self, "错误", f"设备 '{device_name}' 未找到")
            return

        # 清除现有内容
        self._clear_layout(self.device_detail_layout)

        # 设备标题和返回按钮
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        back_btn = QPushButton("← 返回设备列表")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self.hide_device_detail)

        device_title = QLabel(f"设备详情: {device_name}")
        device_title.setFont(QFont("Arial", 14, QFont.Bold))
        device_title.setObjectName("deviceDetailTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(device_title)
        header_layout.addStretch()
        self.device_detail_layout.addWidget(header_widget)

        # 创建选项卡
        tab_widget = QTabWidget()
        tab_widget.setObjectName("detailTabs")

        # 添加基本信息选项卡
        info_tab = self._create_info_tab(device_config)
        tab_widget.addTab(info_tab, "基本信息")

        # 添加操作面板选项卡
        control_tab = self._create_control_tab(device_config)
        tab_widget.addTab(control_tab, "操作面板")

        # 添加日志选项卡
        log_tab = self._create_log_tab(device_config)
        tab_widget.addTab(log_tab, "日志面板")

        self.device_detail_layout.addWidget(tab_widget)

        # 显示设备详情框架，隐藏设备列表框架
        self.devices_frame.hide()
        self.device_detail_frame.show()

    def _create_info_tab(self, device_config):
        """创建基本信息选项卡"""
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_layout.setContentsMargins(15, 15, 15, 15)

        # 基本信息标题
        info_title = QLabel("基本信息")
        info_title.setFont(QFont("Arial", 12, QFont.Bold))
        info_title.setObjectName("sectionTitle")
        info_layout.addWidget(info_title)

        # 基本信息表格
        info_table = QTableWidget(6, 2)
        info_table.setObjectName("infoTable")
        info_table.setHorizontalHeaderLabels(["属性", "值"])
        info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        info_table.verticalHeader().setVisible(False)
        info_table.setEditTriggers(QTableWidget.NoEditTriggers)
        info_table.setAlternatingRowColors(True)
        info_table.setFrameShape(QFrame.NoFrame)

        info_items = [
            ("设备名称", device_config.device_name),
            ("设备类型", device_config.adb_config.name),
            ("ADB路径", device_config.adb_config.adb_path),
            ("ADB地址", device_config.adb_config.address),
            ("计划任务", "已启用" if device_config.schedule_enabled else "未启用"),
            ("启动命令", device_config.start_command or "无")
        ]

        for row, (key, value) in enumerate(info_items):
            info_table.setItem(row, 0, QTableWidgetItem(key))
            info_table.setItem(row, 1, QTableWidgetItem(value))
            info_table.setRowHeight(row, 35)

        info_layout.addWidget(info_table)
        info_layout.addStretch()

        return info_tab

    def _create_control_tab(self, device_config):
        """创建操作面板选项卡"""
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        control_layout.setContentsMargins(15, 15, 15, 15)

        # 创建分隔器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("controlSplitter")

        # 左侧 - 资源选择
        resource_widget = self._create_resource_selection_widget(device_config)

        # 右侧 - 设置面板（初始为空）
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_frame.setObjectName("settingsFrame")
        self.settings_layout = QVBoxLayout(settings_frame)
        self.settings_layout.setContentsMargins(15, 15, 15, 15)

        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        self.settings_layout.addWidget(self.settings_content)
        self.settings_layout.addStretch()

        # 将两部分添加到分隔器
        splitter.addWidget(resource_widget)
        splitter.addWidget(settings_frame)

        # 设置初始大小
        splitter.setSizes([600, 400])

        control_layout.addWidget(splitter)

        return control_tab

    def _create_resource_selection_widget(self, device_config):
        """创建资源选择控件"""
        resource_widget = QWidget()
        resource_layout = QVBoxLayout(resource_widget)
        resource_layout.setContentsMargins(0, 0, 10, 0)

        resource_label = QLabel("资源选择")
        resource_label.setFont(QFont("Arial", 12, QFont.Bold))
        resource_label.setObjectName("sectionTitle")
        resource_layout.addWidget(resource_label)

        # 获取所有可用资源
        all_resources = self.global_config.get_all_resource_configs()

        # 获取资源启用状态的字典
        resource_enabled_map = {r.resource_name: r.enable for r in device_config.resources}

        # 资源表格（带复选框）
        resource_table = QTableWidget(len(all_resources), 3)
        resource_table.setObjectName("resourceTable")
        resource_table.setHorizontalHeaderLabels(["启用", "资源名称", "操作"])
        resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        resource_table.verticalHeader().setVisible(False)
        resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        resource_table.setAlternatingRowColors(True)
        resource_table.setFrameShape(QFrame.NoFrame)

        for row, resource_config in enumerate(all_resources):
            resource_name = resource_config.resource_name

            # 复选框
            checkbox = QCheckBox()
            # 检查该资源是否已启用
            checkbox.setChecked(resource_enabled_map.get(resource_name, False))

            # 连接复选框状态变化信号，更新设备配置中对应资源的启用状态
            checkbox.stateChanged.connect(
                lambda state, d_config=device_config, r_name=resource_name, cb=checkbox:
                self.update_resource_enable_status(d_config, r_name, cb.isChecked())
            )

            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(5, 2, 5, 2)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            resource_table.setCellWidget(row, 0, checkbox_widget)

            # 资源名称
            name_item = QTableWidgetItem(f"{resource_name}")
            resource_table.setItem(row, 1, name_item)

            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)

            run_btn = QPushButton("运行")
            run_btn.setFixedWidth(60)
            run_btn.setObjectName("runButton")
            run_btn.clicked.connect(lambda checked, d_config=device_config, r_name=resource_name:
                                    self.run_resource_task(d_config, r_name))

            settings_btn = QPushButton("设置")
            settings_btn.setFixedWidth(60)
            settings_btn.setObjectName("settingsButton")
            settings_btn.clicked.connect(
                lambda checked, r_name=resource_name, d_config=device_config:
                self.show_resource_settings(d_config, r_name)
            )

            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)
            resource_table.setCellWidget(row, 2, button_widget)
            resource_table.setRowHeight(row, 35)

        resource_layout.addWidget(resource_table)

        # 添加一键启动按钮
        one_key_start_btn = QPushButton("一键启动")
        one_key_start_btn.setFixedHeight(40)
        one_key_start_btn.setObjectName("oneKeyButton")
        resource_layout.addWidget(one_key_start_btn)
        one_key_start_btn.clicked.connect(lambda: self.one_key_start_all(device_config))

        return resource_widget

    def one_key_start_all(self, device_config):
        """
        一键启动：提交所有已启用资源的任务
        """
        runtime_configs = []
        # 遍历设备配置中的所有资源，收集启用状态为 True 的资源对应的运行时配置
        for resource in device_config.resources:
            if resource.enable:
                runtime_config = self.global_config.get_runtime_configs_for_resource(
                    resource.resource_name, device_config.device_name)
                if runtime_config is not None:
                    runtime_configs.append(runtime_config)
        if runtime_configs:
            # 创建执行器并一次性提交所有任务（submit_task 已支持传入列表）
            self.manager.create_executor(device_config)
            self.manager.submit_task(device_config.device_name, runtime_configs)

    def run_resource_task(self,d_config,resource_name):
        run_time_config=self.global_config.get_runtime_configs_for_resource(resource_name,d_config.device_name)

        self.manager.create_executor(d_config)
        self.manager.submit_task(d_config.device_name, run_time_config)

    def _create_log_tab(self, device_config):
        """创建日志选项卡"""
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(15, 15, 15, 15)

        log_label = QLabel("设备日志")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        log_label.setObjectName("sectionTitle")
        log_layout.addWidget(log_label)

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setObjectName("logTextEdit")
        log_text.setText(f"""11:45:14
{device_config.device_name}
启动成功
19:19:10
{device_config.device_name} 运行正常, 这是一
长的日志信息, 用于测试SiLogItem组
动操行和显示效果。查看多行日志是
确显示和滚动。
00:00:00
{device_config.device_name}
检测到异常
""")

        log_layout.addWidget(log_text)

        return log_tab

    def update_resource_enable_status(self, device_config, resource_name, is_enabled):
        """更新资源启用状态并立即保存"""
        try:
            # 查找现有资源配置或创建新配置
            device_resource = self._get_device_resource(device_config, resource_name)

            # 如果资源配置不存在，则创建一个新的
            if not device_resource:
                device_resource = Resource(
                    resource_name=resource_name,
                    enable=False,
                    selected_tasks=[],
                    options=[]
                )
                device_config.resources.append(device_resource)

            # 更新资源的启用状态
            device_resource.enable = is_enabled

            # 立即保存全局配置
            self.global_config.save_all_configs()
        except Exception as e:
            print(f"Error updating resource enable status: {e}")
            QMessageBox.critical(self, "保存失败", f"更新资源 '{resource_name}' 状态失败: {e}")

    def _get_device_resource(self, device_config, resource_name):
        """从设备配置中获取指定资源"""
        for resource in device_config.resources:
            if resource.resource_name == resource_name:
                return resource
        return None

    def hide_device_detail(self):
        """隐藏设备详情"""
        self.device_detail_frame.hide()
        self.devices_frame.show()

    def refresh_device_list(self):
        """刷新设备列表"""
        self.populate_device_table()

    def show_resource_settings(self, device_config, resource_name):
        """显示资源设置"""
        # 设置全局属性，供 eventFilter 使用
        self.selected_device_name = device_config.device_name
        self.selected_resource_name = resource_name
        # 获取全局资源配置
        full_resource_config = self.global_config.get_resource_config(resource_name)
        if not full_resource_config:
            QMessageBox.warning(self, "错误", f"找不到资源 '{resource_name}' 的配置")
            return

        # 获取或创建设备资源配置
        device_resource = self._get_device_resource(device_config, resource_name)
        if not device_resource:
            device_resource = Resource(
                resource_name=resource_name,
                enable=False,
                selected_tasks=[],  # 初始化为空列表
                options=[]
            )
            device_config.resources.append(device_resource)

        # 清除现有设置内容
        self._clear_layout(self.settings_content_layout)

        # 创建设置UI
        self._create_resource_settings_ui(device_resource, full_resource_config, device_config)

    def drag_connect(self, current_order):
        """事件过滤器，用于捕获拖拽事件并更新任务顺序"""
        try:
            device_name = getattr(self, 'selected_device_name', None)
            resource_name = getattr(self, 'selected_resource_name', None)
            if not (device_name and resource_name):
                return

            device_config = self.get_device_config(device_name)
            if not device_config:
                return

            resource_config = next(
                (res for res in device_config.resources if res.resource_name == resource_name),
                None
            )
            if not resource_config:
                return

            # 更新已选任务顺序（只保留已选择的任务）
            resource_config.selected_tasks = [
                task for task in current_order if task in resource_config.selected_tasks
            ]
            self.global_config.save_all_configs()
        except Exception as e:
            print(f"Error in eventFilter: {e}")

    def _create_resource_settings_ui(self, device_resource, full_resource_config, device_config):
        """创建资源设置UI"""
        # 资源名称标题
        resource_name = QLabel(f"{device_resource.resource_name} 设置")
        resource_name.setFont(QFont("Arial", 12, QFont.Bold))
        resource_name.setObjectName("resourceSettingsTitle")
        self.settings_content_layout.addWidget(resource_name)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # 使用DraggableContainer作为滚动区域内的容器控件
        scroll_content = DraggableContainer()
        scroll_content.setObjectName('draggableContainer')
        scroll_content.layout.installEventFilter(self)  # 添加事件过滤器
        scroll_content.drag.connect(self.drag_connect)

        # 记录原始任务顺序
        task_order_map = {task.task_name: idx for idx, task in enumerate(full_resource_config.resource_tasks)}
        # 记录selected_tasks中的顺序（device_resource.selected_tasks可能为空，使用or []处理）
        selected_order = {task_name: idx for idx, task_name in enumerate(device_resource.selected_tasks or [])}

        # 创建排序后的任务列表：
        # 1. 如果任务在selected_order中，排序权值为0，并按照selected_order中的顺序排序；
        # 2. 如果任务不在selected_order中，排序权值为1，并按照原始顺序排序。
        sorted_tasks = sorted(
            full_resource_config.resource_tasks,
            key=lambda task: (
                0 if task.task_name in selected_order else 1,
                selected_order.get(task.task_name, task_order_map.get(task.task_name, float('inf')))
            )
        )

        for task in sorted_tasks:
            options_widget = CollapsibleWidget(task.task_name)

            # 根据selected_order判断任务是否选中
            is_task_selected = task.task_name in selected_order
            options_widget.checkbox.setChecked(is_task_selected)

            # 使用闭包确保正确传递任务名称
            options_widget.checkbox.stateChanged.connect(
                lambda state, t_name=task.task_name, cb=options_widget.checkbox:
                self.update_task_selection(
                    device_config,
                    device_resource,
                    t_name,
                    cb.isChecked()
                )
            )

            if task.option:
                for option_name in task.option:
                    for option in full_resource_config.options:
                        if option.name == option_name:
                            option_widget = self._create_option_widget(
                                option, option_name,
                                {opt.option_name: opt for opt in device_resource.options},
                                task.task_name,
                                {},
                                device_config,
                                device_resource
                            )
                            options_widget.content_layout.addWidget(option_widget)
            else:
                no_options_label = QLabel("该任务没有可配置的选项")
                no_options_label.setStyleSheet("color: #666666; font-style: italic;")
                no_options_label.setAlignment(Qt.AlignCenter)
                options_widget.content_layout.addWidget(no_options_label)

            scroll_content.layout.addWidget(options_widget)

        scroll_content.layout.addStretch()
        scroll_area.setWidget(scroll_content)
        self.settings_content_layout.addWidget(scroll_area)

    def _create_option_widget(self, option, option_name, current_options, task_name,
                              task_options_map, device_config, device_resource):
        """创建选项控件"""
        option_widget = QWidget()
        option_layout = QHBoxLayout(option_widget)
        option_layout.setContentsMargins(0, 2, 0, 2)
        option_layout.setSpacing(10)

        # 选项标签
        option_label = QLabel(option.name)
        option_layout.addWidget(option_label)
        option_layout.addStretch()

        # 根据选项类型添加不同的控件
        if isinstance(option, SelectOption):
            widget = QComboBox()
            for choice in option.choices:
                widget.addItem(choice.name, choice.value)
            # 设置当前值（如果在设备配置中存在）
            if option_name in current_options:
                index = widget.findData(current_options[option_name].value)
                if index >= 0:
                    widget.setCurrentIndex(index)

            # 连接选择变化信号
            widget.currentIndexChanged.connect(
                lambda index, w=widget, o_name=option_name:
                self.update_option_value(device_config, device_resource, o_name, w.currentData())
            )

        elif isinstance(option, BoolOption):
            widget = QCheckBox()
            if option_name in current_options:
                widget.setChecked(current_options[option_name].value)
            else:
                widget.setChecked(option.default)

            # 连接复选框状态变化信号
            widget.stateChanged.connect(
                lambda state, o_name=option_name, cb=widget:
                self.update_option_value(device_config, device_resource, o_name, cb.isChecked())
            )

        elif isinstance(option, InputOption):
            widget = QLineEdit()
            if option_name in current_options:
                widget.setText(str(current_options[option_name].value))
            else:
                widget.setText(str(option.default))

            # 连接文本编辑完成信号
            widget.editingFinished.connect(
                lambda o_name=option_name, le=widget:
                self.update_option_value(device_config, device_resource, o_name, le.text())
            )
        else:
            widget = QLabel("不支持的选项类型")

        option_layout.addWidget(widget)

        # 将选项与其控件关联，方便后续引用
        task_options_map[(task_name, option_name)] = widget

        return option_widget

    def update_task_selection(self, device_config, resource_config, task_name, is_selected):
        """更新任务选择状态并立即保存"""
        try:
            # 确保 selected_tasks 是列表
            selected_tasks = resource_config.selected_tasks or []

            # 获取当前界面上的所有任务
            if is_selected:
                # 如果任务不在选定列表中，则添加到选定列表
                if task_name not in selected_tasks:
                    selected_tasks.append(task_name)
            else:
                # 移除任务，如果存在
                if task_name in selected_tasks:
                    selected_tasks.remove(task_name)

            # 更新资源配置
            resource_config.selected_tasks = selected_tasks

            # 立即保存全局配置
            self.global_config.save_all_configs()

            print(f"Updated selected tasks: {selected_tasks}")  # 调试信息
        except Exception as e:
            print(f"Error updating task selection: {e}")
            QMessageBox.critical(self, "保存失败", f"更新任务 '{task_name}' 选择状态失败: {e}")

    def update_option_value(self, device_config, resource_config, option_name, value):
        """更新选项值并立即保存"""
        try:
            # 查找已有选项配置
            option_found = False
            for i, option in enumerate(resource_config.options):
                if option.option_name == option_name:
                    resource_config.options[i].value = value
                    option_found = True
                    break

            # 如果未找到，添加新选项
            if not option_found:
                new_option = OptionConfig(
                    option_name=option_name,
                    value=value
                )
                resource_config.options.append(new_option)

            # 立即保存全局配置
            self.global_config.save_all_configs()
        except Exception as e:
            print(f"Error updating option value: {e}")
            QMessageBox.critical(self, "保存失败", f"更新选项 '{option_name}' 值失败: {e}")

    def _clear_layout(self, layout):
        """清除布局中的所有控件"""
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())