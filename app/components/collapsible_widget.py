from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QApplication
)
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt, QMimeData
from PySide6.QtGui import QFont, QDrag, QPixmap, QMouseEvent

class CollapsibleWidget(QWidget):
    """可折叠组件：优化了展开/收缩动画避免闪烁，同时添加拖动功能"""

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

        # 拖动句柄：使用一个空白的QLabel填充标题栏中除按钮之外的区域
        self.drag_handle = QLabel()
        self.drag_handle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.drag_handle.setStyleSheet("background: transparent;")
        # 为拖动句柄绑定鼠标事件
        self.drag_handle.mousePressEvent = self.drag_handle_mouse_press
        self.drag_handle.mouseMoveEvent = self.drag_handle_mouse_move

        # 展开/折叠按钮
        self.toggle_button = QPushButton("▼")
        self.toggle_button.setFixedSize(24, 24)
        self.toggle_button.setStyleSheet("border: none; background: transparent;")

        # 布局添加（注意：去掉原来的addStretch，使用拖动句柄代替）
        self.header_layout.addWidget(self.checkbox)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.drag_handle)
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
        else:
            # 展开时：确保内容区可见
            self.content_widget.setVisible(True)
            self.animation.setStartValue(0)
            self.animation.setEndValue(content_height)
            self.toggle_button.setText("▲")

        self.animation.start()
        self.is_expanded = not self.is_expanded

    # --- 以下为拖动实现代码 ---
    def drag_handle_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        event.accept()

    def drag_handle_mouse_move(self, event: QMouseEvent):
        if not (event.buttons() & Qt.LeftButton):
            return
        # 若移动距离未达到拖动的阈值，则不启动拖动
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        # 启动拖动操作
        drag = QDrag(self)
        mimeData = QMimeData()
        # 使用 widget 的 id 作为标识（也可以使用其他唯一标识）
        mimeData.setText(str(id(self)))
        drag.setMimeData(mimeData)
        # 制作一个widget的快照作为拖动时的图片
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.exec(Qt.MoveAction)



class DraggableContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setAcceptDrops(True)

        # 创建一个蓝色提示线，初始时隐藏
        self.drop_indicator = QFrame(self)
        self.drop_indicator.setStyleSheet("background-color: blue;")
        self.drop_indicator.setFixedHeight(2)
        self.drop_indicator.hide()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.drop_indicator.show()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        pos = event.pos()
        # 默认插入到末尾
        insert_index = self.layout.count()
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if not item.widget():
                continue
            widget = item.widget()
            geo = widget.geometry()
            # 如果鼠标位置在某个控件上半部分，则插入到该控件之前
            if pos.y() < geo.y() + geo.height() / 2:
                insert_index = i
                break

        # 根据插入位置计算提示线的 y 坐标
        if insert_index == 0:
            y = 0
        elif insert_index >= self.layout.count():
            # 从布局最后向前查找最后一个有效控件
            last_widget = None
            for i in range(self.layout.count() - 1, -1, -1):
                w = self.layout.itemAt(i).widget()
                if w is not None:
                    last_widget = w
                    break
            if last_widget:
                y = last_widget.geometry().bottom()
            else:
                y = self.height()  # 没有控件时使用容器高度作为默认值
        else:
            target_widget = self.layout.itemAt(insert_index).widget()
            if target_widget:
                y = target_widget.geometry().y()
            else:
                y = self.height()

        # 调整提示线的位置和宽度
        self.drop_indicator.setGeometry(0, y - 1, self.width(), 2)
        self.drop_indicator.raise_()
        self.drop_indicator.show()

    def dragLeaveEvent(self, event):
        self.drop_indicator.hide()
        event.accept()

    def dropEvent(self, event):
        # 隐藏提示线
        self.drop_indicator.hide()
        # 从 mimeData 中获取拖动控件的 id
        widget_id = int(event.mimeData().text())
        dragged_widget = None
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            widget = item.widget()
            if widget and id(widget) == widget_id:
                dragged_widget = widget
                break
        if dragged_widget:
            pos = event.pos()
            # 根据拖动位置计算插入索引：如果 pos.y() 在某个控件上半部分，则插入到该控件前面
            insert_index = self.layout.count()  # 默认插入到末尾
            for i in range(self.layout.count()):
                widget = self.layout.itemAt(i).widget()
                if widget:
                    geo = widget.geometry()
                    if pos.y() < geo.y() + geo.height() / 2:
                        insert_index = i
                        break
            # 移除再插入拖动控件
            self.layout.removeWidget(dragged_widget)
            self.layout.insertWidget(insert_index, dragged_widget)
        event.acceptProposedAction()
