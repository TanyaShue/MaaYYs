from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QCheckBox, QToolButton, QWidget, QGroupBox
from ui.main import Ui_MainWindo


# 启动应用程序
app = QApplication([])
window = MainWindow()
window.show()
app.exec()
