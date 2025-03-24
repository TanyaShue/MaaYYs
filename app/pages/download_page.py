import os
import json
import time
import shutil
import requests
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QTableWidget,
                               QTableWidgetItem, QPushButton, QHeaderView, QHBoxLayout,
                               QProgressBar, QMessageBox, QSizePolicy, QDialog, QFormLayout,
                               QLineEdit, QTextEdit, QDialogButtonBox)

# Import GlobalConfig from the app
from app.models.config.global_config import global_config


class AddResourceDialog(QDialog):
    """Dialog for adding new resources"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("添加新资源")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Resource URL (GitHub repo or direct ZIP URL)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("GitHub仓库链接或ZIP文件URL")
        form_layout.addRow("资源链接:", self.url_edit)

        # Resource name (optional, extracted from ZIP if not provided)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("自动提取 (可选)")
        form_layout.addRow("资源名称:", self.name_edit)

        # # Resource type (model, plugin, etc.)
        # self.type_combo = QComboBox()
        # self.type_combo.addItems(["模型", "插件", "工具", "其他"])
        # form_layout.addRow("资源类型:", self.type_combo)

        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("资源描述 (可选)")
        self.desc_edit.setMaximumHeight(100)
        form_layout.addRow("描述:", self.desc_edit)

        layout.addLayout(form_layout)

        # Add buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Disable OK button initially
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        # Connect URL field to validation
        self.url_edit.textChanged.connect(self.validate_input)

        layout.addWidget(self.button_box)

    def validate_input(self):
        """Enable OK button only if URL is valid"""
        url = self.url_edit.text().strip()
        valid = url.startswith(("http://", "https://")) and (
                "github.com" in url or url.endswith(".zip")
        )
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(valid)

    def get_data(self):
        """Return the dialog data"""
        return {
            "url": self.url_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "type": self.type_combo.currentText(),
            "description": self.desc_edit.toPlainText().strip()
        }


class DownloadPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.download_threads = []
        self.load_resources()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 页面标题
        title_label = QLabel("资源下载")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setObjectName("pageTitle")
        layout.addWidget(title_label)

        # 下载信息面板
        download_frame = QFrame()
        download_frame.setFrameShape(QFrame.StyledPanel)
        download_layout = QVBoxLayout(download_frame)

        # 添加资源和一键更新按钮行
        top_buttons_layout = QHBoxLayout()

        # 添加新资源按钮
        self.add_resource_button = QPushButton("添加新资源")
        self.add_resource_button.setMinimumHeight(36)
        self.add_resource_button.setIcon(QIcon("assets/icons/add.png"))  # 假设有合适的图标
        self.add_resource_button.clicked.connect(self.show_add_resource_dialog)
        top_buttons_layout.addWidget(self.add_resource_button)

        top_buttons_layout.addStretch()

        # 一键更新按钮
        self.update_all_button = QPushButton("一键检查所有更新")
        self.update_all_button.setMinimumHeight(36)
        self.update_all_button.setFixedWidth(200)
        self.update_all_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.update_all_button.clicked.connect(self.check_for_updates)
        top_buttons_layout.addWidget(self.update_all_button)

        download_layout.addLayout(top_buttons_layout)

        # 可用资源表
        resources_label = QLabel("可用资源")
        resources_label.setFont(QFont("Arial", 14, QFont.Bold))
        resources_label.setObjectName("sectionTitle")
        download_layout.addWidget(resources_label)

        self.resources_table = QTableWidget(0, 5)
        self.resources_table.setHorizontalHeaderLabels(["资源名称", "版本", "作者", "描述", "操作"])
        self.resources_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.resources_table.verticalHeader().setVisible(False)
        download_layout.addWidget(self.resources_table)

        # 下载队列表
        queue_label = QLabel("下载队列")
        queue_label.setFont(QFont("Arial", 14, QFont.Bold))
        queue_label.setObjectName("sectionTitle")
        download_layout.addWidget(queue_label)

        self.queue_table = QTableWidget(0, 4)
        self.queue_table.setHorizontalHeaderLabels(["资源名称", "进度", "速度", "操作"])
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.queue_table.verticalHeader().setVisible(False)
        download_layout.addWidget(self.queue_table)

        layout.addWidget(download_frame)

    def show_add_resource_dialog(self):
        """显示添加新资源的对话框"""
        dialog = AddResourceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.add_new_resource(data)

    def add_new_resource(self, data):
        """添加新资源"""
        # 显示下载中状态
        self.add_resource_button.setEnabled(False)
        self.add_resource_button.setText("添加中...")

        # 创建临时目录
        temp_dir = Path("assets/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 处理GitHub和直接ZIP URL
        url = data["url"]
        if "github.com" in url and not url.endswith(".zip"):
            # 如果是GitHub仓库链接
            self.process_github_repo(url, data)
        else:
            # 直接下载ZIP
            self.download_resource_zip(url, data)

    def process_github_repo(self, repo_url, data):
        """处理GitHub仓库链接"""
        # 解析GitHub URL获取owner/repo
        try:
            parts = repo_url.split('github.com/')[1].split('/')
            if len(parts) < 2:
                self.add_resource_failed("GitHub地址格式不正确")
                return

            owner, repo = parts[0], parts[1]
            # 移除.git后缀（如果有）
            if repo.endswith('.git'):
                repo = repo[:-4]

            # 构建API URL
            api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

            # 获取最新版本信息
            response = requests.get(api_url)

            if response.status_code != 200:
                self.add_resource_failed(f"API返回错误 ({response.status_code})")
                return

            release_info = response.json()

            # 提取版本信息
            latest_version = release_info.get('tag_name', '').lstrip('v')

            # 如果没提供名称，使用仓库名
            if not data["name"]:
                data["name"] = repo

            # 查找ZIP资源
            download_url = None
            for asset in release_info.get('assets', []):
                if asset.get('name', '').endswith('.zip'):
                    download_url = asset.get('browser_download_url')
                    break

            if not download_url:
                self.add_resource_failed("找不到可下载的资源包")
                return

            # 下载ZIP资源
            self.download_resource_zip(download_url, data, latest_version)

        except Exception as e:
            self.add_resource_failed(str(e))

    def download_resource_zip(self, url, data, version=None):
        """下载资源ZIP文件"""
        # 添加到下载队列
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)

        # 设置资源名称
        resource_name = data["name"] if data["name"] else "新资源"
        self.queue_table.setItem(row, 0, QTableWidgetItem(resource_name))

        # 设置行高
        self.queue_table.setRowHeight(row, 45)  # 调整下载队列行高

        # 创建进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        self.queue_table.setCellWidget(row, 1, progress_bar)

        # 添加速度标签
        speed_label = QLabel("等待中...")
        self.queue_table.setCellWidget(row, 2, speed_label)

        # 添加取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(30)
        self.queue_table.setCellWidget(row, 3, cancel_btn)

        # 创建下载线程
        temp_dir = Path("assets/temp")
        download_thread = ResourceDownloadThread(resource_name, url, temp_dir, data, version)

        # 连接信号
        download_thread.progress_updated.connect(
            lambda r, p, s: self.update_download_progress(r, p, s)
        )
        download_thread.download_completed.connect(
            lambda r, p, d: self.resource_download_completed(r, p, d)
        )
        download_thread.download_failed.connect(
            lambda r, e: self.resource_download_failed(r, e)
        )

        # 保存线程引用
        self.download_threads.append(download_thread)

        # 连接取消按钮
        cancel_btn.clicked.connect(download_thread.cancel)

        # 开始下载
        download_thread.start()

    def update_download_progress(self, resource_name, progress, speed):
        """更新下载进度"""
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, 0)
            if item and item.text() == resource_name:
                progress_bar = self.queue_table.cellWidget(row, 1)
                if progress_bar:
                    progress_bar.setValue(int(progress))
                    progress_bar.setFormat(f"{int(progress)}%")

                speed_label = self.queue_table.cellWidget(row, 2)
                if speed_label:
                    speed_label.setText(f"{speed:.2f} MB/s")
                break

    def resource_download_completed(self, resource_name, file_path, data):
        """处理资源下载完成事件"""
        # 在队列中查找资源
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, 0)
            if item and item.text() == resource_name:
                # 从队列中移除
                self.queue_table.removeRow(row)
                break

        try:
            # 安装新资源
            self.install_new_resource(resource_name, file_path, data)

            # 重新加载资源列表
            self.load_resources()

            # 恢复添加按钮状态
            self.add_resource_button.setEnabled(True)
            self.add_resource_button.setText("添加新资源")

            # 显示成功消息
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar().showMessage(f"资源 {resource_name} 已成功添加", 5000)

        except Exception as e:
            self.resource_download_failed(resource_name, str(e))

    def resource_download_failed(self, resource_name, error):
        """处理资源下载失败事件"""
        # 在队列中查找资源
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, 0)
            if item and item.text() == resource_name:
                # 从队列中移除
                self.queue_table.removeRow(row)
                break

        # 恢复添加按钮状态
        self.add_resource_button.setEnabled(True)
        self.add_resource_button.setText("添加新资源")

        # 显示错误信息
        if hasattr(self.window(), 'statusBar'):
            self.window().statusBar().showMessage(f"添加资源失败: {error}", 5000)
        else:
            QMessageBox.warning(
                self,
                "添加失败",
                f"资源 {resource_name} 添加失败:\n{error}"
            )

    def add_resource_failed(self, error):
        """处理添加资源失败"""
        # 恢复按钮状态
        self.add_resource_button.setEnabled(True)
        self.add_resource_button.setText("添加新资源")

        # 显示错误信息
        if hasattr(self.window(), 'statusBar'):
            self.window().statusBar().showMessage(f"添加资源失败: {error}", 5000)
        else:
            QMessageBox.warning(
                self,
                "添加失败",
                f"添加资源失败:\n{error}"
            )

    def install_new_resource(self, resource_name, file_path, data):
        """安装新下载的资源"""
        try:
            # 解压ZIP文件到临时目录
            with tempfile.TemporaryDirectory() as extract_dir:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # 查找资源配置文件
                resource_config_path = None

                # 首先尝试找已有的resource_config.json
                for root, dirs, files in os.walk(extract_dir):
                    if "resource_config.json" in files:
                        resource_config_path = os.path.join(root, "resource_config.json")
                        resource_dir = root
                        break

                # 如果找不到配置文件，则创建一个
                if not resource_config_path:
                    # 查找包含主要文件的目录
                    main_dir = extract_dir
                    for item in os.listdir(extract_dir):
                        item_path = os.path.join(extract_dir, item)
                        if os.path.isdir(item_path) and not item.startswith('.'):
                            # 使用第一个非隐藏目录
                            main_dir = item_path
                            break

                    # 创建资源配置
                    resource_dir = main_dir
                    resource_config = {
                        "resource_name": data["name"] or resource_name,
                        "resource_version": data.get("version", "1.0.0"),
                        "resource_type": data["type"],
                        "resource_author": data.get("author", "未知"),
                        "resource_description": data["description"] or "从外部源添加的资源",
                        "resource_update_service": data["url"] if "github.com" in data["url"] else ""
                    }

                    # 写入配置文件
                    resource_config_path = os.path.join(resource_dir, "resource_config.json")
                    with open(resource_config_path, 'w', encoding='utf-8') as f:
                        json.dump(resource_config, f, ensure_ascii=False, indent=4)

                # 创建目标目录
                target_dir = Path(f"assets/resource/{resource_name.lower().replace(' ', '_')}")
                if target_dir.exists():
                    shutil.rmtree(target_dir)

                # 复制资源到目标目录
                shutil.copytree(resource_dir, target_dir)

                # 加载新资源配置
                global_config.load_resource_config(str(target_dir / "resource_config.json"))

        except Exception as e:
            raise Exception(f"安装资源失败: {str(e)}")

    def load_resources(self):
        """从GlobalConfig加载资源并显示在表格中"""
        # 获取所有资源
        resources = global_config.get_all_resource_configs()

        # 清空表格
        self.resources_table.setRowCount(0)

        # 添加资源到表格
        for i, resource in enumerate(resources):
            self.resources_table.insertRow(i)
            self.resources_table.setItem(i, 0, QTableWidgetItem(resource.resource_name))
            self.resources_table.setItem(i, 1, QTableWidgetItem(resource.resource_version))
            self.resources_table.setItem(i, 2, QTableWidgetItem(resource.resource_author))
            self.resources_table.setItem(i, 3, QTableWidgetItem(resource.resource_description))

            # 创建检查更新按钮
            check_btn = QPushButton("检查更新")
            check_btn.setProperty("resource_name", resource.resource_name)
            check_btn.setFixedHeight(30)
            check_btn.clicked.connect(lambda checked, r=resource: self.check_resource_update(r))
            check_btn.setStyleSheet("QPushButton { background-color: #f0f0f0; }")
            self.resources_table.setCellWidget(i, 4, check_btn)

        # 调整行高
        for i in range(self.resources_table.rowCount()):
            self.resources_table.setRowHeight(i, 45)  # 增加行高

    def check_for_updates(self):
        """检查所有资源的更新"""
        self.update_all_button.setText("正在检查更新...")
        self.update_all_button.setEnabled(False)
        self.update_all_button.setStyleSheet("background-color: #FFD700;")  # 设置为金黄色

        resources = global_config.get_all_resource_configs()

        # 使用单独的线程检查所有更新
        check_thread = CheckUpdatesThread(resources)
        check_thread.update_found.connect(self.handle_update_found)
        check_thread.check_completed.connect(self.handle_check_completed)
        check_thread.start()

        # 保存线程引用，防止垃圾回收
        self.download_threads.append(check_thread)

    def handle_update_found(self, resource_name, latest_version, current_version, download_url):
        """处理找到更新的事件"""
        # 查找资源对应的行
        for row in range(self.resources_table.rowCount()):
            item = self.resources_table.item(row, 0)
            if item and item.text() == resource_name:
                # 更新版本显示
                self.resources_table.item(row, 1).setText(f"{current_version} → {latest_version}")

                # 替换按钮为更新按钮
                update_btn = QPushButton("更新")
                update_btn.setProperty("resource_name", resource_name)
                update_btn.setProperty("download_url", download_url)
                update_btn.setProperty("version", latest_version)
                update_btn.setFixedHeight(30)
                update_btn.setStyleSheet("background-color: #4CAF50; color: white;")

                # 获取完整的资源对象
                resource = next((r for r in global_config.get_all_resource_configs()
                                 if r.resource_name == resource_name), None)

                if resource:
                    update_btn.clicked.connect(
                        lambda checked, r=resource, url=download_url, v=latest_version:
                        self.start_download(r, url, v)
                    )
                    self.resources_table.setCellWidget(row, 4, update_btn)
                break

    def handle_check_completed(self, total_checked, updates_found):
        """处理检查完成的事件"""
        self.update_all_button.setEnabled(True)

        if updates_found == 0:
            self.update_all_button.setText("一键检查所有更新")
            self.update_all_button.setStyleSheet("")  # 恢复默认样式

            # 在状态栏显示消息（不弹窗）
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar().showMessage(f"已检查 {total_checked} 个资源，所有资源均为最新版本。", 5000)
        else:
            self.update_all_button.setText(f"一键更新 ({updates_found})")
            self.update_all_button.setStyleSheet("background-color: #4CAF50; color: white;")
            self.update_all_button.clicked.disconnect()
            self.update_all_button.clicked.connect(self.update_all_resources)

    def update_all_resources(self):
        """更新所有有新版本的资源"""
        for row in range(self.resources_table.rowCount()):
            update_btn = self.resources_table.cellWidget(row, 4)
            if update_btn and isinstance(update_btn, QPushButton) and update_btn.text() == "更新":
                # 模拟点击更新按钮
                update_btn.click()

    def check_resource_update(self, resource):
        """检查特定资源的更新"""
        # 修改按钮为检查中
        for row in range(self.resources_table.rowCount()):
            item = self.resources_table.item(row, 0)
            if item and item.text() == resource.resource_name:
                check_btn = self.resources_table.cellWidget(row, 4)
                check_btn.setText("检查中...")
                check_btn.setEnabled(False)
                check_btn.setStyleSheet("background-color: #FFD700;")  # 设置为金黄色
                break

        # 创建单独的线程来检查更新
        check_thread = SingleResourceCheckThread(resource)
        check_thread.update_found.connect(
            lambda resource_name, latest_version, current_version, download_url:
            self.handle_single_update_found(resource_name, latest_version, current_version, download_url)
        )
        check_thread.update_not_found.connect(
            lambda resource_name:
            self.handle_single_update_not_found(resource_name)
        )
        check_thread.check_failed.connect(
            lambda resource_name, error_message:
            self.update_check_failed(resource_name, error_message)
        )

        # 保存线程引用，防止垃圾回收
        self.download_threads.append(check_thread)

        # 启动线程
        check_thread.start()

    def handle_single_update_found(self, resource_name, latest_version, current_version, download_url):
        """处理单个资源找到更新"""
        # 查找资源对应的行
        for row in range(self.resources_table.rowCount()):
            item = self.resources_table.item(row, 0)
            if item and item.text() == resource_name:
                # 更新版本显示
                self.resources_table.item(row, 1).setText(
                    f"{current_version} → {latest_version}"
                )

                # 获取完整的资源对象
                resource = next((r for r in global_config.get_all_resource_configs()
                                 if r.resource_name == resource_name), None)

                if resource:
                    # 更换为更新按钮
                    update_btn = QPushButton("更新")
                    update_btn.setProperty("resource_name", resource_name)
                    update_btn.setProperty("download_url", download_url)
                    update_btn.setProperty("version", latest_version)
                    update_btn.setFixedHeight(30)
                    update_btn.setStyleSheet("background-color: #4CAF50; color: white;")
                    update_btn.clicked.connect(
                        lambda checked, r=resource, url=download_url, v=latest_version:
                        self.start_download(r, url, v)
                    )
                    self.resources_table.setCellWidget(row, 4, update_btn)
                break

    def handle_single_update_not_found(self, resource_name):
        """处理单个资源未找到更新"""
        # 查找资源对应的行
        for row in range(self.resources_table.rowCount()):
            item = self.resources_table.item(row, 0)
            if item and item.text() == resource_name:
                # 已是最新版本
                check_btn = QPushButton("已是最新版本")
                check_btn.setFixedHeight(30)
                check_btn.setEnabled(False)
                check_btn.setStyleSheet("background-color: #E0E0E0;")
                self.resources_table.setCellWidget(row, 4, check_btn)

                # 使用QTimer在主线程中延迟恢复按钮状态
                from PySide6.QtCore import QTimer
                QTimer.singleShot(3000, lambda: self.restore_check_button(resource_name))
                break

    def restore_check_button(self, resource_name):
        """恢复检查更新按钮"""
        for row in range(self.resources_table.rowCount()):
            item = self.resources_table.item(row, 0)
            if item and item.text() == resource_name:
                # 获取完整的资源对象
                resource = next((r for r in global_config.get_all_resource_configs()
                                 if r.resource_name == resource_name), None)

                if resource:
                    # 恢复检查更新按钮
                    check_btn = QPushButton("检查更新")
                    check_btn.setFixedHeight(30)
                    check_btn.setStyleSheet("QPushButton { background-color: #f0f0f0; }")
                    check_btn.clicked.connect(lambda checked, r=resource: self.check_resource_update(r))
                    self.resources_table.setCellWidget(row, 4, check_btn)
                break

    def update_check_failed(self, resource_name, error_message):
        """处理更新检查失败的情况"""
        for row in range(self.resources_table.rowCount()):
            item = self.resources_table.item(row, 0)
            if item and item.text() == resource_name:
                # 恢复按钮
                check_btn = QPushButton("检查更新")
                check_btn.setFixedHeight(30)
                check_btn.setStyleSheet("QPushButton { background-color: #f0f0f0; }")

                # 获取完整的资源对象
                resource = next((r for r in global_config.get_all_resource_configs()
                                 if r.resource_name == resource_name), None)

                if resource:
                    check_btn.clicked.connect(lambda checked, r=resource: self.check_resource_update(r))
                    self.resources_table.setCellWidget(row, 4, check_btn)
                break

        # 在状态栏显示错误信息（如果有状态栏）
        if hasattr(self.window(), 'statusBar'):
            self.window().statusBar().showMessage(f"检查更新失败: {error_message}", 5000)

    def start_download(self, resource, url, version):
        """开始下载资源"""
        # 创建临时目录（如果不存在）
        temp_dir = Path("assets/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 添加到下载队列
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)
        self.queue_table.setItem(row, 0, QTableWidgetItem(resource.resource_name))

        # 设置行高
        self.queue_table.setRowHeight(row, 45)  # 调整下载队列行高

        # 创建进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("%p%")
        self.queue_table.setCellWidget(row, 1, progress_bar)

        # 添加速度标签
        speed_label = QLabel("等待中...")
        self.queue_table.setCellWidget(row, 2, speed_label)

        # 添加取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(30)
        self.queue_table.setCellWidget(row, 3, cancel_btn)

        # 更新资源表中的按钮状态
        for i in range(self.resources_table.rowCount()):
            item = self.resources_table.item(i, 0)
            if item and item.text() == resource.resource_name:
                downloading_btn = QPushButton("下载中...")
                downloading_btn.setFixedHeight(30)
                downloading_btn.setEnabled(False)
                downloading_btn.setStyleSheet("background-color: #FFD700;")  # 设置为金黄色
                self.resources_table.setCellWidget(i, 4, downloading_btn)
                break

        # 创建下载线程
        download_thread = DownloadThread(resource, url, temp_dir, version)
        download_thread.progress_updated.connect(
            lambda r, p, s: self.update_download_progress(r, p, s)
        )
        download_thread.download_completed.connect(
            lambda r, p: self.download_completed(r, p)
        )
        download_thread.download_failed.connect(
            lambda r, e: self.download_failed(r, e)
        )

        # 保存线程引用，防止垃圾回收
        self.download_threads.append(download_thread)

        # 连接取消按钮
        cancel_btn.clicked.connect(download_thread.cancel)

        # 开始下载
        download_thread.start()

    def download_completed(self, resource, file_path):
        """处理下载完成事件"""
        # 在队列中查找资源
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, 0)
            if item and item.text() == resource.resource_name:
                # 从队列中移除
                self.queue_table.removeRow(row)
                break

        # 安装更新
        try:
            self.install_update(resource, file_path)

            # 更新资源表中的状态
            for i in range(self.resources_table.rowCount()):
                item = self.resources_table.item(i, 0)
                if item and item.text() == resource.resource_name:
                    # 恢复检查更新按钮
                    check_btn = QPushButton("检查更新")
                    check_btn.setFixedHeight(30)
                    check_btn.setStyleSheet("QPushButton { background-color: #f0f0f0; }")

                    # 获取最新的资源数据
                    updated_resource = next((r for r in global_config.get_all_resource_configs()
                                             if r.resource_name == resource.resource_name), None)

                    if updated_resource:
                        # 更新版本显示
                        self.resources_table.setItem(i, 1, QTableWidgetItem(updated_resource.resource_version))
                        check_btn.clicked.connect(lambda checked, r=updated_resource: self.check_resource_update(r))
                        self.resources_table.setCellWidget(i, 4, check_btn)
                    break

            # 检查是否所有更新都已经完成
            all_completed = True
            for i in range(self.resources_table.rowCount()):
                update_btn = self.resources_table.cellWidget(i, 4)
                if update_btn and update_btn.text() == "更新":
                    all_completed = False
                    break

            if all_completed and self.update_all_button.text().startswith("一键更新"):
                # 恢复一键更新按钮状态
                self.update_all_button.setText("一键检查所有更新")
                self.update_all_button.setStyleSheet("")  # 恢复默认样式
                self.update_all_button.clicked.disconnect()
                self.update_all_button.clicked.connect(self.check_for_updates)

            # 显示成功消息
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar().showMessage(f"资源 {resource.resource_name} 已成功更新", 5000)

        except Exception as e:
            self.download_failed(resource.resource_name, str(e))

    def download_failed(self, resource_name, error):
        """处理下载失败事件"""
        # 在队列中查找资源
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, 0)
            if item and item.text() == resource_name:
                # 从队列中移除
                self.queue_table.removeRow(row)
                break

        # 更新资源表中的状态
        for i in range(self.resources_table.rowCount()):
            item = self.resources_table.item(i, 0)
            if item and item.text() == resource_name:
                # 恢复检查更新按钮
                check_btn = QPushButton("检查更新")
                check_btn.setFixedHeight(30)
                check_btn.setStyleSheet("QPushButton { background-color: #f0f0f0; }")

                # 获取完整的资源对象
                resource = next((r for r in global_config.get_all_resource_configs()
                                 if r.resource_name == resource_name), None)

                if resource:
                    check_btn.clicked.connect(lambda checked, r=resource: self.check_resource_update(r))
                    self.resources_table.setCellWidget(i, 4, check_btn)
                break

        # 显示错误信息
        if hasattr(self.window(), 'statusBar'):
            self.window().statusBar().showMessage(f"下载失败: {error}", 5000)
        else:
            QMessageBox.warning(
                self,
                "下载失败",
                f"资源 {resource_name} 下载失败:\n{error}"
            )

    def install_update(self, resource, file_path):
        """安装下载的更新"""
        try:
            # 解压ZIP文件到临时目录
            with tempfile.TemporaryDirectory() as extract_dir:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # 递归查找包含resource_config.json的目录
                resource_config_path = None
                resource_dir = None

                for root, dirs, files in os.walk(extract_dir):
                    if "resource_config.json" in files:
                        resource_config_path = os.path.join(root, "resource_config.json")
                        resource_dir = root
                        break

                if not resource_config_path:
                    raise ValueError("更新包中未找到resource_config.json文件")

                # 创建历史备份目录
                history_dir = Path("assets/history")
                history_dir.mkdir(parents=True, exist_ok=True)

                # 获取原资源目录
                original_resource_dir = Path(resource.source_file).parent

                # 创建带有时间戳的备份文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{resource.resource_name}_{resource.resource_version}_{timestamp}.zip"
                backup_path = history_dir / backup_filename

                # 压缩原资源目录到历史目录
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(original_resource_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, start=original_resource_dir.parent)
                            zipf.write(file_path, arcname)

                # 删除原资源目录
                if original_resource_dir.exists():
                    shutil.rmtree(original_resource_dir)

                # 将新资源目录移动到原位置
                shutil.copytree(resource_dir, original_resource_dir)

                # 重新加载资源配置
                global_config.load_resource_config(str(original_resource_dir / "resource_config.json"))

        except Exception as e:
            raise Exception(f"安装更新失败: {str(e)}")


class ResourceDownloadThread(QThread):
    """新资源下载线程"""
    progress_updated = Signal(str, float, float)  # resource_name, progress, speed
    download_completed = Signal(str, str, dict)  # resource_name, file_path, data
    download_failed = Signal(str, str)  # resource_name, error

    def __init__(self, resource_name, url, output_dir, data, version=None):
        super().__init__()
        self.resource_name = resource_name
        self.url = url
        self.output_dir = output_dir
        self.data = data
        self.version = version or "1.0.0"
        self.is_cancelled = False

    def run(self):
        try:
            # 创建输出文件名
            filename = f"{self.resource_name}_{self.version}.zip"
            output_path = self.output_dir / filename

            # 开始下载并报告进度
            response = requests.get(self.url, stream=True)
            response.raise_for_status()  # 抛出HTTP错误

            total_size = int(response.headers.get('content-length', 0))

            # 如果没有content-length头，使用默认大小
            if total_size == 0:
                total_size = 1024 * 1024  # 1MB默认

            # 计算块大小（总大小的1%）
            chunk_size = max(4096, total_size // 100)

            # 打开文件进行写入
            with open(output_path, 'wb') as f:
                downloaded = 0
                start_time = time.time()
                last_update_time = start_time

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.is_cancelled:
                        # 删除部分文件
                        f.close()
                        if output_path.exists():
                            output_path.unlink()
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 计算进度和速度
                        progress = (downloaded / total_size) * 100
                        current_time = time.time()
                        elapsed = current_time - last_update_time

                        # 每0.5秒更新一次速度
                        if elapsed >= 0.5:
                            speed = (chunk_size / 1024 / 1024) / elapsed  # MB/s
                            self.progress_updated.emit(self.resource_name, progress, speed)
                            last_update_time = current_time

            # 发送完成信号
            self.download_completed.emit(self.resource_name, str(output_path), self.data)

        except Exception as e:
            self.download_failed.emit(self.resource_name, str(e))

    def cancel(self):
        """取消下载"""
        self.is_cancelled = True


class DownloadThread(QThread):
    progress_updated = Signal(str, float, float)  # resource_name, progress, speed
    download_completed = Signal(object, str)  # resource, file_path
    download_failed = Signal(str, str)  # resource_name, error

    def __init__(self, resource, url, output_dir, version):
        super().__init__()
        self.resource = resource
        self.url = url
        self.output_dir = output_dir
        self.version = version
        self.is_cancelled = False

    def run(self):
        try:
            # 创建输出文件名
            filename = f"{self.resource.resource_name}_{self.version}.zip"
            output_path = self.output_dir / filename

            # 开始下载并报告进度
            response = requests.get(self.url, stream=True)
            response.raise_for_status()  # 抛出HTTP错误

            total_size = int(response.headers.get('content-length', 0))

            # 如果没有content-length头，使用默认大小
            if total_size == 0:
                total_size = 1024 * 1024  # 1MB默认

            # 计算块大小（总大小的1%）
            chunk_size = max(4096, total_size // 100)

            # 打开文件进行写入
            with open(output_path, 'wb') as f:
                downloaded = 0
                start_time = time.time()
                last_update_time = start_time

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.is_cancelled:
                        # 删除部分文件
                        f.close()
                        if output_path.exists():
                            output_path.unlink()
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 计算进度和速度
                        progress = (downloaded / total_size) * 100
                        current_time = time.time()
                        elapsed = current_time - last_update_time

                        # 每0.5秒更新一次速度
                        if elapsed >= 0.5:
                            speed = (chunk_size / 1024 / 1024) / elapsed  # MB/s
                            self.progress_updated.emit(self.resource.resource_name, progress, speed)
                            last_update_time = current_time

            # 发送完成信号
            self.download_completed.emit(self.resource, str(output_path))

        except Exception as e:
            self.download_failed.emit(self.resource.resource_name, str(e))

    def cancel(self):
        """取消下载"""
        self.is_cancelled = True


class SingleResourceCheckThread(QThread):
    """单个资源更新检查线程"""
    update_found = Signal(str, str, str, str)  # resource_name, latest_version, current_version, download_url
    update_not_found = Signal(str)  # resource_name
    check_failed = Signal(str, str)  # resource_name, error_message

    def __init__(self, resource):
        super().__init__()
        self.resource = resource

    def run(self):
        try:
            update_service = self.resource.resource_update_service

            # 处理GitHub资源（支持直接API URL和仓库URL）
            if update_service.startswith("https://api.github.com/repos/"):
                # 直接使用API URL
                api_url = update_service
            elif update_service.startswith("https://github.com/"):
                # 解析GitHub URL获取owner/repo
                try:
                    parts = update_service.split('github.com/')[1].split('/')
                    if len(parts) < 2:
                        self.check_failed.emit(
                            self.resource.resource_name,
                            f"GitHub地址格式不正确: {update_service}"
                        )
                        return

                    owner, repo = parts[0], parts[1]

                    # 移除.git后缀（如果有）
                    if repo.endswith('.git'):
                        repo = repo[:-4]

                    # 从GitHub URL构建API URL
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                except Exception as e:
                    self.check_failed.emit(
                        self.resource.resource_name,
                        f"解析GitHub地址时出错: {str(e)}"
                    )
                    return
            else:
                self.check_failed.emit(
                    self.resource.resource_name,
                    f"不支持的更新源: {update_service}"
                )
                return

            # 从GitHub API获取最新版本信息
            response = requests.get(api_url)

            if response.status_code != 200:
                self.check_failed.emit(
                    self.resource.resource_name,
                    f"API返回错误 ({response.status_code})"
                )
                return

            release_info = response.json()
            latest_version = release_info.get('tag_name', '').lstrip('v')

            # 比较版本
            if latest_version != self.resource.resource_version:
                # 有更新可用
                download_url = None

                # 查找下载URL
                for asset in release_info.get('assets', []):
                    if asset.get('name', '').endswith('.zip'):
                        download_url = asset.get('browser_download_url')
                        break

                if download_url:
                    # 发送找到更新信号
                    self.update_found.emit(
                        self.resource.resource_name,
                        latest_version,
                        self.resource.resource_version,
                        download_url
                    )
                else:
                    # 没找到下载链接
                    self.check_failed.emit(
                        self.resource.resource_name,
                        "找不到可下载的资源包"
                    )
            else:
                # 没有更新，已是最新版本
                self.update_not_found.emit(self.resource.resource_name)

        except Exception as e:
            # 检查失败
            self.check_failed.emit(self.resource.resource_name, str(e))


class CheckUpdatesThread(QThread):
    update_found = Signal(str, str, str, str)  # resource_name, latest_version, current_version, download_url
    check_completed = Signal(int, int)  # total_checked, updates_found

    def __init__(self, resources):
        super().__init__()
        self.resources = resources

    def run(self):
        updates_found = 0

        for resource in self.resources:
            update_service = resource.resource_update_service

            try:
                # 跳过没有更新服务的资源
                if not update_service:
                    continue

                # 处理GitHub资源
                if update_service.startswith("https://api.github.com/repos/"):
                    api_url = update_service
                elif update_service.startswith("https://github.com/"):
                    parts = update_service.split('github.com/')[1].split('/')
                    if len(parts) < 2:
                        continue

                    owner, repo = parts[0], parts[1]
                    if repo.endswith('.git'):
                        repo = repo[:-4]

                    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                else:
                    continue

                # 从GitHub API获取最新版本信息
                response = requests.get(api_url)
                if response.status_code != 200:
                    continue

                release_info = response.json()
                latest_version = release_info.get('tag_name', '').lstrip('v')

                # 比较版本
                if latest_version != resource.resource_version:
                    # 查找下载URL
                    download_url = None
                    for asset in release_info.get('assets', []):
                        if asset.get('name', '').endswith('.zip'):
                            download_url = asset.get('browser_download_url')
                            break

                    if download_url:
                        self.update_found.emit(
                            resource.resource_name,
                            latest_version,
                            resource.resource_version,
                            download_url
                        )
                        updates_found += 1

            except Exception:
                # 跳过出错的资源
                continue

        # 发送检查完成信号
        self.check_completed.emit(len(self.resources), updates_found)