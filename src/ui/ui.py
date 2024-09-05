# ui_module.py
import tkinter as tk
from tkinter import scrolledtext
from utils.config import load_default_config  # 导入配置模块
import threading
import asyncio
from tasks import main

UI_X, UI_Y = 600, 400

class AppUI:
    def __init__(self, root, logger):
        self.root = root
        self.logger = logger
        self.tab_frames = {}
        self.init_ui()

    def init_ui(self):
        self.root.title("MaaYYs")
        self.root.geometry(f"{UI_X}x{UI_Y}")

        # 左侧按钮栏
        left_frame = tk.Frame(self.root, width=100, bg="lightgray")
        left_frame.pack(side="left", fill="y")

        # 右侧内容区域
        content_frame = tk.Frame(self.root)
        content_frame.pack(side="right", fill="both", expand=True)

        # 初始化标签页布局
        self.tab_frames["开始"] = self.create_tab1_layout(content_frame)
        self.tab_frames["设置"] = self.create_tab2_layout(content_frame)

        # 创建左侧按钮
        tabs = ["开始", "设置"]
        for tab_name in tabs:
            button = tk.Button(left_frame, text=tab_name, command=lambda name=tab_name: self.show_content(name))
            button.pack(pady=10, padx=10, fill="x")

        # 显示第一个标签
        self.show_content("开始")

    def create_tab1_layout(self, content_frame):
        frame = tk.Frame(content_frame)

        # 左侧部分
        left_part = tk.Frame(frame, width=(UI_X - 100) // 2, bg="white")
        left_part.pack(side="left", fill="y", expand=True)

        # "adb路径" 标签和文本框
        adb_path_label = tk.Label(left_part, text="adb路径")
        adb_path_label.pack(pady=10, padx=20)
        adb_path_entry = tk.Entry(left_part, width=30)
        adb_path_entry.pack(pady=5, padx=20)

        # "adb端口" 标签和文本框
        adb_port_label = tk.Label(left_part, text="adb端口")
        adb_port_label.pack(pady=10, padx=20)
        adb_port_entry = tk.Entry(left_part, width=30)
        adb_port_entry.pack(pady=5, padx=20)

        # 加载默认配置并填充文本框
        config = load_default_config()  # 从配置模块加载配置
        adb_path_entry.insert(0, config.get("adb_path", ""))
        adb_port_entry.insert(0, config.get("adb_port", ""))

        # 右侧部分：日志输出窗口
        self.log_output = scrolledtext.ScrolledText(frame, width=(UI_X - 100) // 2, height=200, bg="lightblue")
        self.log_output.pack(side="right", fill="both", expand=True)

        # 绑定日志窗口到日志模块
        self.logger.set_log_output(self.log_output)

        # 连接按钮
        connect_button = tk.Button(left_part, text="连接", command=lambda: self.connect(adb_path_entry, adb_port_entry, connect_button))
        connect_button.pack(pady=20, padx=20)
        return frame

    def create_tab2_layout(self, content_frame):
        frame = tk.Frame(content_frame)
        top_part = tk.Frame(frame, height=200, bg="lightyellow")
        top_part.pack(side="top", fill="x")
        bottom_part = tk.Frame(frame, height=200, bg="lightgreen")
        bottom_part.pack(side="bottom", fill="x")
        return frame

    def show_content(self, tab_name):
        for frame in self.tab_frames.values():
            frame.pack_forget()
        self.tab_frames[tab_name].pack(fill="both", expand=True)

    def connect(self, adb_path_entry, adb_port_entry, connect_button):
        adb_path = adb_path_entry.get()
        adb_port = adb_port_entry.get()

        self.logger.add_log(f"ADB路径: {adb_path}")
        self.logger.add_log(f"ADB端口: {adb_port}")
        self.logger.add_log("正在连接...")

        # 启动主要业务的线程
        threading.Thread(target=lambda: asyncio.run(main(adb_path, adb_port, self.logger.add_log))).start()

        # 禁用按钮
        connect_button.config(text="已连接", state=tk.DISABLED)
