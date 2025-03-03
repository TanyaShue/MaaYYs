from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

class CollapsibleWidget(QWidget):
    """可折叠组件：优化了展开/收缩动画避免闪烁"""

    def __init__(self, title="折叠组件", parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.title_text = title
        self._init_ui()

    def _init_ui(self):
        # 主布局：标题栏 + 内容区
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ========== 标题栏 ==========
        self.header_widget = QWidget()
        self.header_widget.setObjectName("collapsibleHeader")
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(5, 8, 5, 8)
        self.header_layout.setSpacing(10)

        # 复选框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(False)

        # 标题标签
        self.title_label = QLabel(self.title_text)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))

        # 展开/折叠按钮
        self.toggle_button = QPushButton("▼")
        self.toggle_button.setFixedSize(24, 24)
        self.toggle_button.setStyleSheet("border: none; background: transparent;")

        # 布局添加
        self.header_layout.addWidget(self.checkbox)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.toggle_button)

        # ========== 内容区 ==========
        self.content_widget = QWidget()
        self.content_widget.setObjectName("collapsibleContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(25, 5, 10, 5)  # 左边增加缩进
        self.content_layout.setSpacing(5)

        # 初始时内容区“收起”：最大高度设为 0（不隐藏，避免闪烁）
        self.content_widget.setMaximumHeight(0)
        # 注意：不再调用 setVisible(False)

        # 将标题栏和内容区加入主布局
        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.content_widget)

        # 连接点击信号
        self.toggle_button.clicked.connect(self.toggle_content)
        self.title_label.mousePressEvent = lambda event: self.toggle_content()

        # 样式设置
        self.setStyleSheet("""
            #collapsibleHeader {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            #collapsibleHeader:hover {
                background-color: #e9e9e9;
            }
            #collapsibleContent {
                background-color: #fcfcfc;
                border-left: 1px solid #ddd;
                margin-left: 15px;
            }
        """)

    def toggle_content(self):
        # 计算内容区展开时应有的高度（考虑边距）
        content_height = self.content_layout.sizeHint().height() + 10

        # 创建动画，目标属性为 maximumHeight
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(200)  # 设置动画时长

        if self.is_expanded:
            # 折叠时：从当前高度动画到 0
            self.animation.setStartValue(self.content_widget.height())
            self.animation.setEndValue(0)
            self.toggle_button.setText("▼")
            # 不再调用 setVisible(False) 避免隐藏后布局重新计算引起闪烁
        else:
            # 展开时：确保内容区可见（如果之前被设置过可见性变化）
            self.content_widget.setVisible(True)
            self.animation.setStartValue(0)
            self.animation.setEndValue(content_height)
            self.toggle_button.setText("▲")

        self.animation.start()
        self.is_expanded = not self.is_expanded
