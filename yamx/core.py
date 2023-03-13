from pathlib import Path
import yaml
import io
from typing import IO, Union

# library imports
from .loaders import ExtendedLoader

DEFAULT_ROOT: str = "global"  # {"global", "relative"}


def load(
    filepath: str,
    root: str = DEFAULT_ROOT,
) -> Union[dict, list]:
    return Yaml.load(filepath, root=root)


def loads(
    stream: Union[str, IO],
    root: str = DEFAULT_ROOT,
) -> Union[dict, list]:
    return Yaml.loads(stream, root=root)


class Yaml(ExtendedLoader):
    root_dir: Path = None

    def __init__(self, stream: IO):
        super().__init__(stream)

    @classmethod
    def load(
        cls,
        filepath: Union[str, Path],
        root: Union[str, Path] = DEFAULT_ROOT,
    ) -> Union[dict, list]:
        with Path(filepath).open() as stream:
            return cls.loads(stream, root=root)

    @classmethod
    def loads(
        cls,
        stream: Union[str, IO],
        root: Union[str, Path] = DEFAULT_ROOT,
    ) -> Union[dict, list]:
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
        return yaml.load(stream, Loader=new_loader)
