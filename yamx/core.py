from pathlib import Path
import yaml
import io
from omegaconf import DictConfig, ListConfig
from typing import IO, Union

# library imports
from .loaders import ExtendedLoader

DEFAULT_OUTPUT: str = "primitive"  # {"omegaconf", "primitive"}
DEFAULT_ROOT: str = "global"  # {"global", "relative"}


def load(
    filepath: str,
    root: str = DEFAULT_ROOT,
    output: str = DEFAULT_OUTPUT,
) -> Union[DictConfig, ListConfig, dict, list]:
    return Yaml.load(filepath, root=root, output=output)


def loads(
    stream: Union[str, IO],
    root: str = DEFAULT_ROOT,
    output: str = DEFAULT_OUTPUT,
) -> Union[DictConfig, ListConfig, dict, list]:
    return Yaml.loads(stream, root=root, output=output)


class Yaml(ExtendedLoader):
    root_dir: Path = None

    def __init__(self, stream: IO):
        super().__init__(stream)

    @classmethod
    def load(
        cls,
        filepath: Union[str, Path],
        root: Union[str, Path] = DEFAULT_ROOT,
        output: str = DEFAULT_OUTPUT,
    ) -> Union[DictConfig, ListConfig, dict, list]:
        with Path(filepath).open() as stream:
            return cls.loads(stream, root=root, output=output)

    @classmethod
    def loads(
        cls,
        stream: Union[str, IO],
        root: Union[str, Path] = DEFAULT_ROOT,
        output: str = DEFAULT_OUTPUT,
    ) -> Union[DictConfig, ListConfig, dict, list]:
        if isinstance(root, str) and root == "global":
            if isinstance(stream, IO):
                cls.root_dir = Path(stream.name).resolve().parent
            else:
                cls.root_dir = Path.cwd()
        elif isinstance(root, (Path, str)):
            cls.root_dir = Path(root)

        if isinstance(stream, str):
            stream = io.StringIO(stream)
        new_loader = ExtendedLoader
        new_loader.root_dir = cls.root_dir
        res = yaml.load(stream, Loader=new_loader)
        if not isinstance(res, (dict, list)):
            raise ValueError(f"Unsupported type: {type(res)}")
        if output == "omegaconf":
            if isinstance(res, dict):
                return DictConfig(res)
            elif isinstance(res, list):
                return ListConfig(res)
        else:
            return res
