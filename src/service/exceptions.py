# -*- coding: UTF-8 -*-
class TaskerError(Exception):
    """基础异常类"""
    pass

class TaskerNotFoundError(TaskerError):
    """Tasker不存在异常"""
    pass

class TaskerInitializationError(TaskerError):
    """Tasker初始化失败异常"""
    pass

class TaskerValidationError(TaskerError):
    """数据验证异常"""
    pass