from PySide6.QtWidgets import QWidget, QCheckBox, QVBoxLayout
from PySide6.QtCore import Qt

class CollapsibleBox(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)

        self.toggle_button = QCheckBox(title)
        self.toggle_button.setObjectName("collapsibleToggle")

        self.toggle_button.stateChanged.connect(self.on_toggle)

        self.content_area = QWidget()
        self.content_area.setVisible(False)

        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 0, 0, 0)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_area)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def on_toggle(self, state):
        self.content_area.setVisible(state == Qt.Checked)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)