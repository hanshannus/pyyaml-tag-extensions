from .loaders import ExtendedLoader
from pathlib import Path
import yaml


def load(filepath, root="global"):
    return Yaml.load(filepath, root=root)


def loads(stream, root="global"):
    return Yaml.load(stream, root=root)


class Yaml(ExtendedLoader):
    root_dir: Path = None

    def __init__(self, stream):
        super().__init__(stream)

    @classmethod
    def load(cls, filepath, root="global"):
        with Path(filepath).open() as stream:
            return cls.loads(stream, root=root)

    @classmethod
    def loads(cls, stream, root="global"):
        if isinstance(root, str) and root == "global":
            cls.root_dir = Path(stream.name).resolve().parent
        elif isinstance(root, (Path, str)):
            cls.root_dir = Path(root)
        new_loader = ExtendedLoader
        new_loader.root_dir = cls.root_dir
        return yaml.load(stream, Loader=new_loader)
