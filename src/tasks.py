from custom_decorators.loader import load_custom_actions, load_custom_recognizers, action_registry, recognizer_registry
from maa.define import RectType
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit, AdbDevice
from until.logger import add_log
from until.common import load_tasks_from_pipeline
import asyncio

async def main(adb_path, adb_port):
    try:
        add_log("Maa框架开始初始化")
        Toolkit.init_option("./")

        resource = Resource()
        await resource.load("./assets/resource/base")

        device = AdbDevice()
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
