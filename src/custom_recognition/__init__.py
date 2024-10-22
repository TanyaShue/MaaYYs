import os
import importlib
import inspect
from maa.custom_recognition import CustomRecognition   # 导入基类

# 动态导入当前目录下的所有模块
package_dir = os.path.dirname(__file__)
recognizer_registry = {}  # 注册表

def register_actions(module):
    """注册模块中的动作类到 action_registry。"""
    for name, obj in module.__dict__.items():
        if inspect.isclass(obj) and issubclass(obj, CustomRecognition) and not inspect.isabstract(obj):
            recognizer_registry[name] = obj()  # 实例化并注册到动作注册表

# 遍历当前目录下的所有模块
for filename in os.listdir(package_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = f"{__name__}.{filename[:-3]}"  # 去掉.py后缀
        submodule = importlib.import_module(module_name)  # 导入模块
        register_actions(submodule)  # 注册动作类

print("recognizer_registry:", recognizer_registry)
