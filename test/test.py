from PySide6.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QStyle

class IconWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        icons = sorted([attr for attr in dir(QStyle) if attr.startswith("SP_")])
        for i, icon_name in enumerate(icons):
            button = QPushButton(icon_name)
            icon = self.style().standardIcon(getattr(QStyle, icon_name))
            button.setIcon(icon)
            layout.addWidget(button, i // 4, i % 4)
        self.setLayout(layout)

app = QApplication([])
window = IconWindow()
window.show()
app.exec()
