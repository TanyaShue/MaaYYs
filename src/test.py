import inspect
import pkgutil
import importlib

def get_custom_recognizer_classes(package):
    return [
        name for _, module_name, _ in pkgutil.walk_packages(package.__path__)
        for name, obj in inspect.getmembers(importlib.import_module(f"{package.__name__}.{module_name}"), inspect.isclass)
        if obj.__module__.startswith(package.__name__) and getattr(obj, '_is_custom_action', False)
    ]

# 示例用法
import customAction
for cls_name in get_custom_recognizer_classes(customAction):
    print(f"Class Name: {cls_name}")
