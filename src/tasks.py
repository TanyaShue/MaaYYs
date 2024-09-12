import asyncio
import traceback
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit
from custom_decorators.loader import load_custom_actions, load_custom_recognizers, action_registry, recognizer_registry
from utils.logger import Logger  # 导入全局 Logger 单例
from contextlib import asynccontextmanager
import os
from maa.library import Library

class MaaInstanceSingleton:
    _instance: Instance = None
    _lock = asyncio.Lock()
    _resource: Resource = None
    _controller: AdbController = None

    @staticmethod
    async def get_instance(resource=None, controller=None) -> Instance:
        async with MaaInstanceSingleton._lock:
            if MaaInstanceSingleton._instance is None:
                MaaInstanceSingleton._instance = Instance()
                MaaInstanceSingleton._instance.bind(resource, controller)

            return MaaInstanceSingleton._instance


class TaskManager:

    @staticmethod
    async def main(adb_path, adb_port):
        logger = Logger()  # 获取全局 Logger 实例
        async with log_task(logger, "Maa框架初始化"):
            try:
                Toolkit.init_option("assets")
                resource = Resource()
                await resource.load("assets/resource/base")

                # 初始化设备并连接
                controller = AdbController(adb_path=adb_path, address=adb_port) 
                await controller.connect()

                # 保存资源和控制器到单例中
                MaaInstanceSingleton._controller = controller
                MaaInstanceSingleton._resource = resource

                maa_inst = await MaaInstanceSingleton.get_instance(resource, controller)
                
                                # 注册自定义 action 和 recognizer
                load_custom_actions("src/custom_actions")
                for action_name, action_instance in action_registry.items():
                    maa_inst.register_action(action_name, action_instance)

                load_custom_recognizers("src/custom_recognizer")
                for recognizer_name, recognizer_instance in recognizer_registry.items():
                    maa_inst.register_recognizer(recognizer_name, recognizer_instance)
                

                if not maa_inst.inited:
                    logger.add_log_thread_safe("MAA框架初始化失败")
                    return



            except Exception as e:
                print("程序执行过程中发生错误: ", e)
                print(f"程序执行过程中发生错误: {traceback.format_exc()}")
                logger.add_log_thread_safe(e)
                logger.add_log_thread_safe(f"程序执行过程中发生错误: {traceback.format_exc()}")


@asynccontextmanager
async def log_task(logger, task_name):
    """
    用于异步日志记录的上下文管理器，捕获任务的开始和结束信息，以及错误日志。
    """
    logger.add_log_thread_safe(f"{task_name} 开始")
    try:
        yield
    except Exception as e:
        logger.add_log_thread_safe(f"{task_name} 失败: {e}")
    else:
        logger.add_log_thread_safe(f"{task_name} 完成")

