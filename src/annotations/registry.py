import customRecognizer
import customAction
import inspect
import pkgutil
import importlib

def get_custom_classes(package, attribute_name):
    """
    获取包中的所有类对象，这些类具有指定的自定义属性。
    
    :param package: 包对象
    :param attribute_name: 自定义属性的名称
    :return: 类对象列表
    """
    return [
        cls for _, module_name, _ in pkgutil.walk_packages(package.__path__)
        for name, cls in inspect.getmembers(importlib.import_module(f"{package.__name__}.{module_name}"), inspect.isclass)
        if cls.__module__.startswith(package.__name__) and getattr(cls, attribute_name, False)
    ]

def register_custom_classes(maa_inst, package, attribute_name, register_method):
    """
    注册自定义类到给定的注册方法中。
    
    :param maa_inst: 实例对象
    :param package: 包对象
    :param attribute_name: 自定义属性的名称
    :param register_method: 注册方法
    """
    for cls in get_custom_classes(package, attribute_name):
        print(f"开始注册自定义类：{cls.__name__}")
        instance = cls()  # 创建类实例
        name = cls.__name__  # 使用类名作为名称
        success = register_method(name, instance)  # 注册类及其名称
        if success:
            print(f"成功注册自定义类：{cls.__name__}")
        else:
            print(f"注册自定义类失败：{cls.__name__}")

def register_custom_recognizers(maa_inst):
    register_custom_classes(maa_inst, customRecognizer, '_is_custom_recognizer', maa_inst.register_recognizer)

def register_custom_action(maa_inst):
    register_custom_classes(maa_inst, customAction, '_is_custom_action', maa_inst.register_action)
