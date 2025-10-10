from maa.context import Context

# 1. 定义一个全局变量来存储设备名称，并给一个默认值
device_name: str = "default_device"

def set_device_name(name: str):
    """
    设置全局的设备名称。
    MaaAgent.py 启动时会调用此函数。
    """
    global device_name
    device_name = name
    print(f"[Global] Device name set to: {device_name}")


def print_to_ui(context:Context,message,leve:str="info"):
    context.run_task("自定义输出", {"自定义输出": {"focus": {"start": f"{message}"}}})




