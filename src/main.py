from ui.ui import AppUI
from  PySide6.QtWidgets import QApplication
from utils.logger import Logger

if __name__ == "__main__":
    loger =Logger()
    app = QApplication([])
    ui = AppUI()
    ui.show()
    app.exec()

