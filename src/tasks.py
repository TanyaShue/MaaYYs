from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit, AdbDevice
from custom_decorators.loader import load_custom_actions, load_custom_recognizers, action_registry, recognizer_registry
from utils.common import load_tasks_from_pipeline

async def main(adb_path, adb_port, add_log_callback):
    try:
        add_log_callback("Maa框架开始初始化")
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
            add_log_callback("MAA框架初始化失败")
            return

        load_custom_actions("src/custom_actions")
        for action_name, action_instance in action_registry.items():
            maa_inst.register_action(action_name, action_instance)

        load_custom_recognizers("src/custom_recognizer")
        for recognizer_name, recognizer_instance in recognizer_registry.items():
            maa_inst.register_recognizer(recognizer_name, recognizer_instance)

        add_log_callback("加载任务列表")
        tasks = load_tasks_from_pipeline("assets/resource/base/pipeline")
        add_log_callback("任务加载完成")
    except Exception as e:
        add_log_callback(f"程序执行过程中发生错误: {e}")
