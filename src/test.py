import asyncio
from maa.resource import Resource
from maa.controller import AdbController
from maa.instance import Instance
from maa.toolkit import Toolkit, AdbDevice



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
    async def main(self):
        try:
            Toolkit.init_option("./")
            resource = Resource()
            await resource.load("./assets/resource/base")
            device = AdbDevice
            device.address = "127.0.0.1:5575"
            device.adb_path = "C:\\Program Files\\BlueStacks_nxt\\HD-Adb.exe"
            controller = AdbController(
                adb_path=device.adb_path,
                address=device.address,
            )
            await controller.connect()

            maa_inst = await MaaInstanceSingleton.get_instance()
            maa_inst.bind(resource, controller)
            if not maa_inst.inited:
                print("MAA框架初始化失败")
                return

            print("Maa框架初始化成功，准备开始执行测试任务")

            await test()
            
            print("测试任务执行完成")
            
        except Exception as e:
            print(f"程序执行过程中发生错误: {e}")

async def test():
    maa_inst = await MaaInstanceSingleton.get_instance()
    print(f"当前实例：{maa_inst}")
    await maa_inst.run_task("打开阴阳师_key")

async def test_main():
    task_manager = TaskManager()
    
    await task_manager.main()  # 先执行 main 方法
    print("Main 方法执行完成")
    
    # 执行第一个任务
    print("开始执行第一个测试任务")
    await test()
    
    # 执行第二个任务
    print("开始执行第二个测试任务")
    await test()

if __name__ == "__main__":
    asyncio.run(test_main())
