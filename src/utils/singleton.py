from functools import wraps
from typing import Type


def singleton(cls: Type) -> Type:
    """Decorator to make a class a singleton."""
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance