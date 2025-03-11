from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSplitter, QFrame, QHBoxLayout,
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QCheckBox, QPushButton, QScrollArea, QComboBox, QLineEdit,
                               QMessageBox)
from PySide6.QtGui import QFont

# 导入自定义组件
from app.components.collapsible_widget import CollapsibleWidget, DraggableContainer
from app.models.config.resource_config import SelectOption, BoolOption, InputOption


class ControlTab(QWidget):
    def __init__(self, device_config, global_config, manager, parent_detail_page, parent=None):
        super().__init__(parent)
        self.device_config = device_config
        self.global_config = global_config
        self.manager = manager
        self.parent_detail_page = parent_detail_page  # 用于调用 DeviceDetailPage 中的回调函数
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)

        # 创建左右分割区域
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("controlSplitter")

        # 左侧：资源选择控件
        self.resource_widget = self._create_resource_selection_widget()
        self.splitter.addWidget(self.resource_widget)

        # 右侧：设置面板（初始为空）
        self.settings_frame = QFrame()
        self.settings_frame.setFrameShape(QFrame.StyledPanel)
        self.settings_frame.setObjectName("settingsFrame")
        self.settings_layout = QVBoxLayout(self.settings_frame)
        self.settings_layout.setContentsMargins(15, 15, 15, 15)

        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        self.settings_layout.addWidget(self.settings_content)
        self.settings_layout.addStretch()

        self.splitter.addWidget(self.settings_frame)
        self.splitter.setSizes([600, 400])

        self.layout.addWidget(self.splitter)

    def _create_resource_selection_widget(self):
        resource_widget = QWidget()
        resource_layout = QVBoxLayout(resource_widget)
        resource_layout.setContentsMargins(0, 0, 10, 0)

        resource_label = QLabel("资源选择")
        resource_label.setFont(QFont("Arial", 12, QFont.Bold))
        resource_label.setObjectName("sectionTitle")
        resource_layout.addWidget(resource_label)

        # 获取所有可用资源
        all_resources = self.global_config.get_all_resource_configs()
        # 构造设备资源启用状态映射
        resource_enabled_map = {r.resource_name: r.enable for r in self.device_config.resources}

        self.resource_table = QTableWidget(len(all_resources), 3)
        self.resource_table.setObjectName("resourceTable")
        self.resource_table.setHorizontalHeaderLabels(["启用", "资源名称", "操作"])
        self.resource_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resource_table.verticalHeader().setVisible(False)
        self.resource_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.setFrameShape(QFrame.NoFrame)

        for row, resource_config in enumerate(all_resources):
            resource_name = resource_config.resource_name

            # 复选框：更新资源启用状态（调用父页面方法）
            checkbox = QCheckBox()
            checkbox.setChecked(resource_enabled_map.get(resource_name, False))
            checkbox.stateChanged.connect(
                lambda state, r_name=resource_name, cb=checkbox:
                self.parent_detail_page.update_resource_enable_status(r_name, cb.isChecked())
            )
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(5, 2, 5, 2)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            self.resource_table.setCellWidget(row, 0, checkbox_widget)

            # 资源名称
            name_item = QTableWidgetItem(f"{resource_name}")
            self.resource_table.setItem(row, 1, name_item)

            # 操作按钮：“运行”与“设置”
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)

            run_btn = QPushButton("运行")
            run_btn.setFixedWidth(60)
            run_btn.setObjectName("runButton")
            run_btn.clicked.connect(lambda checked, r_name=resource_name:
                                    self.manager.run_resource_task(self.device_config, r_name))

            settings_btn = QPushButton("设置")
            settings_btn.setFixedWidth(60)
            settings_btn.setObjectName("settingsButton")
            settings_btn.clicked.connect(lambda checked, r_name=resource_name:
                                         self.parent_detail_page.show_resource_settings(r_name))

            button_layout.addWidget(run_btn)
            button_layout.addWidget(settings_btn)
            self.resource_table.setCellWidget(row, 2, button_widget)
            self.resource_table.setRowHeight(row, 35)

        resource_layout.addWidget(self.resource_table)

        # “一键启动”按钮
        one_key_start_btn = QPushButton("一键启动")
        one_key_start_btn.setFixedHeight(40)
        one_key_start_btn.setObjectName("oneKeyButton")
        one_key_start_btn.clicked.connect(lambda: self.manager.run_device_all_resource_task(self.device_config))
        resource_layout.addWidget(one_key_start_btn)

        return resource_widget

    def show_resource_settings(self, device_resource, full_resource_config):
        """显示并构建资源设置界面"""
        self._clear_layout(self.settings_content_layout)
        self._create_resource_settings_ui(device_resource, full_resource_config)

    def _create_resource_settings_ui(self, device_resource, full_resource_config):
        # 资源名称标题
        resource_name_label = QLabel(f"{device_resource.resource_name} 设置")
        resource_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        resource_name_label.setObjectName("resourceSettingsTitle")
        self.settings_content_layout.addWidget(resource_name_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # 使用 DraggableContainer 作为滚动区域内的容器
        scroll_content = DraggableContainer()
        scroll_content.setObjectName('draggableContainer')
        scroll_content.layout.installEventFilter(self)  # 添加事件过滤器
        scroll_content.drag.connect(self.drag_connect)

        # 记录任务原始顺序和已选任务顺序
        task_order_map = {task.task_name: idx for idx, task in enumerate(full_resource_config.resource_tasks)}
        selected_order = {task_name: idx for idx, task_name in enumerate(device_resource.selected_tasks or [])}

        # 排序任务：已选择的任务优先，按原始顺序排序
        sorted_tasks = sorted(
            full_resource_config.resource_tasks,
            key=lambda task: (
                0 if task.task_name in selected_order else 1,
                selected_order.get(task.task_name, task_order_map.get(task.task_name, float('inf')))
            )
        )

        for task in sorted_tasks:
            options_widget = CollapsibleWidget(task.task_name)
            # 根据 selected_order 判断任务是否选中
            is_task_selected = task.task_name in selected_order
            options_widget.checkbox.setChecked(is_task_selected)

            # 任务选择状态改变时调用父页面更新回调
            options_widget.checkbox.stateChanged.connect(
                lambda state, t_name=task.task_name, cb=options_widget.checkbox:
                self.parent_detail_page.update_task_selection(device_resource, t_name, cb.isChecked())
            )

            # 如果任务有可配置选项，构建选项控件
            if task.option:
                for option_name in task.option:
                    for option in full_resource_config.options:
                        if option.name == option_name:
                            option_widget = self._create_option_widget(
                                option, option_name,
                                {opt.option_name: opt for opt in device_resource.options},
                                task.task_name,
                                {},
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

    def _create_option_widget(self, option, option_name, current_options, task_name, task_options_map, resource_config):
        """根据选项类型创建控件"""
        option_widget = QWidget()
        option_layout = QHBoxLayout(option_widget)
        option_layout.setContentsMargins(0, 2, 0, 2)
        option_layout.setSpacing(10)

        option_label = QLabel(option.name)
        option_layout.addWidget(option_label)
        option_layout.addStretch()

        if isinstance(option, SelectOption):
            widget = QComboBox()
            for choice in option.choices:
                widget.addItem(choice.name, choice.value)
            if option_name in current_options:
                index = widget.findData(current_options[option_name].value)
                if index >= 0:
                    widget.setCurrentIndex(index)
            widget.currentIndexChanged.connect(
                lambda index, w=widget, o_name=option_name, res_config=resource_config:
                self.parent_detail_page.update_option_value(res_config, o_name, w.currentData())
            )
        elif isinstance(option, BoolOption):
            widget = QCheckBox()
            if option_name in current_options:
                widget.setChecked(current_options[option_name].value)
            else:
                widget.setChecked(option.default)
            widget.stateChanged.connect(
                lambda state, o_name=option_name, cb=widget, res_config=resource_config:
                self.parent_detail_page.update_option_value(res_config, o_name, cb.isChecked())
            )
        elif isinstance(option, InputOption):
            widget = QLineEdit()
            if option_name in current_options:
                widget.setText(str(current_options[option_name].value))
            else:
                widget.setText(str(option.default))
            widget.editingFinished.connect(
                lambda o_name=option_name, le=widget, res_config=resource_config:
                self.parent_detail_page.update_option_value(res_config, o_name, le.text())
            )
        else:
            widget = QLabel("不支持的选项类型")

        option_layout.addWidget(widget)
        task_options_map[(task_name, option_name)] = widget

        return option_widget

    def drag_connect(self, current_order):
        """捕获拖拽事件，更新任务顺序"""
        try:
            device_name = self.parent_detail_page.selected_device_name
            resource_name = self.parent_detail_page.selected_resource_name
            if not (device_name and resource_name):
                return
            device_config = self.global_config.get_device_config(device_name)
            if not device_config:
                return
            resource_config = next((res for res in device_config.resources if res.resource_name == resource_name), None)
            if not resource_config:
                return
            resource_config.selected_tasks = [
                task for task in current_order if task in resource_config.selected_tasks
            ]
            self.global_config.save_all_configs()
        except Exception as e:
            print(f"Error in eventFilter: {e}")

    def _clear_layout(self, layout):
        """清除指定布局中的所有控件"""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())
