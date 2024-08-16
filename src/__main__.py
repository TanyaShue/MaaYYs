# -*- coding: UTF-8 -*-
from typing import Tuple

# python -m pip install maafw
from maa.define import RectType
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit

from maa.custom_recognizer import CustomRecognizer
from maa.custom_action import CustomAction

import maa
import asyncio
import random
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
    
    if not maa_inst.inited:
        print("MAA框架初始化失败")
        input("按任意键退出")
        sys.exit()

    # maa_inst.register_recognizer("MyRec", my_rec)
    maa_inst.register_action("Random_touch", Random_touch)
    print("MAA框架初始化完成,开始执行任务")
    # await maa_inst.run_recognition("OCR",{"expected":"WeChat"})
    await maa_inst.run_task("回到主页")

class Random_touch(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        # 读取 box 的参数
        x, y, w, h = box.x, box.y, box.w, box.h
        
        print(f"box参数: {box}")
        
        # 计算中心点的坐标
        center_x = x + w / 2
        center_y = y + h / 2
        
        # 使用正态分布随机生成点
        random_x = random.gauss(center_x, w / 6)  # 6 chosen to keep most points within the box
        random_y = random.gauss(center_y, h / 6)  # Adjusting sigma for distribution width
        
        # 限制生成的点在box范围内
        random_x = min(max(random_x, x), x + w)
        random_y = min(max(random_y, y), y + h)

        # 点击随机生成的点
        context.click(round(random_x), round(random_y))
        print(f"随机生成的点: {random_x, random_y}")
                
        return True
    def stop(self) -> None:
        pass


# my_rec = MyRecognizer()
Random_touch = Random_touch()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")