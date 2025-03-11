from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QTabWidget, QHBoxLayout, QLabel, QPushButton

from app.models.config.global_config import global_config
from app.pages.control_tab import ControlTab
from app.pages.info_tab import InfoTab
from app.pages.log_tab import LogTab
from core.tasker_manager import task_manager


class DeviceDetailPage(QWidget):
    # 定义返回信号
    back_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_config = global_config
        self.device_config = None
        self.manager = task_manager
        self.selected_device_name = None
        self.selected_resource_name = None

        self.init_ui()

    def init_ui(self):
        """初始化整体UI"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 详情区域
        self.detail_frame = QFrame()
        self.detail_frame.setFrameShape(QFrame.StyledPanel)
        self.detail_frame.setObjectName("deviceDetailFrame")

        self.detail_layout = QVBoxLayout(self.detail_frame)
        self.detail_layout.setContentsMargins(15, 15, 15, 15)

        self.layout.addWidget(self.detail_frame)

    def set_device_config(self, device_config):
        """设置设备配置并刷新UI"""
        self.device_config = device_config
        self._clear_layout(self.detail_layout)
        self._setup_detail_ui()

    def _setup_detail_ui(self):
        """设置详情页面UI（包含头部和选项卡）"""
        if not self.device_config:
            return

        # 头部区域：返回按钮与设备标题
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 10)

        back_btn = QPushButton("← 返回设备列表")
        back_btn.setObjectName("backButton")
        back_btn.clicked.connect(self._on_back_clicked)

        device_title = QLabel(f"设备详情: {self.device_config.device_name}")
        device_title.setFont(QFont("Arial", 14, QFont.Bold))
        device_title.setObjectName("deviceDetailTitle")

        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        header_layout.addWidget(device_title)
        header_layout.addStretch()
        self.detail_layout.addWidget(header_widget)

        # 创建选项卡控件
        tab_widget = QTabWidget()
        tab_widget.setObjectName("detailTabs")

        # “基本信息”选项卡
        self.info_tab = InfoTab(self.device_config)
        tab_widget.addTab(self.info_tab, "基本信息")

        # “操作面板”选项卡，将 self 作为回调传入
        self.control_tab = ControlTab(self.device_config, self.global_config, self.manager, self)
        tab_widget.addTab(self.control_tab, "操作面板")

        # “日志面板”选项卡
        self.log_tab = LogTab(self.device_config)
        tab_widget.addTab(self.log_tab, "日志面板")

        self.detail_layout.addWidget(tab_widget)

    def _on_back_clicked(self):
        """返回按钮点击事件"""
        self.back_signal.emit()

    def update_resource_enable_status(self, resource_name, is_enabled):
        """更新资源启用状态并立即保存"""
        try:
            device_resource = self._get_device_resource(resource_name)
            if not device_resource:
                from app.models.config.resource_config import Resource
                device_resource = Resource(
                    resource_name=resource_name,
                    enable=False,
                    selected_tasks=[],
                    options=[]
                )
                self.device_config.resources.append(device_resource)
            device_resource.enable = is_enabled
            self.global_config.save_all_configs()
        except Exception as e:
            print(f"Error updating resource enable status: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "保存失败", f"更新资源 '{resource_name}' 状态失败: {e}")

    def _get_device_resource(self, resource_name):
        """从设备配置中查找指定资源"""
        for resource in self.device_config.resources:
            if resource.resource_name == resource_name:
                return resource
        return None

    def show_resource_settings(self, resource_name):
        """显示资源设置（调用操作面板中的方法更新设置区域）"""
        self.selected_device_name = self.device_config.device_name
        self.selected_resource_name = resource_name

        # 获取全局资源配置
        full_resource_config = self.global_config.get_resource_config(resource_name)
        if not full_resource_config:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", f"找不到资源 '{resource_name}' 的配置")
            return

        # 获取或创建设备资源配置
        device_resource = self._get_device_resource(resource_name)
        if not device_resource:
            from app.models.config.resource_config import Resource
            device_resource = Resource(
                resource_name=resource_name,
                enable=False,
                selected_tasks=[],
                options=[]
            )
            self.device_config.resources.append(device_resource)

        # 委托 control_tab 显示资源设置
        self.control_tab.show_resource_settings(device_resource, full_resource_config)

    def update_task_selection(self, resource_config, task_name, is_selected):
        """更新任务选择状态并保存配置"""
        try:
            selected_tasks = resource_config.selected_tasks or []
            if is_selected:
                if task_name not in selected_tasks:
                    selected_tasks.append(task_name)
            else:
                if task_name in selected_tasks:
                    selected_tasks.remove(task_name)
            resource_config.selected_tasks = selected_tasks
            self.global_config.save_all_configs()
            print(f"Updated selected tasks: {selected_tasks}")
        except Exception as e:
            print(f"Error updating task selection: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "保存失败", f"更新任务 '{task_name}' 选择状态失败: {e}")

    def update_option_value(self, resource_config, option_name, value):
        """更新选项值并保存配置"""
        try:
            option_found = False
            for i, option in enumerate(resource_config.options):
                if option.option_name == option_name:
                    resource_config.options[i].value = value
                    option_found = True
                    break
            if not option_found:
                from app.models.config.device_config import OptionConfig
                new_option = OptionConfig(
                    option_name=option_name,
                    value=value
                )
                resource_config.options.append(new_option)
            self.global_config.save_all_configs()
        except Exception as e:
            print(f"Error updating option value: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "保存失败", f"更新选项 '{option_name}' 值失败: {e}")

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
