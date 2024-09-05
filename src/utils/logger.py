# logger.py
import tkinter as tk
import time


class Logger:
    def __init__(self):
        self.log_output = None

    def set_log_output(self, log_output):
        """ 设置日志输出框 """
        self.log_output = log_output

    def add_log(self, message):
        """ 添加日志到日志框 """
        if self.log_output:
            self.log_output.insert(tk.END, f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{message}\n")
            self.log_output.see(tk.END)  # 自动滚动到最新的日志
        else:
            print(f"日志框未初始化，日志内容：{message}")
