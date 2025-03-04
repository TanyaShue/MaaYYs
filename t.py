import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QCheckBox, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QMouseEvent

class CollapsibleWidget(QWidget):
    """可折叠组件，增加了拖动支持"""

    def __init__(self, title="折叠组件", parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.title_text = title
        self.dragging = False
        self.drag_start_pos = None  # 记录拖动起始位置（相对于drag_handle）
        self._init_ui()

    def _init_ui(self):
        # 主布局：标题栏 + 内容区
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 标题栏
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

        # 拖动句柄：占据中间区域，设置为透明
        self.drag_handle = QLabel()
        self.drag_handle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.drag_handle.setStyleSheet("background: transparent;")
        # 通过事件过滤器来处理拖动
        self.drag_handle.installEventFilter(self)

        # 折叠按钮
        self.toggle_button = QPushButton("▼")
        self.toggle_button.setFixedSize(24, 24)
        self.toggle_button.setStyleSheet("border: none; background: transparent;")
        self.toggle_button.clicked.connect(self.toggle_content)

        # 布局添加
        self.header_layout.addWidget(self.checkbox)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.drag_handle)
        self.header_layout.addWidget(self.toggle_button)

        # 内容区
        self.content_widget = QWidget()
        self.content_widget.setObjectName("collapsibleContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(25, 5, 10, 5)
        self.content_layout.setSpacing(5)
        self.content_widget.setMaximumHeight(0)

        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.content_widget)

        # 样式
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
        # 展开/收起动画
        content_height = self.content_layout.sizeHint().height() + 10
        animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        animation.setDuration(200)
        if self.is_expanded:
            animation.setStartValue(self.content_widget.height())
            animation.setEndValue(0)
            self.toggle_button.setText("▼")
        else:
            self.content_widget.setVisible(True)
            animation.setStartValue(0)
            animation.setEndValue(content_height)
            self.toggle_button.setText("▲")
        animation.start()
        self.is_expanded = not self.is_expanded

    def eventFilter(self, source, event):
        if source == self.drag_handle:
            if event.type() == QMouseEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    # 使用 position() 替代 pos() 并转换为 QPoint
                    self.drag_start_pos = event.position().toPoint()
                return True
            elif event.type() == QMouseEvent.MouseMove:
                if not self.dragging and self.drag_start_pos:
                    # 同样替换为 event.position().toPoint()
                    if (
                            event.position().toPoint() - self.drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                        self.dragging = True
                        container = self.getContainer()
                        if container:
                            start_pos_in_container = self.mapTo(container, self.drag_start_pos)
                            container.start_drag(self, start_pos_in_container)
                elif self.dragging:
                    container = self.getContainer()
                    if container:
                        # 使用 globalPosition() 替换 globalPos()
                        current_pos = self.mapTo(container, event.globalPosition().toPoint())
                        container.update_drag(self, current_pos)
                return True
            elif event.type() == QMouseEvent.MouseButtonRelease:
                if self.dragging:
                    container = self.getContainer()
                    if container:
                        current_pos = self.mapTo(container, event.globalPosition().toPoint())
                        container.end_drag(self, current_pos)
                    self.dragging = False
                    self.drag_start_pos = None
                return True
        return super().eventFilter(source, event)

    def getContainer(self):
        # 假定容器为 DraggableContainer
        parent = self.parentWidget()
        while parent:
            if isinstance(parent, DraggableContainer):
                return parent
            parent = parent.parentWidget()
        return None

# 容器控件，支持拖动排序与动画
class DraggableContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setAcceptDrops(True)
        self.dragged_widget = None
        self.drag_offset = QPoint(0, 0)
        # 蓝色提示线：显示当前插入位置
        self.drop_indicator = QFrame(self)
        self.drop_indicator.setStyleSheet("background-color: blue;")
        self.drop_indicator.setFixedHeight(2)
        self.drop_indicator.hide()

    def start_drag(self, widget, pos):
        """拖动开始：脱离布局，将widget设置为容器的子控件"""
        self.dragged_widget = widget
        widget_pos = widget.pos()
        self.drag_offset = pos - widget_pos
        # 从布局中移除控件
        self.layout.removeWidget(widget)
        # 重新设置父控件，并确保可见
        widget.setParent(self)
        widget.raise_()
        widget.show()

    def update_drag(self, widget, pos):
        """拖动过程中：更新控件位置并实时更新插入提示线"""
        if self.dragged_widget is widget:
            new_pos = pos - self.drag_offset
            # 限制新位置在容器范围内，防止控件拖出可见区域
            container_rect = self.rect()
            new_x = max(0, min(new_pos.x(), container_rect.width() - widget.width()))
            new_y = max(0, min(new_pos.y(), container_rect.height() - widget.height()))
            widget.move(new_x, new_y)
            self._update_drop_indicator(widget.pos())

    def _update_drop_indicator(self, widget_pos):
        """根据拖动组件当前的y坐标更新蓝色提示线的位置"""
        insert_index = 0
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            w = item.widget()
            if w:
                geo = w.geometry()
                if widget_pos.y() < geo.y() + geo.height() / 2:
                    insert_index = i
                    break
                else:
                    insert_index = i + 1

        # 计算提示线y坐标
        if insert_index == 0:
            y = 0
        elif insert_index >= self.layout.count():
            if self.layout.count() > 0:
                last_widget = self.layout.itemAt(self.layout.count()-1).widget()
                y = last_widget.geometry().bottom() + self.layout.spacing()
            else:
                y = 0
        else:
            target_widget = self.layout.itemAt(insert_index).widget()
            y = target_widget.geometry().y()
        self.drop_indicator.setGeometry(0, y - 1, self.width(), 2)
        self.drop_indicator.raise_()
        self.drop_indicator.show()

    def end_drag(self, widget, pos):
        """拖动结束：根据当前鼠标位置确定插入位置，并平滑动画到目标位置后重新插入布局"""
        self.drop_indicator.hide()
        insert_index = 0
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            w = item.widget()
            if w:
                geo = w.geometry()
                if pos.y() < geo.y() + geo.height() / 2:
                    insert_index = i
                    break
                else:
                    insert_index = i + 1

        # 计算目标y坐标：假设目标位置与其他控件对齐
        target_y = 0
        if insert_index == 0:
            target_y = 0
        elif insert_index >= self.layout.count():
            if self.layout.count() > 0:
                last_widget = self.layout.itemAt(self.layout.count()-1).widget()
                target_y = last_widget.geometry().bottom() + self.layout.spacing()
            else:
                target_y = 0
        else:
            target_widget = self.layout.itemAt(insert_index).widget()
            target_y = target_widget.geometry().y()

        # 平滑动画：将拖动组件移动到目标位置
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.setStartValue(widget.pos())
        # 保持x坐标不变，更新y坐标
        new_pos = QPoint(widget.pos().x(), target_y)
        animation.setEndValue(new_pos)
        # 动画结束后，将组件重新插入布局
        animation.finished.connect(lambda: self._finish_drop(widget, insert_index))
        animation.start()

    def _finish_drop(self, widget, insert_index):
        """动画完成后，将组件插入布局"""
        widget.setParent(self)
        self.layout.insertWidget(insert_index, widget)
        widget.show()
        self.dragged_widget = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 构造容器并加入几个示例组件
    container = DraggableContainer()
    container.setGeometry(100, 100, 300, 500)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(container)

    # 添加几个 CollapsibleWidget 示例（固定高度仅为了演示效果）
    for i in range(5):
        cw = CollapsibleWidget(f"组件 {i+1}")
        cw.setFixedHeight(80)
        container.layout.addWidget(cw)

    scroll_area.show()
    sys.exit(app.exec())
