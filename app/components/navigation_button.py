from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPainter, QColor, QPen
from PySide6.QtWidgets import QPushButton, QToolTip, QVBoxLayout, QLabel


class NavigationButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(parent)
        self.setText("")  # We'll use our custom layout for text
        self.setFixedSize(60, 60)  # Square button that fits sidebar width
        self.setCheckable(True)
        self.setObjectName("navButton")
        self.setToolTip(text)

        # Create layout for icon and text
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)

        # Add icon
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))

        # Add small text label below icon (hidden by default)
        self.text_label = QLabel(text)
        self.text_label.setObjectName("navButtonLabel")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setVisible(False)  # Hidden by default, shown on expand
        layout.addStretch(1)
        layout.addWidget(self.text_label)

        # Set up hover animation effect properties
        self._hovered = False
        self._animation = QPropertyAnimation(self, b"iconSize")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)

        # Track indicator state
        self._show_indicator = False

    def enterEvent(self, event):
        # Handle mouse enter with animation
        if not self.isChecked():
            self._animation.setStartValue(self.iconSize())
            self._animation.setEndValue(QSize(28, 28))
            self._animation.start()
        self._hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Handle mouse leave with animation
        if not self.isChecked():
            self._animation.setStartValue(self.iconSize())
            self._animation.setEndValue(QSize(24, 24))
            self._animation.start()
        self._hovered = False
        super().leaveEvent(event)

    def setShowText(self, show):
        """Toggle display of the text label below the icon"""
        self.text_label.setVisible(show)

    def paintEvent(self, event):
        # First draw the normal button
        super().paintEvent(event)

        # Then draw active indicator if checked
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw left edge active indicator
            indicator_width = 4
            indicator_height = 24

            # Get highlight color from stylesheet or use default
            if self.property("highlightColor"):
                color = QColor(self.property("highlightColor"))
            else:
                color = QColor("#1a73e8")  # Default blue highlight

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)

            # Draw rounded rectangle on left edge
            painter.drawRoundedRect(
                0,
                (self.height() - indicator_height) // 2,
                indicator_width,
                indicator_height,
                2, 2
            )
            painter.end()