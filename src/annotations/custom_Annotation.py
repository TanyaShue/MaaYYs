# 自定义装饰器 @customRecognizer
def customRecognizer(cls):
    cls._is_custom_recognizer = True
    return cls

# 自定义装饰器 @customAction
def customAction(cls):
    cls._is_custom_action = True
    return cls