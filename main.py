import os
from PySide6.QtWidgets import QApplication
from src.ui.ui import MainWindow
from src.utils.logger import setup_logging

if __name__ == "__main__":
    # 获取当前工作目录
    current_dir = os.getcwd()
    # 配置日志文件路径
    log_file_path = os.path.join(current_dir, "assets", "debug", "app.log")

    # 设置日志
    setup_logging(log_file_path)

    # 注册退出时的清理函数，确保即使发生异常也会清理
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
