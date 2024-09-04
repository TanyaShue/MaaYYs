import tkinter as tk
from ui.ui import create_ui, show_content
from until.config import load_default_config
import asyncio
import threading
from tasks import main as run_main

def start_application():
    # 创建主窗口和界面
    root = tk.Tk()
    root.title("MaaYYs")
    root.geometry("600x400")

    # 创建 UI 组件
    ui_frame = create_ui(root)
    
    # 显示默认标签
    show_content("开始", ui_frame)
    
    # 启动 Tkinter 主循环
    root.mainloop()

if __name__ == "__main__":
    start_application()
