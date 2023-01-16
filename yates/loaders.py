import yaml
import yaml.constructor
import importlib
import re
from yaml import Node, Loader
from pathlib import Path
from typing import IO, Any


def _load_module(import_str: str):
    package, name = import_str.rsplit(".", maxsplit=1)
    module = importlib.import_module(package)
    return getattr(module, name)


def _load_file(filename, root=None):
    with open(filename, 'r') as stream:
        new_loader = ExtendedLoader
        new_loader.root_dir = root
        return yaml.load(stream, Loader=new_loader)


class ExtendedLoader(yaml.SafeLoader):
    root_dir: Path = None

    def __init__(self, stream: IO):
        if self.root_dir is None:
            self.root_dir = Path(stream.name).resolve().parent
        # extend node by content of another YAML file
        self.add_constructor(None, self._dynamic)
        super(ExtendedLoader, self).__init__(stream)

    # def _extend(self, loader: "ExtendedLoader", node: Node):
    #     filename = node.tag.split(":", 1)[1]
    #     if not filename.startswith("/"):
    #         filename = self.root_dir / filename
    #     with open(filename, 'r') as stream:
    #         defaults = yaml.load(stream, loader)
    #
    #     if isinstance(node, yaml.MappingNode):
    #         return {**defaults, **loader.construct_mapping(node)}
    #     elif isinstance(node, yaml.SequenceNode):
    #         return [*defaults, *loader.construct_sequence(node)]
    #     elif isinstance(node, yaml.SequenceNode):
    #         return [*defaults, *loader.construct_sequence(node)]
    #
    #     raise

    @staticmethod
    def _from(loader: "ExtendedLoader", node: Node):
        # define file path
        filename = node.tag.split(":", 1)[1]
        if not filename.startswith("/"):
            filename = str(loader.root_dir / filename)
        #
        ref = []
        if ".yml" in filename or ".yaml" in filename:
            suffix = ".yml" if ".yml" in filename else ".yaml"
            ref = filename.rsplit(suffix, 1)[1]
            filename = filename.rstrip(ref.lstrip("/")).rstrip("/")
            ref = ref.lstrip("/").split("/")
        else:
            # search for file in root directory
            for path in loader.root_dir.rglob("*.*"):
                pathstem = str(path.with_suffix(""))
                if not (path.suffix in [".yml", ".yaml"] and
                        filename.startswith(pathstem)):
                    continue
                ref = filename.lstrip(pathstem).lstrip("/").split("/")
                filename = str(path)
        # load file
        cfg = _load_file(filename, root=loader.root_dir)
        # remove empty keys from list
        ref = [i for i in ref if i != ""]
        # extract value from config
        for i in ref:
            if i not in cfg:
                raise KeyError(f"Key '{i}' not found")
            cfg = cfg[i]

        if isinstance(node, yaml.MappingNode):
            return {**cfg, **loader.construct_mapping(node)}
        elif isinstance(node, yaml.SequenceNode):
            return [*cfg, *loader.construct_sequence(node)]

        return cfg

    @staticmethod
    def _import(loader: Loader, node: Node):
        if node.value != "":
            raise yaml.constructor.ConstructorError(
                f"Cannot use node tag '!import:...' with an actual node value."
            )
        return _load_module(node.tag.split(":", 1)[1])

    @staticmethod
    def _init(loader: Loader, node: Node):
        import_str = node.tag.split(":", 1)[1]
        module = _load_module(import_str)

        if node.value == "":
            return module()

        if not isinstance(node, yaml.SequenceNode):
            raise yaml.constructor.ConstructorError(
                f"Only list and null nodes allowed after '!init:' tag."
            )

        args = []
        kwargs = {}
        print("init node", node)
        for subnode in node.value:
            if isinstance(subnode, yaml.ScalarNode):
                constructor = loader.construct_scalar
            elif isinstance(subnode, yaml.SequenceNode):
                constructor = loader.construct_sequence
            elif isinstance(subnode, yaml.MappingNode):
                constructor = loader.construct_mapping
            else:
                continue
            value = constructor(subnode)
            if isinstance(value, dict):
                for k, v in value.items():
                    kwargs[k] = v
            else:
                args.append(value)

        print(args)
        print(kwargs)
        return module(*args, **kwargs)

    def _dynamic(self, loader: Loader, node: Node):
        if node.tag.startswith("!extend:"):
            return self._extend(loader, node)
        if node.tag.startswith("!init:"):
            return self._init(loader, node)
        if node.tag.startswith("!from:"):
            return self._from(loader, node)
        if node.tag.startswith("!import:"):
            return self._import(loader, node)
        raise yaml.constructor.ConstructorError(
            f"could not determine a constructor for the tag '{node.tag}'"
        )
