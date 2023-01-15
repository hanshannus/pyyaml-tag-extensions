from functools import wraps
from .core import Yaml


def load(filepath, root="global"):
    def wrapper(func):
        @wraps(func)
        def wrapped(cfg=None):
            if cfg is not None:
                return func(cfg)
            else:
                return func(Yaml.load(filepath, root=root))
        return wrapped

    return wrapper
