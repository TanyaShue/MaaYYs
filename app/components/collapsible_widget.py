from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, Qt, QMimeData,
    QParallelAnimationGroup, QPoint, Property, Signal
)
from PySide6.QtGui import QFont, QDrag, QPixmap, QMouseEvent, QCursor, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QPushButton,
    QFrame, QSizePolicy, QApplication, QGraphicsOpacityEffect
)


class CollapsibleWidget(QWidget):
    """可折叠组件：优化了展开/收缩动画，添加了过渡效果和拖动功能"""

    def __init__(self, title="折叠组件", parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.title_text = title
        # 初始化旋转角度属性
        self._rotation_angle = 0
        self._init_ui()
        self._setup_animations()

    def _init_ui(self):
        # 主布局：标题栏 + 内容区
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ========== 标题栏 ==========
        self.header_widget = QWidget()
        self.header_widget.setObjectName("collapsibleHeader")
        self.header_widget.setFixedHeight(40)  # 设置固定高度
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(5, 0, 5, 0)  # 减小垂直边距
        self.header_layout.setSpacing(5)  # 减小间距

        # 复选框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(False)

        # 标题标签 - 让它靠近复选框
        self.title_label = QLabel(self.title_text)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))

        # 拖动句柄 - 设置为占据所有剩余空间
        self.drag_handle = QLabel("≡")  # 使用 ≡ 作为拖动图标
        self.drag_handle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.drag_handle.setStyleSheet("background: transparent; color: #80868b; font-size: 16px; padding-left: 5px;")
        self.drag_handle.setCursor(QCursor(Qt.OpenHandCursor))
        self.drag_handle.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 左对齐并垂直居中
        self.drag_handle.mousePressEvent = self.drag_handle_mouse_press
        self.drag_handle.mouseMoveEvent = self.drag_handle_mouse_move

        # 展开/折叠按钮 - 靠近右侧
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(QIcon("assets/icons/dropdown.svg"))
        self.toggle_button.setFixedSize(24, 24)
        self.toggle_button.setObjectName("toggleButton")

        # 布局添加 - 确保标题靠近复选框，按钮靠近右侧
        self.header_layout.addWidget(self.checkbox)
        self.header_layout.addWidget(self.title_label, 0, Qt.AlignLeft)  # 左对齐
        self.header_layout.addWidget(self.drag_handle)  # 这将占据所有剩余空间
        self.header_layout.addWidget(self.toggle_button, 0, Qt.AlignRight)  # 右对齐

        # ========== 内容区 ==========
        self.content_widget = QWidget()
        self.content_widget.setObjectName("collapsibleContent")
        # 添加透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self.content_widget)
        self.opacity_effect.setOpacity(0.0)
        self.content_widget.setGraphicsEffect(self.opacity_effect)

        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(25, 5, 10, 5)
        self.content_layout.setSpacing(5)

        # 初始时内容区"收起"
        self.content_widget.setMaximumHeight(0)

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
                transition: background-color 0.3s;
            }
            #collapsibleHeader:hover {
                background-color: #e9e9e9;
            }
            #collapsibleContent {
                background-color: #fcfcfc;
                border-left: 1px solid #ddd;
                margin-left: 15px;
                margin-right: 15px;  /* Add right margin to make content narrower */
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            #toggleButton {
                border: none;
                background: transparent;
                transition: transform 0.3s ease;
            }
        """)
    def _setup_animations(self):
        # 准备所有动画，但不启动
        self.height_animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.height_animation.setEasingCurve(QEasingCurve.OutCubic)  # 更平滑的曲线
        self.height_animation.setDuration(300)  # 稍微延长动画时间

        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.setDuration(250)

        self.rotate_animation = QPropertyAnimation(self, b"rotation_angle")
        self.rotate_animation.setEasingCurve(QEasingCurve.OutBack)  # 带有轻微反弹效果
        self.rotate_animation.setDuration(300)

        # 创建一个并行动画组
        self.animation_group = QParallelAnimationGroup()
        self.animation_group.addAnimation(self.height_animation)
        self.animation_group.addAnimation(self.opacity_animation)
        self.animation_group.addAnimation(self.rotate_animation)

    # 属性访问器，用于旋转箭头
    def _get_rotation_angle(self):
        return self._rotation_angle

    def _set_rotation_angle(self, angle):
        self._rotation_angle = angle
        # 根据角度旋转按钮上的文本
        self.toggle_button.setStyleSheet(f"""
            #toggleButton {{
                border: none;
                background: transparent;
                transform: rotate({angle}deg);
            }}
        """)

    rotation_angle = Property(float, _get_rotation_angle, _set_rotation_angle)

    def toggle_content(self):
        # 计算内容区展开时应有的高度
        content_height = self.content_layout.sizeHint().height() + 10

        if self.is_expanded:
            # 折叠动画
            self.height_animation.setStartValue(self.content_widget.height())
            self.height_animation.setEndValue(0)
            self.opacity_animation.setStartValue(1.0)
            self.opacity_animation.setEndValue(0.0)
            self.rotate_animation.setStartValue(180)
            self.rotate_animation.setEndValue(0)
        else:
            # 展开动画
            self.content_widget.setVisible(True)
            self.height_animation.setStartValue(0)
            self.height_animation.setEndValue(content_height)
            self.opacity_animation.setStartValue(0.0)
            self.opacity_animation.setEndValue(1.0)
            self.rotate_animation.setStartValue(0)
            self.rotate_animation.setEndValue(180)

        # 启动动画组
        self.animation_group.start()
        self.is_expanded = not self.is_expanded

    # --- 拖动实现代码 ---
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
        mimeData.setText(str(id(self)))
        drag.setMimeData(mimeData)

        # 制作一个带阴影效果的widget快照
        pixmap = QPixmap(self.size())
        self.render(pixmap)

        # 设置拖动图像和热点
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, 10))  # 调整拖动时的手柄位置

        # 执行拖动，使用 QPixmap 代替不支持的 setOpacity
        drag.exec(Qt.MoveAction)


class DraggableContainer(QWidget):
    drag=Signal(list)

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
        # 获取并发送当前子组件的顺序列表
        current_order = self.get_widget_order()
        self.drag.emit([widget.title_text for widget in current_order])

    # 获取当前容器中的子组件顺序
    def get_widget_order(self):
        """
        返回当前容器中子组件的顺序列表。
        列表中的每个元素是一个 CollapsibleWidget 对象。
        """
        widget_list = []
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget(): # 确保 item 和 widget 存在
                widget = item.widget()
                widget_list.append(widget)
        return widget_list