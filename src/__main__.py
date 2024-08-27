# -*- coding: UTF-8 -*-
from typing import Tuple, List


# python -m pip install maafw
from maa.define import RectType
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit
from annotations import registry
# from maa.custom_recognizer import CustomRecognizer



import asyncio
import traceback
import sys

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

    # for demo, we just use the first device
    device = device_list[0]
    controller = AdbController(
        adb_path=device.adb_path,
        address=device.address,
    )
    await controller.connect()

    maa_inst = Instance()
    maa_inst.bind(resource, controller)
    print("开始注册自定义识别器和动作")
    registry.register_custom_recognizers(maa_inst)
    registry.register_custom_action(maa_inst)
    print("注册自定义识别器和动作完成")

    if not maa_inst.inited:
        print("MAA框架初始化失败")
        input("按任意键退出")
        sys.exit()

    # print("初始化题库")
    # file_path = '题库4.3.xlsx'
    # Find_answer.qa_dict_v2 = load_qa_from_excel_v2(file_path)
    # # maa_inst.register_recognizer("MyRec", my_rec)
    print("MAA框架初始化完成,开始执行任务")
    # await maa_inst.run_recognition("OCR",{"expected":"WeChat"})
    await maa_inst.run_task("打开加速器")

if __name__ == "__main__":

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")