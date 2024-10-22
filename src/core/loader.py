import importlib
import inspect
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition

# Global registries for custom actions and recognizers
action_registry = {}
recognizer_registry = {}

custom_actions_module = "src.custom_actions"
custom_recognition_module = "src.custom_recognition"

def load_custom_actions():
    load_custom(custom_actions_module, CustomAction)

def load_custom_recognizers():
    load_custom(custom_recognition_module, CustomRecognition)

def load_custom(module_path, cls):
    # 获取模块下的所有子模块
    try:
        package = importlib.import_module(module_path)
    except ModuleNotFoundError:
        print(f"Module {module_path} not found.")
        return

    # 动态加载子模块
    for submodule_name in dir(package):
        if not submodule_name.startswith("__"):
            full_module_name = f"{module_path}.{submodule_name}"
            try:
                submodule = importlib.import_module(full_module_name)
                for name, obj in submodule.__dict__.items():
                    # 检查是否为 cls 的子类并且不是抽象类
                    if inspect.isclass(obj) and issubclass(obj, cls) and not inspect.isabstract(obj):
                        action_registry[name] = obj() if cls == CustomAction else recognizer_registry.setdefault(name, obj())
            except ModuleNotFoundError as e:
                print(f"Failed to import {full_module_name}: {str(e)}")
