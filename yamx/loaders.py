import yaml
import yaml.constructor
import importlib
import os
from yaml import Node
from pathlib import Path
from typing import IO, Callable


def _load_module(import_str: str):
    package, name = import_str.rsplit(".", maxsplit=1)
    module = importlib.import_module(package)
    return getattr(module, name)


def _load_file(filename, root=None):
    with open(filename, 'r') as stream:
        new_loader = ExtendedLoader
        new_loader.root_dir = root
        return yaml.load(stream, Loader=new_loader)


def _separate_file_from_tree(filename, suffix="y*ml"):
    path = Path(filename)
    # find dir, filename, and config tree
    name = ""
    tree = []
    while not (path.is_dir() and path.exists()):
        if name != "":
            tree += [name]
        name = path.name
        path = path.parent
        if str(path) == "/":
            break
    # recombine dir and filename
    if Path(name).suffix:
        path = path / name
        if not path.exists():
            raise ValueError(f"Could not find {name} in {path.parent}")
    else:
        path = [i for i in path.glob(f"{name}.{suffix}")]
        if len(path) != 1:
            raise ValueError(f"Found {len(path)} matches: {path}")
        path = path[0]
    # tree is in wrong order and must be reversed
    tree.reverse()
    return path, tree


def _parse_from_tag(filename, suffix="y*ml"):
    path, tree = _separate_file_from_tree(filename, suffix=suffix)

    with path.open() as fp:
        cfg = yaml.safe_load(fp)

    for i in tree:
        if i.isnumeric():
            i = int(i)
        cfg = cfg[i]

    return cfg


class ExtendedLoader(yaml.SafeLoader):
    """Extend `yaml.SafeLoader` with additional tags.

    Example
    -------

    Using `!from`
    
    .. highlight:: yaml
    .. code-block:: yaml
        # constants.yaml
        value: 123

    >>> import yamx
    >>> yamx.loads("key: !from:constants.yaml")
    {key: {value: 123}}
    >>> yamx.loads("key: !from:constants.yaml/value")
    {key: 123}
    >>> yamx.loads("key: !from:constants/value")
    {key: 123}
    """
    root_dir: Path = None
    suffix: str = "y*ml"

    def __init__(self, stream: IO):
        """_summary_

        Parameters
        ----------
        stream : IO
            IO stream of a YAML configuration file.
        """
        if self.root_dir is None:
            self.root_dir = Path(stream.name).resolve().parent
        # extend node by content of another YAML file
        self.add_constructor(None, self._dynamic)
        super(ExtendedLoader, self).__init__(stream)

    def _from(self, loader: "ExtendedLoader", node: Node):
        # define file path
        filename = node.tag.split(":", 1)[1]
        if not filename.startswith("/"):
            filename = str(loader.root_dir / filename)
        #
        cfg = _parse_from_tag(filename, suffix=self.suffix)
        #
        if isinstance(node, yaml.MappingNode):
            return {**cfg, **loader.construct_mapping(node)}
        elif isinstance(node, yaml.SequenceNode):
            return [*cfg, *loader.construct_sequence(node)]

        return cfg

    @staticmethod
    def _import(loader: "ExtendedLoader", node: Node):
        assert node.value == ""
        return _load_module(node.tag.split(":", 1)[1])

    def _collect_parameters(self, loader, node):
        args = []
        kwargs = {}
        # no arguments provided
        if node.value == "":
            return args, kwargs
        # arguments of call must be provided in a sequence
        assert isinstance(node, yaml.SequenceNode)
        for subnode in node.value:
            value = self._dynamic(loader, subnode)
            if isinstance(value, dict):
                for k, v in value.items():
                    kwargs[k] = v
            else:
                args.append(value)
        return args, kwargs

    def _init(self, loader: "ExtendedLoader", node: Node):
        import_str = node.tag.split(":", 1)[1]
        module = _load_module(import_str)
        args, kwargs = self._collect_parameters(loader, node)
        return module(*args, **kwargs)

    def _call(self, loader: "ExtendedLoader", node: Node):
        func_str = node.tag.split(":")[1]
        args, kwargs = self._collect_parameters(loader, node)
        return func_str, args, kwargs

    @staticmethod
    def _chain(loader: "ExtendedLoader", node: Node):
        assert isinstance(node, yaml.SequenceNode)
        value = loader.construct_sequence(node)
        module = value[0]
        chain = value[1:]
        for i, (method, args, kwargs) in enumerate(chain):
            module = getattr(module, method)
            if isinstance(module, Callable):
                module = module(*args, **kwargs)
            elif not (i + 1 == len(chain) and len(args) + len(kwargs) == 0):
                raise
        return module

    @staticmethod
    def _env(loader: "ExtendedLoader", node: Node):
        if ":" in node.tag:
            env_name = node.tag.split(":", 1)[1]
        elif isinstance(node, yaml.ScalarNode):
            env_name = loader.construct_scalar(node)
        value: str = os.environ.get(env_name)

        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
            
        if value[0] in ["'", '"'] and value[-1] in ["'", '"']:
            value = value[1:-1]

        return value

    def _dynamic(self, loader: "ExtendedLoader", node: Node):
        # list of custom tags to parse
        if node.tag.startswith("!chain"):
            return self._chain(loader, node)
        if node.tag.startswith("!call"):
            return self._call(loader, node)
        if node.tag.startswith("!init"):
            return self._init(loader, node)
        if node.tag.startswith("!from"):
            return self._from(loader, node)
        if node.tag.startswith("!import"):
            return self._import(loader, node)
        if node.tag.startswith("!env"):
            return self._env(loader, node)
        # parse standard tags
        if isinstance(node, yaml.ScalarNode):
            constructor = loader.construct_scalar
        elif isinstance(node, yaml.SequenceNode):
            constructor = loader.construct_sequence
        elif isinstance(node, yaml.MappingNode):
            constructor = loader.construct_mapping
        else:
            raise
        return constructor(node)
