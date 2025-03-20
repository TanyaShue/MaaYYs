from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QScrollArea, QCheckBox, QComboBox, QLineEdit, QToolButton, QPushButton, QSizePolicy
)

from app.models.config.global_config import global_config
from app.models.logging.log_manager import log_manager
from app.components.collapsible_widget import CollapsibleWidget, DraggableContainer
from app.models.config.resource_config import SelectOption, BoolOption, InputOption


class TaskSettingsWidget(QFrame):
    """Task settings widget for configuring resource tasks"""

    def __init__(self, device_config, parent=None):
        super().__init__(parent)
        self.device_config = device_config
        self.selected_resource_name = None
        self.task_option_widgets = {}
        self.status_indicator = None
        self.status_dot = None
        self.status_text = None

        self.setObjectName("taskSettingsFrame")
        self.setFrameShape(QFrame.StyledPanel)

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)

        # Header with title and help button
        header_layout = QHBoxLayout()

        # Section title
        section_title = QLabel("任务设置")
        section_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        section_title.setObjectName("sectionTitle")

        # Help button
        help_btn = QToolButton()
        help_btn.setIcon(QIcon("assets/icons/help.svg"))
        help_btn.setIconSize(QSize(16, 16))
        help_btn.setToolTip("任务设置帮助")
        help_btn.setObjectName("helpButton")

        header_layout.addWidget(section_title)
        header_layout.addStretch()
        header_layout.addWidget(help_btn)

        self.layout.addLayout(header_layout)

        # Content area with card-like appearance
        content_card = QFrame()
        content_card.setObjectName("contentCard")
        content_card.setFrameShape(QFrame.StyledPanel)

        card_layout = QVBoxLayout(content_card)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # Content area for resource settings (initially empty)
        self.settings_content = QWidget()
        self.settings_content_layout = QVBoxLayout(self.settings_content)
        self.settings_content_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_content_layout.setSpacing(15)

        # Add initial message with icon
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_layout.setSpacing(15)

        placeholder_icon = QLabel()
        placeholder_icon.setPixmap(QIcon("assets/icons/settings-gear.svg").pixmap(48, 48))
        placeholder_icon.setAlignment(Qt.AlignCenter)

        initial_message = QLabel("请从左侧资源列表中选择一个资源进行设置")
        initial_message.setAlignment(Qt.AlignCenter)
        initial_message.setObjectName("placeholderText")

        sub_message = QLabel("点击资源列表中的设置按钮来配置任务")
        sub_message.setAlignment(Qt.AlignCenter)
        sub_message.setObjectName("subText")

        placeholder_layout.addWidget(placeholder_icon)
        placeholder_layout.addWidget(initial_message)
        placeholder_layout.addWidget(sub_message)

        self.settings_content_layout.addWidget(placeholder_widget)

        card_layout.addWidget(self.settings_content)
        self.layout.addWidget(content_card)
        self.layout.addStretch()

    def show_resource_settings(self, resource_name):
        """Show settings for the selected resource with enhanced styling"""
        self.selected_resource_name = resource_name

        # Clear current settings content
        self._clear_layout(self.settings_content_layout)

        # Get resource configurations
        full_resource_config = global_config.get_resource_config(resource_name)
        if not full_resource_config:
            # Show error message if resource config not found
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_layout.setAlignment(Qt.AlignCenter)

            error_icon = QLabel()
            error_icon.setPixmap(QIcon("assets/icons/error.svg").pixmap(48, 48))
            error_icon.setAlignment(Qt.AlignCenter)

            error_label = QLabel(f"未找到资源 {resource_name} 的配置信息")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setObjectName("errorText")

            error_layout.addWidget(error_icon)
            error_layout.addWidget(error_label)

            self.settings_content_layout.addWidget(error_widget)
            return

        # Get device-specific resource config
        device_resource = None
        if self.device_config:
            device_resource = next((r for r in self.device_config.resources if r.resource_name == resource_name), None)

        if not device_resource:
            # Show message if device has no configuration for this resource
            no_config_widget = QWidget()
            no_config_layout = QVBoxLayout(no_config_widget)
            no_config_layout.setAlignment(Qt.AlignCenter)

            warning_icon = QLabel()
            warning_icon.setPixmap(QIcon("assets/icons/warning.svg").pixmap(48, 48))
            warning_icon.setAlignment(Qt.AlignCenter)

            no_config_label = QLabel(f"设备未配置资源 {resource_name}")
            no_config_label.setAlignment(Qt.AlignCenter)
            no_config_label.setObjectName("warningText")

            action_btn = QPushButton("添加资源配置")
            action_btn.setObjectName("primaryButton")
            action_btn.setFixedWidth(150)

            no_config_layout.addWidget(warning_icon)
            no_config_layout.addWidget(no_config_label)
            no_config_layout.addSpacing(15)
            no_config_layout.addWidget(action_btn, 0, Qt.AlignCenter)

            self.settings_content_layout.addWidget(no_config_widget)
            return

        # Create resource settings UI with header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        resource_name_label = QLabel(f"{resource_name}")
        resource_name_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        resource_name_label.setObjectName("resourceSettingsTitle")

        # Add resource status indicator
        self.status_indicator = QWidget()
        status_layout = QHBoxLayout(self.status_indicator)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet(
            f"background-color: {'#34a853' if device_resource.enable else '#ea4335'}; border-radius: 4px;")

        self.status_text = QLabel(f"{'已启用' if device_resource.enable else '已禁用'}")
        self.status_text.setObjectName("statusText")
        self.status_text.setStyleSheet(f"color: {'#34a853' if device_resource.enable else '#ea4335'}; font-size: 12px;")

        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_text)

        header_layout.addWidget(resource_name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)

        self.settings_content_layout.addWidget(header_widget)

        # Add description if available
        if hasattr(full_resource_config, 'description') and full_resource_config.description:
            description_label = QLabel(full_resource_config.description)
            description_label.setObjectName("resourceDescription")
            description_label.setWordWrap(True)
            description_label.setContentsMargins(0, 0, 0, 10)
            self.settings_content_layout.addWidget(description_label)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumHeight(1)
        separator.setObjectName("separator")
        self.settings_content_layout.addWidget(separator)
        self.settings_content_layout.addSpacing(10)

        # Instructions for drag & drop
        instructions = QLabel("拖放任务可调整执行顺序")
        instructions.setObjectName("instructionText")
        instructions.setAlignment(Qt.AlignCenter)
        self.settings_content_layout.addWidget(instructions)
        self.settings_content_layout.addSpacing(10)

        # Create scroll area for tasks
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        # 禁用水平滚动条
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Create draggable container for tasks
        scroll_content = DraggableContainer()
        scroll_content.setObjectName('draggableContainer')
        # 减小最小宽度
        scroll_content.setMinimumWidth(200)  # 设置较小的最小宽度

        scroll_content.layout.setContentsMargins(5, 5, 5, 5)
        scroll_content.layout.setSpacing(10)
        scroll_content.layout.installEventFilter(self)
        scroll_content.drag.connect(self.on_drag_tasks)

        # 确保内容适应滚动区域宽度
        scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Get task order information
        task_order_map = {task.task_name: idx for idx, task in enumerate(full_resource_config.resource_tasks)}
        selected_order = {task_name: idx for idx, task_name in enumerate(device_resource.selected_tasks or [])}

        # Sort tasks by selection status and order
        sorted_tasks = sorted(
            full_resource_config.resource_tasks,
            key=lambda task: (
                0 if task.task_name in selected_order else 1,
                selected_order.get(task.task_name, task_order_map.get(task.task_name, float('inf')))
            )
        )

        # Create task widgets
        self.task_option_widgets = {}  # Store widgets for later reference

        for task in sorted_tasks:
            # Create collapsible widget
            options_widget = CollapsibleWidget(task.task_name)
            options_widget.setObjectName("taskItem")
            options_widget.setMinimumHeight(40)  # 设置最小高度

            is_task_selected = task.task_name in selected_order
            options_widget.checkbox.setChecked(is_task_selected)

            # 也不需要手动修改拖动区域宽度，因为已经在CollapsibleWidget中设置好了

            options_widget.checkbox.stateChanged.connect(
                lambda state, t_name=task.task_name, cb=options_widget.checkbox:
                self.update_task_selection(device_resource, t_name, cb.isChecked())
            )

            # Add option widgets if task has options
            if hasattr(task, 'option') and task.option:
                for option_name in task.option:
                    for option in full_resource_config.options:
                        if option.name == option_name:
                            option_widget = self._create_option_widget(
                                option, option_name,
                                {opt.option_name: opt for opt in device_resource.options},
                                task.task_name,
                                self.task_option_widgets,
                                device_resource
                            )
                            options_widget.content_layout.addWidget(option_widget)
            else:
                no_options_label = QLabel("该任务没有可配置的选项")
                no_options_label.setObjectName("noOptionsLabel")
                no_options_label.setWordWrap(True)
                options_widget.content_layout.addWidget(no_options_label)

            scroll_content.layout.addWidget(options_widget)

        scroll_content.layout.addStretch()
        scroll_area.setWidget(scroll_content)
        self.settings_content_layout.addWidget(scroll_area)

    def update_resource_status(self, resource_name, enabled):
        """Update the resource status in the UI when it changes in ResourceWidget"""
        # Only update if this is the currently selected resource
        if self.selected_resource_name == resource_name and self.status_dot and self.status_text:
            # Update status dot color
            self.status_dot.setStyleSheet(
                f"background-color: {'#34a853' if enabled else '#ea4335'}; border-radius: 4px;")

            # Update status text
            self.status_text.setText(f"{'已启用' if enabled else '已禁用'}")
            self.status_text.setStyleSheet(f"color: {'#34a853' if enabled else '#ea4335'}; font-size: 12px;")

            # Log the update
            log_manager.log_device_info(
                self.device_config.device_name if hasattr(self.device_config, 'device_name') else "未知设备",
                f"资源 {resource_name} 状态已在任务设置中更新"
            )

    def _create_option_widget(self, option, option_name, current_options, task_name, task_options_map, resource_config):
        """Create a widget for an option based on its type with enhanced styling"""
        option_widget = QWidget()
        option_widget.setObjectName("optionWidget")
        # 确保选项控件适应父容器宽度
        option_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        option_layout = QHBoxLayout(option_widget)
        # 减小边距，使其在较窄的容器中也能显示良好
        option_layout.setContentsMargins(5, 5, 5, 5)
        option_layout.setSpacing(8)  # 减小子元素间的间距

        # Option label with tooltip if description exists
        option_label = QLabel(option.name)
        option_label.setObjectName("optionLabel")
        # 禁止标签自动换行
        option_label.setWordWrap(False)
        # 设置固定最小宽度，防止标签占用太多空间
        option_label.setMinimumWidth(60)

        if hasattr(option, 'description') and option.description:
            option_label.setToolTip(option.description)
            info_icon = QLabel("ℹ️")
            info_icon.setFixedWidth(16)
            info_icon.setToolTip(option.description)
            option_layout.addWidget(info_icon)

        option_layout.addWidget(option_label)
        option_layout.addStretch()

        # Create control based on option type
        if isinstance(option, SelectOption):
            widget = QComboBox()
            widget.setObjectName("optionComboBox")
            # 设置下拉框适应可用空间的最小宽度
            widget.setMinimumWidth(80)

            for choice in option.choices:
                widget.addItem(choice.name, choice.value)
            if option_name in current_options:
                index = widget.findData(current_options[option_name].value)
                if index >= 0:
                    widget.setCurrentIndex(index)
            widget.currentIndexChanged.connect(
                lambda index, w=widget, o_name=option_name, res_config=resource_config:
                self.update_option_value(res_config, o_name, w.currentData())
            )
        elif isinstance(option, BoolOption):
            widget = QCheckBox()
            widget.setObjectName("optionCheckBox")
            if option_name in current_options:
                widget.setChecked(current_options[option_name].value)
            else:
                widget.setChecked(option.default)
            widget.stateChanged.connect(
                lambda state, o_name=option_name, cb=widget, res_config=resource_config:
                self.update_option_value(res_config, o_name, cb.isChecked())
            )
        elif isinstance(option, InputOption):
            widget = QLineEdit()
            widget.setObjectName("optionLineEdit")
            # 设置输入框适应可用空间
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            # 缩短输入框的最小宽度
            widget.setMinimumWidth(40)

            if option_name in current_options:
                widget.setText(str(current_options[option_name].value))
            else:
                widget.setText(str(option.default))
            widget.editingFinished.connect(
                lambda o_name=option_name, le=widget, res_config=resource_config:
                self.update_option_value(res_config, o_name, le.text())
            )

            # Add placeholder text based on option type
            if hasattr(option, 'option_type'):
                if option.option_type == 'number':
                    # For numeric input
                    widget.setPlaceholderText("输入数字...")
                elif option.option_type == 'text':
                    # For text input
                    widget.setPlaceholderText("输入文本...")
        else:
            widget = QLabel("不支持的选项类型")
            widget.setStyleSheet("color: #ea4335; font-style: italic;")
            widget.setWordWrap(True)

        option_layout.addWidget(widget)
        task_options_map[(task_name, option_name)] = widget

        return option_widget

    def update_task_selection(self, resource_config, task_name, is_selected):
        """Update task selection status with improved UI feedback"""
        if not resource_config:
            return

        if not hasattr(resource_config, 'selected_tasks') or resource_config.selected_tasks is None:
            resource_config.selected_tasks = []

        if is_selected and task_name not in resource_config.selected_tasks:
            resource_config.selected_tasks.append(task_name)
        elif not is_selected and task_name in resource_config.selected_tasks:
            resource_config.selected_tasks.remove(task_name)

        # Save the updated configuration
        global_config.save_all_configs()

        # Update task count label if present
        for i in range(self.settings_content_layout.count()):
            widget = self.settings_content_layout.itemAt(i).widget()
            if isinstance(widget, QWidget):
                count_label = widget.findChild(QLabel, "countLabel")
                if count_label and resource_config:
                    count_label.setText(f"{len(resource_config.selected_tasks or [])} 个已选择")
                    break

        # Log the change with more details
        status_text = "已选择" if is_selected else "已取消选择"
        device_name = resource_config.device_name if hasattr(resource_config, 'device_name') else "未知设备"
        resource_name = resource_config.resource_name if hasattr(resource_config, 'resource_name') else "未知资源"
        log_manager.log_device_info(device_name, f"资源 [{resource_name}] 的任务 [{task_name}] {status_text}")

    def update_option_value(self, resource_config, option_name, value):
        """Update option value for a resource with improved feedback"""
        if not resource_config:
            return

        if not hasattr(resource_config, 'options') or resource_config.options is None:
            resource_config.options = []

        # Find existing option or create a new one
        option = next((opt for opt in resource_config.options if opt.option_name == option_name), None)

        if option:
            # Convert value to appropriate type if needed
            if isinstance(option.value, bool) and not isinstance(value, bool):
                if str(value).lower() in ['true', '1', 'yes', 'y']:
                    value = True
                else:
                    value = False
            elif isinstance(option.value, int) and not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    # Log error if conversion fails
                    device_name = resource_config.device_name if hasattr(resource_config, 'device_name') else "未知设备"
                    log_manager.log_device_error(device_name, f"选项 {option_name} 的值 '{value}' 无法转换为整数")
                    return
            elif isinstance(option.value, float) and not isinstance(value, float):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    # Log error if conversion fails
                    device_name = resource_config.device_name if hasattr(resource_config, 'device_name') else "未知设备"
                    log_manager.log_device_error(device_name, f"选项 {option_name} 的值 '{value}' 无法转换为浮点数")
                    return

            # Save the previous value for comparison
            prev_value = option.value
            option.value = value

            # Save the updated configuration
            global_config.save_all_configs()

            # Create a readable string representation for logging
            if isinstance(value, bool):
                value_str = "启用" if value else "禁用"
            else:
                value_str = str(value)

            # Log the change with more details
            device_name = resource_config.device_name if hasattr(resource_config, 'device_name') else "未知设备"
            resource_name = resource_config.resource_name if hasattr(resource_config, 'resource_name') else "未知资源"
            log_manager.log_device_info(
                device_name,
                f"资源 [{resource_name}] 的选项 [{option_name}] 已更新: {prev_value} → {value_str}"
            )
        else:
            # Log error if option doesn't exist
            device_name = resource_config.device_name if hasattr(resource_config, 'device_name') else "未知设备"
            log_manager.log_device_error(device_name, f"选项 {option_name} 不存在，无法更新")
            return

    def on_drag_tasks(self, current_order):
        """Handle task drag-and-drop reordering"""
        if not hasattr(self, 'selected_resource_name') or not self.selected_resource_name:
            return

        if not self.device_config:
            return

        resource_config = next(
            (r for r in self.device_config.resources if r.resource_name == self.selected_resource_name), None)
        if not resource_config:
            return

        # Update task order
        resource_config.selected_tasks = [
            task for task in current_order if task in resource_config.selected_tasks
        ]

        # Save the updated configuration
        global_config.save_all_configs()

        # Log the change
        device_name = resource_config.device_name if hasattr(resource_config, 'device_name') else "未知设备"
        log_manager.log_device_info(device_name, f"资源 {self.selected_resource_name} 的任务顺序已更新")

    def clear_settings(self):
        """Clear the settings content"""
        self._clear_layout(self.settings_content_layout)

        # Add initial message with icon
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_layout.setSpacing(15)

        placeholder_icon = QLabel()
        placeholder_icon.setPixmap(QIcon("assets/icons/settings-gear.svg").pixmap(48, 48))
        placeholder_icon.setAlignment(Qt.AlignCenter)

        initial_message = QLabel("请从左侧资源列表中选择一个资源进行设置")
        initial_message.setAlignment(Qt.AlignCenter)
        initial_message.setObjectName("placeholderText")

        placeholder_layout.addWidget(placeholder_icon)
        placeholder_layout.addWidget(initial_message)

        self.settings_content_layout.addWidget(placeholder_widget)

    def _clear_layout(self, layout):
        """Clear all widgets from a layout"""
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())