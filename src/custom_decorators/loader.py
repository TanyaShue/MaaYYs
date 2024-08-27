import os
import importlib
from maa.custom_action import CustomAction
import inspect

# Global registry for custom actions
action_registry = {}

def load_custom_actions(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"custom_actions.{module_name}")
            for name, obj in module.__dict__.items():
                # 检查是否为 CustomAction 的子类并且不是抽象类
                if inspect.isclass(obj) and issubclass(obj, CustomAction) and not inspect.isabstract(obj):
                    action_registry[name] = obj()
