# -*- coding: UTF-8 -*-
import os

from PySide6.QtCore import Qt, Signal, QObject, QRunnable, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog
)
from typing import Optional, Dict, Any

from src.ui.core.task_project_manager import AdbDevice, TaskProjectManager
from src.utils.config_programs import ProgramsJson


class WorkerSignals(QObject):
    """Worker信号类"""
    finished = Signal(list)  # 成功获取设备列表时发出
    error = Signal(str)      # 发生错误时发出

class DeviceRefreshWorker(QRunnable):
    """异步获取设备列表的Worker类"""
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            devices = self.manager.get_adb_devices()
            self.signals.finished.emit(devices)
        except Exception as e:
            self.signals.error.emit(str(e))

class AddProjectDialog(QDialog):
    projectAdded = Signal(str, str, dict)
    Manager = TaskProjectManager()

    def __init__(self, thread_pool,parent=None,):
        super().__init__(parent)
        current_dir = os.getcwd()

        self.programs_json_path = os.path.join(current_dir, "assets", "config", "programs.json")

        # 加载配置
        self.programs = ProgramsJson.load_from_file(self.programs_json_path)
        self.thread_pool = thread_pool
        self.setWindowTitle("添加项目")
        self.setMinimumWidth(400)

        self.setup_ui()

    def setup_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 项目名称输入布局
        name_layout = QHBoxLayout()
        name_label = QLabel("项目名称:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入项目名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        # 游戏选择布局
        program_layout = QHBoxLayout()
        program_label = QLabel("游戏:")
        self.program_box = QComboBox()
        self.program_box.setMinimumWidth(200)
        self.program_box.addItems([p.program_name for p in self.programs.programs])
        program_layout.addWidget(program_label)
        program_layout.addWidget(self.program_box)
        main_layout.addLayout(program_layout)

        # 下拉框和按钮组布局
        combo_layout = QHBoxLayout()
        self.combo_box = QComboBox()
        self.combo_box.setMinimumWidth(200)
        combo_layout.addWidget(self.combo_box)

        # 刷新按钮
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon('assets/icons/svg_icons/icon_search.svg'))
        self.refresh_btn.setFixedSize(30, 30)
        self.refresh_btn.setToolTip("刷新项目")
        self.refresh_btn.clicked.connect(self.refresh_items)
        combo_layout.addWidget(self.refresh_btn)

        # 编辑按钮
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon('assets/icons/svg_icons/icon_more_options.svg'))
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.setToolTip("编辑项目")
        self.edit_btn.clicked.connect(self.edit_items)
        combo_layout.addWidget(self.edit_btn)

        main_layout.addLayout(combo_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # 添加按钮
        self.add_btn = QPushButton("添加")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setFixedHeight(35)
        self.add_btn.clicked.connect(self.add_project)
        main_layout.addWidget(self.add_btn)

    def refresh_items(self):
        """异步刷新下拉框中的设备列表"""
        # 禁用刷新按钮，显示正在加载状态
        self.refresh_btn.setEnabled(False)
        self.combo_box.clear()
        self.combo_box.addItem("正在获取设备列表...")

        # 创建worker实例
        worker = DeviceRefreshWorker(self.Manager)

        # 连接信号
        worker.signals.finished.connect(self.handle_refresh_success)
        worker.signals.error.connect(self.handle_refresh_error)

        # 启动异步任务
        self.thread_pool.start(worker)

    def handle_refresh_success(self, devices):
        """处理设备列表刷新成功"""
        self.refresh_btn.setEnabled(True)
        self.combo_box.clear()

        for device in devices:
            try:
                device_data = device.to_dict()
                display_text = f"{device.name} ({device.address})"
                self.combo_box.addItem(display_text, device_data)
            except Exception as e:
                print(f"添加设备到下拉框时出错: {str(e)}")
                continue

    def handle_refresh_error(self, error_msg):
        """处理设备列表刷新错误"""
        self.refresh_btn.setEnabled(True)
        self.combo_box.clear()
        QMessageBox.warning(self, "错误", f"获取设备列表失败: {error_msg}")


    def get_selected_device(self) -> Optional[AdbDevice]:
        """获取当前选中的设备数据"""
        current_index = self.combo_box.currentIndex()
        if current_index >= 0:
            try:
                device_data = self.combo_box.itemData(current_index)

                if device_data:
                    return device_data
            except Exception as e:
                print(f"获取选中设备数据时出错: {str(e)}")
        return None

    def get_selected_program(self):
        """获取当前选中的项目名称"""
        current_index = self.program_box.currentIndex()
        if current_index >= 0:
            try:
                program_name = self.program_box.itemText(current_index)
                return program_name
            except Exception as e:
                print(f"获取选中项目名称时出错: {str(e)}")
        return None

    def edit_items(self):
        """显示当前选中设备的详细信息"""
        current_index = self.combo_box.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "警告", "请先选择一个设备")
            return

        device_data = self.combo_box.itemData(current_index)
        if not device_data:
            QMessageBox.warning(self, "警告", "未找到设备数据")
            return

        details_dialog = DeviceDetailsDialog(device_data, self)
        details_dialog.exec_()


    def add_project(self):
        """添加项目"""
        name = self.name_input.text()
        program = self.get_selected_program()
        selected_device = self.get_selected_device()
        if not name or not program:
            QMessageBox.warning(self, "警告", "请填写项目名称和程序路径")
            return

        if not selected_device:
            QMessageBox.warning(self, "警告", "请选择一个设备")
            return
        self.projectAdded.emit(name, program, selected_device)
        self.accept()

    def show_dialog(self):
        """显示对话框"""
        self.name_input.clear()
        # self.program_input.clear()
        self.show()

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QWidget,
    QFrame, QMessageBox, QTextEdit, QScrollArea,
    QFormLayout
)
from pathlib import WindowsPath
import json


