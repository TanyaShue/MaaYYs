import logging

from PySide6.QtWidgets import (
    QApplication
)

from src.core.core import TaskProjectManagerClient
from src.ui.ui import MainWindow

if __name__ == "__main__":

    try:
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
    finally:
        TaskProjectManagerClient().terminate_all()  # 尝试优雅终止所有进程

