from ui.ui import AppUI
from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    ui = AppUI()
    ui.show()
    app.exec()

