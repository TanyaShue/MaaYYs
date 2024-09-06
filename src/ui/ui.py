import tkinter as tk
from tkinter import scrolledtext
from utils.config import load_default_config  # 导入配置模块
from utils.common import load_tasks_from_pipeline
import asyncio
from tasks import TaskManager, MaaInstanceSingleton
from utils.logger import Logger  # 导入全局 Logger 单例
import threading

UI_X, UI_Y = 1000, 400

class AppUI:
    def __init__(self, root):
        self.root = root
        self.logger = Logger()  # 获取全局 Logger 实例
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
        frame.grid_rowconfigure(0, weight=1)  # 让行可以扩展
        frame.grid_columnconfigure(0, weight=1, uniform="column")  # 左侧部分
        frame.grid_columnconfigure(1, weight=1, uniform="column")  # 中间部分
        frame.grid_columnconfigure(2, weight=1, uniform="column")  # 右侧部分

        # 左侧部分
        left_part = tk.Frame(frame, bg="white")
        left_part.grid(row=0, column=0, sticky="nsew")

        adb_path_label = tk.Label(left_part, text="adb路径")
        adb_path_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")
        adb_path_entry = tk.Entry(left_part, width=30)
        adb_path_entry.grid(row=1, column=0, padx=20, pady=5)

        adb_port_label = tk.Label(left_part, text="adb端口")
        adb_port_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        adb_port_entry = tk.Entry(left_part, width=30)
        adb_port_entry.grid(row=3, column=0, padx=20, pady=5)

        config = load_default_config()
        adb_path_entry.insert(0, config.get("adb_path", ""))
        adb_port_entry.insert(0, config.get("adb_port", ""))

        connect_button = tk.Button(left_part, text="连接", command=lambda: self.run_async_task(self.connect(adb_path_entry, adb_port_entry, connect_button)))
        connect_button.grid(row=4, column=0, padx=20, pady=10)

        # 中间部分：任务选择框 (Canvas)
        middle_part = tk.Frame(frame, bg="lightgray")
        middle_part.grid(row=0, column=1, sticky="nsew")

        # 确保行、列的权重是动态的
        middle_part.grid_rowconfigure(0, weight=1)
        middle_part.grid_columnconfigure(0, weight=1)

        canvas_frame = tk.Frame(middle_part, bg="lightgray")
        canvas_frame.grid(row=0, column=0, sticky="nsew")

        canvas = tk.Canvas(canvas_frame, bg="white")
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        checkboxes_frame = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=checkboxes_frame, anchor="nw")

        tasks = load_tasks_from_pipeline("assets/resource/base/pipeline")
        task_names = list(tasks.keys())
        self.checkbox_vars = {}

        for option in task_names:
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(checkboxes_frame, text=option, variable=var, bg="white")
            checkbox.pack(anchor="w", padx=10)
            self.checkbox_vars[option] = var

        checkboxes_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        # 下部分：执行按钮
        button_frame = tk.Frame(middle_part, bg="lightgray")
        button_frame.grid(row=1, column=0, sticky="ew", pady=10)

        execute_button = tk.Button(button_frame, text="执行",command=lambda: self.run_async_task(self.execute_selected_options))
        execute_button.pack(side="bottom", pady=10)

        # 右侧部分：日志输出窗口
        log_output = scrolledtext.ScrolledText(frame, height=200, bg="lightblue", state='disabled')
        log_output.grid(row=0, column=2, sticky="nsew")

        self.logger.set_log_output(log_output)

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

        # 启动异步事件循环
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, lambda: asyncio.run(TaskManager.main(adb_path, adb_port, connect_button)))


    def run_async_task(self, task):
        # 使用线程启动事件循环
        threading.Thread(target=self._asyncio_loop, args=(task,)).start()

    def _asyncio_loop(self, task):
        # 在新线程中运行事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(task())


    async def execute_selected_options(self):
  
        print("开始执行按钮点击动作")
        task=TaskManager()
        task.test()
        maa_inst=await MaaInstanceSingleton.get_instance()
        print(f"当前实例：{maa_inst}")
        await maa_inst.run_task("打开阴阳师_key")
        print("按钮测试执行完成")
        
        