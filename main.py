import os
import json
import subprocess
import atexit
from PySide6.QtWidgets import QApplication
from src.ui.ui import MainWindow
from src.utils.logger import setup_logging

# 保存子进程的全局变量
exe_process = None

# 读取配置文件中的DEBUG状态
def load_config():
    """加载 app_config.json 配置文件"""
    config_path = os.path.join(os.getcwd(), "assets", "config", "app_config.json")
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config.get("DEBUG", True)  # 如果配置文件中没有DEBUG字段，则默认True

DEBUG = load_config()  # 将DEBUG设置为配置文件中的值

def start_exe_or_script():
    """根据DEBUG状态启动指定的 exe 或 py 文件"""
    global exe_process
    current_dir = os.getcwd()

    if DEBUG:
        # 调整为你想要运行的 Python 脚本
        script_path = os.path.join(current_dir, "main_service.py")  # 替换为你的脚本路径
        exe_process = subprocess.Popen(['python', script_path])  # 使用 python 解释器运行脚本
        print(f"Started script: {script_path}")
    else:
        try:
            exe_path = os.path.join(current_dir, "MAA_YYS_BACKEND.exe")  # 替换为你的 exe 路径
            exe_process = subprocess.Popen(exe_path)
            print(f"Started exe: {exe_path}")
        except FileNotFoundError:
            print(f"Failed to start exe: {exe_path}")

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
    start_exe_or_script()

    # 启动主窗口
    app = QApplication([])
    window = MainWindow()
    window.show()

    try:
        app.exec()
    finally:
        # 确保在程序退出时关闭 exe
        stop_exe()
