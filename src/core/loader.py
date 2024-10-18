import os
import importlib
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
import inspect

# Global registries for custom actions and recognizers
action_registry = {}
recognizer_registry = {}

custom_actions_path="custom_actions"
custom_recognition_path="custom_recognition"
def load_custom_actions(directory):
    load_custom(directory, custom_actions_path,CustomAction)

def load_custom_recognizers(directory):
    load_custom(directory,custom_recognition_path,CustomRecognition)

def load_custom(directory,path,cls):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"{path}.{module_name}")
            for name, obj in module.__dict__.items():
                # 检查是否为 cls 的子类并且不是抽象类
                if inspect.isclass(obj) and issubclass(obj, cls) and not inspect.isabstract(obj):
                    action_registry[name] = obj()