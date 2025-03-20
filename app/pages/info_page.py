from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTextBrowser, QScrollArea, QSizePolicy, QPushButton,
    QSpacerItem, QTabWidget, QGridLayout
)


class InfoPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header with title and logo
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Logo placeholder - replace path with your actual logo
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("assets/icons/app_logo.png")
            logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            # Fallback if logo not found
            logo_label.setText("MFWPH")
            logo_label.setFont(QFont("Arial", 18, QFont.Bold))

        logo_label.setFixedSize(70, 70)
        header_layout.addWidget(logo_label)

        # Title and version
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        app_title = QLabel("MFWPH")
        app_title.setFont(QFont("Arial", 22, QFont.Bold))
        title_layout.addWidget(app_title)

        app_subtitle = QLabel("MaaFramework Project Helper")
        app_subtitle.setFont(QFont("Arial", 12))
        title_layout.addWidget(app_subtitle)

        version_label = QLabel("版本 1.0.0")
        version_label.setFont(QFont("Arial", 10))
        title_layout.addWidget(version_label)

        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        # GitHub button
        github_btn = QPushButton()
        github_btn.setIcon(QIcon("assets/icons/github.svg"))
        github_btn.setIconSize(QSize(24, 24))
        github_btn.setToolTip("访问项目 GitHub")
        github_btn.setFixedSize(40, 40)
        github_btn.setObjectName("githubButton")
        github_btn.setCursor(Qt.PointingHandCursor)
        # Connect to open GitHub page if needed
        # github_btn.clicked.connect(self.open_github)
        header_layout.addWidget(github_btn)

        main_layout.addWidget(header_widget)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Tabbed content
        tab_widget = QTabWidget()
        tab_widget.setDocumentMode(True)
        tab_widget.setObjectName("infoTabs")

        # About tab
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        about_layout.setContentsMargins(10, 15, 10, 10)
        about_layout.setSpacing(15)

        # Description
        description = QTextBrowser()
        description.setOpenExternalLinks(True)
        description.setFrameShape(QFrame.NoFrame)
        description.setStyleSheet("background: transparent;")
        description.setHtml("""
            <div style="font-family: Arial; font-size: 10pt; line-height: 1.5;">
                <p><b>MFWPH (MaaFramework Project Helper)</b> 是一款基于 MaaFramework 开源框架的自动化管理工具，专为多设备自动化操作设计。</p>

                <p>本应用支持同时操控多个设备执行自定义任务，实现高效、稳定的自动化操作流程。每个设备均可独立运行各种自定义资源任务，
                大幅提升了多设备管理效率。</p>

                <h3>核心功能</h3>
                <ul>
                    <li>多设备同时管理与监控</li>
                    <li>基于 MaaFramework 的高效自动化操作</li>
                    <li>自定义任务创建与执行</li>
                    <li>实时状态监控与日志记录</li>
                    <li>资源下载与自动更新</li>
                    <li>异常检测与自动恢复</li>
                </ul>

                <h3>技术架构</h3>
                <ul>
                    <li>基于 PySide6 构建的现代化 UI</li>
                    <li>集成 MaaFramework 核心功能</li>
                    <li>高性能设备通信模块</li>
                    <li>可扩展的插件系统</li>
                </ul>

                <p>MFWPH 致力于为用户提供一个高效、直观的多设备自动化解决方案，帮助用户节省时间并提高工作效率。</p>
            </div>
        """)
        about_layout.addWidget(description)

        # Features tab
        features_widget = QWidget()
        features_layout = QVBoxLayout(features_widget)
        features_layout.setContentsMargins(10, 15, 10, 10)

        features_scroll = QScrollArea()
        features_scroll.setWidgetResizable(True)
        features_scroll.setFrameShape(QFrame.NoFrame)

        features_content = QWidget()
        features_grid = QGridLayout(features_content)
        features_grid.setContentsMargins(0, 0, 0, 0)
        features_grid.setSpacing(20)

        # Feature items
        feature_items = [
            {"icon": "devices.svg", "title": "多设备管理",
             "desc": "同时连接并管理多台设备，支持各类模拟器和真机。"},
            {"icon": "automation.svg", "title": "自动化操作",
             "desc": "基于 MaaFramework 的高效识别与操作，精准模拟用户交互。"},
            {"icon": "task.svg", "title": "自定义任务",
             "desc": "创建、编辑和执行自定义任务流程，满足各种自动化需求。"},
            {"icon": "monitor.svg", "title": "实时监控",
             "desc": "全方位监控设备状态与任务执行情况，及时发现异常。"},
            {"icon": "resource.svg", "title": "资源管理",
             "desc": "便捷管理自动化资源，支持在线更新与本地导入。"},
            {"icon": "log.svg", "title": "日志系统",
             "desc": "详细记录操作日志，方便排查问题与优化流程。"}
        ]

        # Create feature items
        row, col = 0, 0
        for i, feature in enumerate(feature_items):
            item = self.create_feature_item(feature["icon"], feature["title"], feature["desc"])
            features_grid.addWidget(item, row, col)
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1

        features_content.setLayout(features_grid)
        features_scroll.setWidget(features_content)
        features_layout.addWidget(features_scroll)

        # Credits tab
        credits_widget = QWidget()
        credits_layout = QVBoxLayout(credits_widget)
        credits_layout.setContentsMargins(10, 15, 10, 10)

        credits_text = QTextBrowser()
        credits_text.setOpenExternalLinks(True)
        credits_text.setFrameShape(QFrame.NoFrame)
        credits_text.setStyleSheet("background: transparent;")
        credits_text.setHtml("""
            <div style="font-family: Arial; font-size: 10pt; line-height: 1.5;">
                <h3>鸣谢</h3>

                <p><b>MaaFramework</b><br>
                本项目基于 MaaFramework 开源框架，感谢 MaaFramework 团队的杰出贡献。<br>
                <a href="https://github.com/MaaAssistantArknights/MaaFramework">https://github.com/MaaAssistantArknights/MaaFramework</a></p>

                <h4>开源组件</h4>
                <ul>
                    <li><b>PySide6</b> - Qt for Python</li>
                    <li><b>OpenCV</b> - 计算机视觉库</li>
                    <li><b>ADB</b> - Android Debug Bridge</li>
                    <li><b>Python</b> - 编程语言</li>
                </ul>

                <h4>贡献者</h4>
                <p>感谢所有为本项目做出贡献的开发者与社区成员。</p>

                <h4>特别感谢</h4>
                <p>感谢所有用户的支持与反馈，您的参与是我们不断改进的动力。</p>

                <div style="margin-top: 20px; text-align: center;">
                    <p>© 2025 MFWPH Team. 保留所有权利。</p>
                </div>
            </div>
        """)
        credits_layout.addWidget(credits_text)

        # Add tabs
        tab_widget.addTab(about_widget, "关于")
        tab_widget.addTab(features_widget, "功能")
        tab_widget.addTab(credits_widget, "鸣谢")

        main_layout.addWidget(tab_widget)

    def create_feature_item(self, icon_name, title, description):
        """Create a feature item widget with icon, title and description"""
        item_widget = QFrame()
        item_widget.setObjectName("featureItem")
        item_widget.setFrameShape(QFrame.StyledPanel)
        item_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        item_widget.setMinimumHeight(120)

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(15, 15, 15, 15)

        # Feature icon
        icon_label = QLabel()
        try:
            icon_pixmap = QPixmap(f"assets/icons/{icon_name}")
            icon_label.setPixmap(icon_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            # Fallback if icon not found
            icon_label.setText("•")
            icon_label.setFont(QFont("Arial", 24, QFont.Bold))

        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        item_layout.addWidget(icon_label)

        # Title and description
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        text_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Arial", 10))
        text_layout.addWidget(desc_label)

        item_layout.addWidget(text_widget)

        return item_widget

    def open_github(self):
        """Open the GitHub repository page"""
        # Implement with QDesktopServices.openUrl() if needed
        pass
