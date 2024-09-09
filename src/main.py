# main.py
import tkinter as tk
from utils.logger import Logger
from ui import AppUI

# 创建主窗口
root = tk.Tk()

# 创建日志模块
logger = Logger()

# 创建 AppUI 实例
app_ui = AppUI(root)

# 示例：通过日志模块输出日志
logger.add_log("程序已启动")

# 启动 Tkinter 主循环
root.mainloop()
