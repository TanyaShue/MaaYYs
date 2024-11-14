# -*- coding: UTF-8 -*-
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QWidget,
    QFrame, QMessageBox
)
import json
from typing import Optional, Dict, Any

from ui.core.task_project_manager import AdbDevice, TaskProjectManager, TaskCommunicationError


class AddProjectDialog(QDialog):
    projectAdded = Signal(str, str, str)
    Manager = TaskProjectManager()

    def __init__(self, parent=None, api_url="http://your-api-endpoint/get_all_devices"):
        super().__init__(parent)
        self.api_url = api_url
        self.setWindowTitle("添加项目")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        # 前面的UI设置代码保持不变...
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 项目名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("项目名称:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入项目名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        # 游戏程序输入
        program_layout = QHBoxLayout()
        program_label = QLabel("游戏:")
        self.program_input = QLineEdit()
        self.program_input.setPlaceholderText("请输入游戏名称")
        program_layout.addWidget(program_label)
        program_layout.addWidget(self.program_input)
        main_layout.addLayout(program_layout)

        # 下拉框和按钮组
        combo_layout = QHBoxLayout()
        self.combo_box = QComboBox()
        self.combo_box.setMinimumWidth(200)
        combo_layout.addWidget(self.combo_box)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedSize(30, 30)
        self.refresh_btn.clicked.connect(self.refresh_items)
        combo_layout.addWidget(self.refresh_btn)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.clicked.connect(self.edit_items)
        combo_layout.addWidget(self.edit_btn)

        main_layout.addLayout(combo_layout)

        # 分隔线
        line = QFrame()
        main_layout.addWidget(line)

        # 添加按钮
        self.add_btn = QPushButton("添加")
        self.add_btn.setObjectName("addButton")
        self.add_btn.setFixedHeight(35)
        self.add_btn.clicked.connect(self.add_project)
        main_layout.addWidget(self.add_btn)



    def refresh_items(self):
        """刷新下拉框中的设备列表"""
        self.combo_box.clear()
        try:
            devices = self.Manager.get_adb_devices()
        except TaskCommunicationError as e:
            QMessageBox.warning(self, "错误", f"获取设备数据失败: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "错误", f"解析设备数据失败: {str(e)}")
            return []
        except Exception as e:
            QMessageBox.warning(self, "错误", f"处理设备数据时出错: {str(e)}")
            return []
        for device in devices:
            try:
                # 为设备创建用户数据字典，将大整数转换为字符串
                device_data = device.to_dict()

                display_text = f"{device.name} ({device.address})"

                # 将转换后的数据添加到下拉框
                self.combo_box.addItem(display_text, device_data)

            except Exception as e:
                print(f"添加设备到下拉框时出错: {str(e)}")
                continue

    def get_selected_device(self) -> Optional[AdbDevice]:
        """获取当前选中的设备数据"""
        current_index = self.combo_box.currentIndex()
        if current_index >= 0:
            try:
                device_data = self.combo_box.itemData(current_index)
                if device_data:
                    return AdbDevice.from_dict(device_data)
            except Exception as e:
                print(f"获取选中设备数据时出错: {str(e)}")
        return None

    def edit_items(self):
        """编辑下拉框项目"""
        # 在这里实现编辑逻辑
        pass

    def add_project(self):
        """添加项目"""
        name = self.name_input.text()
        program = self.program_input.text()
        selected_device = self.get_selected_device()

        if not name or not program:
            QMessageBox.warning(self, "警告", "请填写项目名称和程序路径")
            return

        if not selected_device:
            QMessageBox.warning(self, "警告", "请选择一个设备")
            return

        self.projectAdded.emit(name, program, selected_device.address)
        self.accept()

    def show_dialog(self):
        """显示对话框"""
        self.name_input.clear()
        self.program_input.clear()
        self.show()