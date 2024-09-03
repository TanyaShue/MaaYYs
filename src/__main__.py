# -*- coding: UTF-8 -*-
import asyncio
import traceback
import sys
from until.common import load_tasks_from_pipeline
from custom_decorators.loader import load_custom_actions, load_custom_recognizers, action_registry, recognizer_registry
from maa.define import RectType
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit


async def main():
    print("Maa框架开始初始化")
    user_path = "./"
    Toolkit.init_option(user_path)

    resource = Resource()
    await resource.load("./assets/resource/base")

    device_list = await Toolkit.adb_devices()
    if not device_list:
        print("未找到任何ADB设备")
        input("按任意键退出")
        sys.exit()

    device = device_list[0]
    controller = AdbController(
        adb_path=device.adb_path,
        address=device.address,
    )
    await controller.connect()

    maa_inst = Instance()
    maa_inst.bind(resource, controller)

    if not maa_inst.inited:
        print("MAA框架初始化失败")
        input("按任意键退出")
        sys.exit()

    # Load and register custom actions
    load_custom_actions("src/custom_actions")
    for action_name, action_instance in action_registry.items():
        maa_inst.register_action(action_name, action_instance)

    # Load and register custom recognizers
    load_custom_recognizers("src/custom_recognizer")
    for recognizer_name, recognizer_instance in recognizer_registry.items():
        maa_inst.register_recognizer(recognizer_name, recognizer_instance)

    print("加载任务列表")
    tasks = load_tasks_from_pipeline("assets/resource/base/pipeline")
    task_names = list(tasks.keys())

    while True:
        print("可用任务列表：")
        for i, task_name in enumerate(task_names):
            print(f"{i + 1}. {task_name}")
            
        task_index = int(input("请输入要执行的任务编号：")) - 1
        selected_task_name = task_names[task_index]
        
        # await resource.load("./assets/resource/base")
        print(f"开始执行任务: {selected_task_name}")
        await maa_inst.run_task(selected_task_name)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")
