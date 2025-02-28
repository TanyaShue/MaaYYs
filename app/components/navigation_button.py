from PySide6.QtWidgets import QPushButton, QToolTip
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon


class NavigationButton(QPushButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(parent)
        self.setText("")  # Remove text from button
        self.setFixedSize(48, 48)  # Square button that fits sidebar width
        self.setCheckable(True)
        self.setObjectName("navButton")
        self.setToolTip(text)  # Set tooltip to show on hover

        # Configure tooltip style through stylesheet
        QToolTip.setFont(QToolTip.font())

        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))  # Larger icon since there's no text