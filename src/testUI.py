import tkinter as tk
from tkinter import scrolledtext
import threading
import asyncio
import traceback
import json
from until.common import load_tasks_from_pipeline
from custom_decorators.loader import load_custom_actions, load_custom_recognizers, action_registry, recognizer_registry
from maa.define import RectType
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit, AdbDevice

# 创建主窗口
UI_X, UI_Y = 600, 400

root = tk.Tk()
root.title("MaaYYs")
root.geometry(f"{UI_X}x{UI_Y}")

# 左侧按钮栏
left_frame = tk.Frame(root, width=100, bg="lightgray")
left_frame.pack(side="left", fill="y")

# 右侧内容区域
content_frame = tk.Frame(root)
content_frame.pack(side="right", fill="both", expand=True)

# 标签页内容容器
tab_frames = {}

# 日志输出框引用
log_output = None

# 向日志框添加日志的功能
def add_log(message):
    if log_output:
        log_output.insert(tk.END, f"{message}\n")
        log_output.see(tk.END)  # 自动滚动到最新的日志

# 读取默认配置
def load_default_config():
    try:
        with open("assets/config/app_config.json", "r") as file:
            config = json.load(file)
            return config
    except Exception as e:
        add_log(f"读取配置文件失败: {e}")
        return {"adb_path": "", "adb_port": ""}

# 标签页 1 布局：左右两部分，左侧添加文本框和按钮
def create_tab1_layout():
    global log_output
    
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
    config = load_default_config()
    adb_path_entry.insert(0, config.get("adb_path", ""))
    adb_port_entry.insert(0, config.get("adb_port", ""))
    
    # 右侧部分：日志输出窗口
    global log_output
    log_output = scrolledtext.ScrolledText(frame, width=(UI_X - 100) // 2, height=200, bg="lightblue")
    log_output.pack(side="right", fill="both", expand=True)
    
    # "连接" 按钮
    def connect():
        adb_path = adb_path_entry.get()
        adb_port = adb_port_entry.get()
        add_log(f"ADB路径: {adb_path}")
        add_log(f"ADB端口: {adb_port}")
        add_log("正在连接...")
        
        # 启动主要功能的线程
        threading.Thread(target=lambda: asyncio.run(main(adb_path, adb_port))).start()
        
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

# 初始化显示第一个标签的内容
show_content("开始")

async def main(adb_path, adb_port):
    try:
        add_log("Maa框架开始初始化")
        Toolkit.init_option("./")

        resource = Resource()
        await resource.load("./assets/resource/base")

        device = AdbDevice
        device.address = adb_port
        device.adb_path = adb_path
        controller = AdbController(
            adb_path=device.adb_path,
            address=device.address,
        )
        await controller.connect()

        maa_inst = Instance()
        maa_inst.bind(resource, controller)

        if not maa_inst.inited:
            add_log("MAA框架初始化失败")
            return

        # Load and register custom actions
        load_custom_actions("src/custom_actions")
        for action_name, action_instance in action_registry.items():
            maa_inst.register_action(action_name, action_instance)

        # Load and register custom recognizers
        load_custom_recognizers("src/custom_recognizer")
        for recognizer_name, recognizer_instance in recognizer_registry.items():
            maa_inst.register_recognizer(recognizer_name, recognizer_instance)

        add_log("加载任务列表")
        tasks = load_tasks_from_pipeline("assets/resource/base/pipeline")
        add_log("任务加载完成")

    except Exception as e:
        add_log(f"程序执行过程中发生错误: {e}")
        traceback.print_exc()

# 启动 Tkinter 主循环
root.mainloop()
