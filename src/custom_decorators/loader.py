import os
import importlib
from maa.custom_action import CustomAction
from maa.custom_recognizer import CustomRecognizer
import inspect

# Global registries for custom actions and recognizers
action_registry = {}
recognizer_registry = {}

def load_custom_actions(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"custom_actions.{module_name}")
            for name, obj in module.__dict__.items():
                # 检查是否为 CustomAction 的子类并且不是抽象类
                if inspect.isclass(obj) and issubclass(obj, CustomAction) and not inspect.isabstract(obj):
                    action_registry[name] = obj()


def load_custom_recognizers(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"custom_recognizer.{module_name}")
            for name, obj in module.__dict__.items():
                # 检查是否为 CustomRecognizer 的子类并且不是抽象类
                if inspect.isclass(obj) and issubclass(obj, CustomRecognizer) and not inspect.isabstract(obj):
                    recognizer_registry[name] = obj()
