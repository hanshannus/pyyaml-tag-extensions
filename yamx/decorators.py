from functools import wraps
from pathlib import Path
from typing import Union, Callable, Dict, Any
from .core import Yaml


def load(filepath: Union[str, Path], root: Union[str, Path] = "global"):
    def wrapper(func: Callable):
        @wraps(func)
        def wrapped(cfg: Dict[str, Any] = None):
            if cfg is not None:
                return func(cfg)
            else:
                return func(Yaml.load(filepath, root=root))
        return wrapped
    return wrapper
