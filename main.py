import os
import subprocess
import atexit
from PySide6.QtWidgets import QApplication
from src.ui.ui import MainWindow
from src.utils.logger import setup_logging

# 保存子进程的全局变量
exe_process = None


def start_exe():
    """启动指定的 exe 文件"""
    global exe_process
    current_dirs = os.getcwd()
    exe_path = os.path.join(current_dirs, "MAA_YYS_BACKEND.exe")  # 你需要替换这个路径
    exe_process = subprocess.Popen(exe_path)


def stop_exe():
    """关闭 exe 子进程"""
    global exe_process
    if exe_process:
        try:
            print("Attempting to terminate the process...")
            exe_process.terminate()  # 尝试优雅地终止进程
            exe_process.wait(timeout=2)  # 等待2秒关闭
            print("Process terminated successfully.")
        except subprocess.TimeoutExpired:
            print("Terminate timed out, force killing the process...")
            exe_process.kill()  # 强制杀死进程
            print("Process killed.")
        except Exception as e:
            print(f"Failed to terminate exe: {e}")
        finally:
            exe_process = None


if __name__ == "__main__":
    # 获取当前工作目录
    current_dir = os.getcwd()
    # 配置日志文件路径
    log_file_path = os.path.join(current_dir, "assets", "debug", "app.log")

    # 设置日志
    setup_logging(log_file_path)

    # 注册退出时的清理函数，确保即使发生异常也会清理
    atexit.register(stop_exe)

    # 启动 exe 文件
    start_exe()

    # 启动主窗口
    app = QApplication([])
    window = MainWindow()
    window.show()

    try:
        app.exec()
    finally:
        # 确保在程序退出时关闭 exe
        stop_exe()