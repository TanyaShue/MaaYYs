import tkinter as tk
from tkinter import scrolledtext
from config import load_default_config
from until.logger import add_log, set_log_output
import asyncio
import threading
from tasks import main as run_main

# 定义 UI 组件创建函数
def create_ui(root):
    # 左侧按钮栏
    left_frame = tk.Frame(root, width=100, bg="lightgray")
    left_frame.pack(side="left", fill="y")

    # 右侧内容区域
    content_frame = tk.Frame(root)
    content_frame.pack(side="right", fill="both", expand=True)

    # 标签页内容容器
    global tab_frames
    tab_frames = {}

    # 日志输出框引用
    global log_output
    log_output = None

    # 标签页 1 布局：左右两部分，左侧添加文本框和按钮
    def create_tab1_layout():
        nonlocal log_output
        
        frame = tk.Frame(content_frame)
        
        # 左侧部分
        left_part = tk.Frame(frame, width=250, bg="white")
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
        config = load_default_config()
        adb_path_entry.insert(0, config.get("adb_path", ""))
        adb_port_entry.insert(0, config.get("adb_port", ""))
        
        # 右侧部分：日志输出窗口
        nonlocal log_output
        log_output = scrolledtext.ScrolledText(frame, width=250, height=20, bg="lightblue")
        log_output.pack(side="right", fill="both", expand=True)
        
        # 设置日志输出框
        set_log_output(log_output)
        
        # "连接" 按钮
        def connect():
            adb_path = adb_path_entry.get()
            adb_port = adb_port_entry.get()
            add_log(f"ADB路径: {adb_path}")
            add_log(f"ADB端口: {adb_port}")
            add_log("正在连接...")
            
            # 启动主要功能的线程
            threading.Thread(target=lambda: asyncio.run(run_main(adb_path, adb_port))).start()
            
            # 更新按钮状态
            connect_button.config(text="已连接", state=tk.DISABLED)
        
        connect_button = tk.Button(left_part, text="连接", command=connect)
        connect_button.pack(pady=20, padx=20)
        
        return frame

    # 标签页 2 布局：上下两部分
    def create_tab2_layout():
        frame = tk.Frame(content_frame)
        
        # 上半部分
        top_part = tk.Frame(frame, height=200, bg="lightyellow")
        top_part.pack(side="top", fill="x")
        
        # 下半部分
        bottom_part = tk.Frame(frame, height=200, bg="lightgreen")
        bottom_part.pack(side="bottom", fill="x")
        
        return frame

    # 初始化每个标签页的布局
    tab_frames["开始"] = create_tab1_layout()
    tab_frames["设置"] = create_tab2_layout()

    # 显示当前内容的函数
    def show_content(tab_name):
        # 隐藏所有标签页
        for frame in tab_frames.values():
            frame.pack_forget()
        # 显示当前标签页
        tab_frames[tab_name].pack(fill="both", expand=True)

    # 创建左侧的按钮并绑定到内容显示
    tabs = ["开始", "设置"]
    for tab_name in tabs:
        button = tk.Button(left_frame, text=tab_name, command=lambda name=tab_name: show_content(name))
        button.pack(pady=10, padx=10, fill="x")

    return content_frame

# 确保在其他模块中可以访问 show_content
