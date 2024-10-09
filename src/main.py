import logging

from maa.library import Library
from PySide6.QtWidgets import (
    QApplication
)

from src.core.core import TaskProjectManager
from src.ui.ui import MainWindow

if __name__ == '__main__':
    try:
        # 配置日志记录
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s][%(levelname)s] - %(message)s',
            handlers=[
                logging.FileHandler("app.log"),
                logging.StreamHandler()
            ],
            encoding="UTF-8"
        )
        app = QApplication([])
        window = MainWindow()
        window.show()
        app.exec()
    finally:
        TaskProjectManager().terminate_all()