class DeviceDetailsDialog(QDialog):
    """设备详情对话框"""

    def __init__(self, device_data, parent=None):
        super().__init__(parent)
        self.device_data = device_data
        self.setWindowTitle("设备详情")
        self.setMinimumSize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # 创建内容容器
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        form_layout.setSpacing(10)

        # 设备基本信息
        self.add_detail_item(form_layout, "设备名称", self.device_data.get('name', ''))
        self.add_detail_item(form_layout, "设备地址", self.device_data.get('address', ''))
        self.add_detail_item(form_layout, "ADB路径", str(self.device_data.get('adb_path', '')))

        # 转换并显示截图方法
        screencap_methods = self.device_data.get('screencap_methods', '0')
        screencap_desc = self.parse_screencap_methods(int(screencap_methods))
        self.add_detail_item(form_layout, "截图方法", f"{screencap_methods}\n{screencap_desc}")

        # 转换并显示输入方法
        input_methods = self.device_data.get('input_methods', '0')
        input_desc = self.parse_input_methods(int(input_methods))
        self.add_detail_item(form_layout, "输入方法", f"{input_methods}\n{input_desc}")

        # 显示配置信息
        config = self.device_data.get('config', {})
        if config:
            config_text = json.dumps(config, indent=2, ensure_ascii=False)
            self.add_detail_item(form_layout, "设备配置", config_text)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def add_detail_item(self, layout, label, value):
        """添加详情项"""
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(str(value))
        text_edit.setMinimumHeight(60)
        layout.addRow(QLabel(label + ":"), text_edit)

    def parse_screencap_methods(self, methods):
        """解析截图方法位掩码"""
        available_methods = []
        if methods & 1:
            available_methods.append("adb screencap")
        if methods & 2:
            available_methods.append("minicap")
        if methods & 4:
            available_methods.append("uiautomator")
        return "\n".join(available_methods) if available_methods else "无可用截图方法"

    def parse_input_methods(self, methods):
        """解析输入方法位掩码"""
        available_methods = []
        if methods & 1:
            available_methods.append("adb input")
        if methods & 2:
            available_methods.append("minitouch")
        return "\n".join(available_methods) if available_methods else "无可用输入方法"