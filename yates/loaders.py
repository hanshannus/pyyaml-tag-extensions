import yaml
import yaml.constructor
import importlib
import re
from pathlib import Path


def load_module(import_str: str):
    package, name = import_str.rsplit(".", maxsplit=1)
    module = importlib.import_module(package)
    return getattr(module, name)


class ExtendedLoader(yaml.SafeLoader):
    root_dir: Path = None

    def __init__(self, stream):
        if self.root_dir is None:
            self.root_dir = Path(stream.name).resolve().parent
        # extend node by content of another YAML file
        self.add_constructor(None, self.dynamic)
        super(ExtendedLoader, self).__init__(stream)

    def dynamic_extend(self, loader, node):
        filename = node.tag.split(":", 1)[1]
        if not filename.startswith("/"):
            filename = self.root_dir / filename
        with open(filename, 'r') as stream:
            defaults = yaml.load(stream, ExtendedLoader)

        if isinstance(node, yaml.MappingNode):
            return {**defaults, **loader.construct_mapping(node)}
        elif isinstance(node, yaml.SequenceNode):
            return [*defaults, *loader.construct_sequence(node)]
        elif isinstance(node, yaml.SequenceNode):
            return [*defaults, *loader.construct_sequence(node)]

        raise

    @staticmethod
    def dynamic_from(loader, node):
        filename = node.tag.split(":", 1)[1]
        ref = []
        if not filename.startswith("/"):
            filename = str(loader.root_dir / filename)
        if ".yml" in filename or ".yaml" in filename:
            if ".yml" in filename:
                ref = filename.rsplit(".yml", 1)[1]
            else:
                ref = filename.rsplit(".yaml", 1)[1]
            filename = filename.rstrip(ref.lstrip("/")).rstrip("/")
            ref = ref.lstrip("/").split("/")
        else:
            for path in loader.root_dir.rglob("*.*"):
                if path.suffix not in [".yml", ".yaml"]:
                    continue
                pathname = str(path.parent / path.stem)
                if not filename.startswith(pathname):
                    continue
                ref = filename.lstrip(pathname).lstrip("/").split("/")
                filename = str(path)

        with open(filename, 'r') as stream:
            new_loader = ExtendedLoader
            new_loader.root_dir = loader.root_dir
            cfg = yaml.load(stream, Loader=new_loader)

        value = cfg
        for i in ref:
            value = value[i]

        return value

    @staticmethod
    def dynamic_init(loader, node):
        import_str = node.tag.split(":", 1)[1]
        module = load_module(import_str)

        if isinstance(node, yaml.MappingNode):
            res = module(**loader.construct_mapping(node))
        elif isinstance(node, yaml.SequenceNode):
            res = module(*loader.construct_sequence(node))
        elif isinstance(node, yaml.ScalarNode):
            res = module(loader.construct_scalar(node))
        else:
            raise

        return res

    @staticmethod
    def dynamic_import(loader, node):
        import_str = node.tag.split(":", 1)[1]
        if len(re.findall(r"\((.*?)\)", import_str)) == 0 and node.value == "":
            return load_module(import_str)
        if len(re.findall(r"\((.*?)\)", import_str)) == 1 and node.value == "":
            module_str = import_str.split("(", 1)[0]
            return load_module(module_str)()

        module = load_module(import_str)

        if isinstance(node, yaml.MappingNode):
            res = module(**loader.construct_mapping(node))
        elif isinstance(node, yaml.SequenceNode):
            res = module(*loader.construct_sequence(node))
        elif isinstance(node, yaml.ScalarNode):
            res = module(loader.construct_scalar(node))
        else:
            raise

        return res

    def dynamic(self, loader, node):
        if node.tag.startswith("!extend:"):
            return self.dynamic_extend(loader, node)
        if node.tag.startswith("!init:"):
            return self.dynamic_init(loader, node)
        if node.tag.startswith("!from:"):
            return self.dynamic_from(loader, node)
        if node.tag.startswith("!import:"):
            return self.dynamic_import(loader, node)
        raise yaml.constructor.ConstructorError(
            f"could not determine a constructor for the tag '{node.tag}'"
        )
