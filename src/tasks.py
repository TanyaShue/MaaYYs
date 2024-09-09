from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit, AdbDevice
from custom_decorators.loader import load_custom_actions, load_custom_recognizers, action_registry, recognizer_registry
from utils.logger import Logger  # 导入全局 Logger 单例
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
    async def main(adb_path, adb_port):

        logger = Logger()  # 获取全局 Logger 实例
        try:
            logger.add_log_thread_safe("Maa框架开始初始化")
            Toolkit.init_option("../")
            resource = Resource()
            await resource.load("../assets/resource/base")
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
                logger.add_log_thread_safe("MAA框架初始化失败")
                return

            load_custom_actions("custom_actions")
            for action_name, action_instance in action_registry.items():
                maa_inst.register_action(action_name, action_instance)

            load_custom_recognizers("custom_recognizer")
            for recognizer_name, recognizer_instance in recognizer_registry.items():
                maa_inst.register_recognizer(recognizer_name, recognizer_instance)
            logger.add_log_thread_safe("Maa框架初始化完成")

            logger.add_log_thread_safe("开始执行测试任务")
            await maa_inst.run_task("打开阴阳师")
            logger.add_log_thread_safe(" 任务执行完毕")

        except Exception as e:
            logger.add_log(f"程序执行过程中发生错误: {e}")
    
    