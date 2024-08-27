# -*- coding: UTF-8 -*-
from typing import Tuple
from pathlib import WindowsPath

# python -m pip install maafw
from maa.define import RectType
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit, AdbDevice
from maa.custom_recognizer import CustomRecognizer
from maa.custom_action import CustomAction

import maa
import asyncio
import random
import traceback
import sys
import time

async def run_on_device(device, resource):
    print(f"开始处理设备: {device.address}")
    controller = AdbController(
        adb_path=device.adb_path,
        address=device.address,
    )
    await controller.connect()

    maa_inst = Instance()
    maa_inst.bind(resource, controller)
    maa_inst.register_action("Random_touch", Random_touch)
    maa_inst.register_action("Random_wait", Random_wait)

    if not maa_inst.inited:
        print(f"设备 {device.address} 上的MAA框架初始化失败")
        return

    print(f"设备 {device.address} 上的MAA框架初始化完成, 开始执行任务")
    await maa_inst.run_task("打开游戏")
    print(f"设备 {device.address} 上的任务执行完成")

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

    print("找到以下ADB设备：")
    for i, device in enumerate(device_list):
        print(f"{i + 1}: {device.name} - {device.address} ({device.adb_path})")
    
    # 提示用户是否需要手动添加设备
    manual_add = input("是否要手动添加ADB设备信息？(y/n)：").strip().lower()
    if manual_add == 'y':
        # 用户手动输入设备信息
        device_name = input("请输入设备名称：").strip()
        adb_path = input("请输入ADB路径（如C:/Android/adb.exe）：").strip()
        device_address = input("请输入设备地址（如127.0.0.1:5555）：").strip()

        # 创建 AdbDevice 对象并添加到设备列表
        new_device = AdbDevice(
            name=device_name,
            adb_path=WindowsPath(adb_path),
            address=device_address,
            controller_type=16645886,  # 保持默认值
            config='{}'  # 保持默认值
        )
        device_list.append(new_device)
        print(f"手动添加的设备：{new_device.name} - {new_device.address} ({new_device.adb_path})")

    print("现在共有以下ADB设备：")
    for i, device in enumerate(device_list):
        print(f"{i + 1}: {device.name} - {device.address} ({device.adb_path})")

    # 列出所有设备，并提示用户选择
    selected_devices = input("请选择要处理的设备（多个设备用逗号分隔，例如 1,2）：")

    # 解析用户输入的设备序号
    try:
        selected_indices = [int(i.strip()) - 1 for i in selected_devices.split(",")]
    except ValueError:
        print("输入格式不正确，请输入正确的设备编号")
        sys.exit()

    # 验证选择的设备序号是否有效
    selected_devices = [device_list[i] for i in selected_indices if 0 <= i < len(device_list)]
    if not selected_devices:
        print("未选择任何有效的设备，程序退出")
        sys.exit()

    # 并行处理所选设备
    tasks = [run_on_device(device, resource) for device in selected_devices]
    await asyncio.gather(*tasks)

    print("所有选择设备的任务执行完成")

class Random_touch(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        
        print(custom_param)

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

class Random_wait(CustomAction):
    def run(self, context, task_name, custom_param, box, rec_detail) -> bool:
        # 生成一个随机的等待时间，范围可以是 1 到 100 秒
        
        wait_time = random.uniform(1, 100)
        
        # 打印等待时间
        print(f"等待 {wait_time:.2f} 秒...")

        # 等待指定的时间
        time.sleep(wait_time)

        print("等待结束！")
        return True
    def stop(self) -> None:
        pass

# my_rec = MyRecognizer()
Random_touch = Random_touch()
Random_wait = Random_wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"程序执行过程中发生错误: {e}")
        traceback.print_exc()
        input("按回车键退出...")
