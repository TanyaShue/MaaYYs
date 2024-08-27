# -*- coding: UTF-8 -*-
import asyncio
import traceback
import sys
from custom_decorators.loader import load_custom_actions, action_registry
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

    print("MAA框架初始化完成,开始执行任务")
    await maa_inst.run_task("点击探查")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")
