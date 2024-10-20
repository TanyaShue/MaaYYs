import logging

from PySide6.QtWidgets import (
    QApplication
)
from src.ui.ui import MainWindow

if __name__ == "__main__":

    # 配置日志记录
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s][%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler("../assets/debug/app.log"),
            logging.StreamHandler()
        ],
        encoding="UTF-8"
    )
    # 注册退出时的清理函数，确保即使发生异常也会清理

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


