from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit, AdbDevice
from custom_decorators.loader import load_custom_actions, load_custom_recognizers, action_registry, recognizer_registry
from utils.common import load_tasks_from_pipeline
from utils.logger import Logger  # 导入全局 Logger 单例
import tkinter as tk
import asyncio


class MaaInstanceSingleton:
    _instance = None
    _lock = asyncio.Lock()

    @staticmethod
    async def get_instance():
        async with MaaInstanceSingleton._lock:
            if MaaInstanceSingleton._instance is None:
                MaaInstanceSingleton._instance = Instance()
            return MaaInstanceSingleton._instance
    

class TaskManager:
   
    @staticmethod
    async def main(adb_path, adb_port, connect_button: tk.Button):
        connect_button.config(text="正在连接", state=tk.DISABLED)

        logger = Logger()  # 获取全局 Logger 实例
        try:
            logger.add_log("Maa框架开始初始化")
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

            maa_inst = await MaaInstanceSingleton.get_instance()
            maa_inst.bind(resource, controller)
            if not maa_inst.inited:
                logger.add_log("MAA框架初始化失败")
                return

            load_custom_actions("src/custom_actions")
            for action_name, action_instance in action_registry.items():
                maa_inst.register_action(action_name, action_instance)

            load_custom_recognizers("src/custom_recognizer")
            for recognizer_name, recognizer_instance in recognizer_registry.items():
                maa_inst.register_recognizer(recognizer_name, recognizer_instance)
            connect_button.config(text="已连接", state=tk.DISABLED)
            logger.add_log("Maa框架初始化完成")
            print("开始执行异步测试")
            await TaskManager.test()
            print("异步测试完成")
            print("开始正常测试")
            print(f"当前实例：{maa_inst}")
            await maa_inst.run_task("回到主页_key")
            print("正常测试完成")
          

        except Exception as e:
            connect_button.config(text="连接", state=tk.NORMAL)
            logger.add_log(f"程序执行过程中发生错误: {e}")
    
    
    async def test():
        maa_inst=await MaaInstanceSingleton.get_instance()
        print(f"当前实例：{maa_inst}")
        await maa_inst.run_task("打开阴阳师_key")
