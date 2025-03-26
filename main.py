import os
import sys

import psutil
from PySide6.QtWidgets import QApplication

from app.models.logging.log_manager import log_manager


# Custom stream handler to redirect stdout/stderr to the log manager
class LogRedirector:
    def __init__(self, log_func):
        self.log_func = log_func
        self.buffer = ""

    def write(self, text):
        # Buffer the text until we get a newline
        self.buffer += text
        if '\n' in self.buffer:
            # Split by newlines and log each line
            lines = self.buffer.split('\n')
            # Keep the last part if it doesn't end with newline
            self.buffer = lines[-1] if lines[-1] else ""
            # Log complete lines
            for line in lines[:-1]:
                if line.strip():  # Only log non-empty lines
                    self.log_func(line)

    def flush(self):
        # Log any remaining text in the buffer
        if self.buffer:
            self.log_func(self.buffer)
            self.buffer = ""


# Set up redirections to log file
def setup_sys_redirection():
    # Get the app logger
    app_logger = log_manager.get_app_logger()

    # Redirect stdout and stderr to our log manager
    sys.stdout = LogRedirector(app_logger.info)
    sys.stderr = LogRedirector(app_logger.error)

    # Log startup information
    app_logger.info("=== Application started ===")
    app_logger.info(f"Working directory: {os.getcwd()}")
    app_logger.info(f"Python version: {sys.version}")
    app_logger.info(f"System platform: {sys.platform}")


# 定义退出时杀死 adb.exe 进程的函数
def kill_adb_processes():
    app_logger = log_manager.get_app_logger()
    for proc in psutil.process_iter(['name']):
        proc_name = proc.info.get('name', '')
        if proc_name.lower() == "adb.exe":
            try:
                proc.kill()
                app_logger.info(f"Killed adb.exe process with pid {proc.pid}")
            except Exception as e:
                app_logger.error(f"Failed to kill adb.exe process with pid {proc.pid}: {e}")


from app.main_window import MainWindow

if __name__ == "__main__":
    print("aaa")
    setup_sys_redirection()

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(kill_adb_processes)

    window = MainWindow()
    window.show()
    print("bbb")

    sys.exit(app.exec())
