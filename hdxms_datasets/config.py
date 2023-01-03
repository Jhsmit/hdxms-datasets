from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf, DictConfig, DictKeyType
from packaging import version


PACKAGE_NAME = 'hdxms_datasets'

def reset_config():
    """Create a new config.yaml file in the user home dir/.hdxms_datasets folder"""

    with open(conf_home_pth, "w") as target:
        from hdxms_datasets.__version__ import __version__

        version_string = f"# {PACKAGE_NAME} configuration file " + __version__ + "\n\n"
        target.write(version_string)

        with open(current_dir / "config.yaml") as source:
            for line in source:
                target.write(line)


class Singleton(type):
    _instances: dict[type, Singleton] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def instance(cls: Any, *args: Any, **kwargs: Any) -> Any:
        return cls(*args, **kwargs)


class HDXMSDatasetsConfig(metaclass=Singleton):
    __slots__ = ["conf"]

    def __init__(self) -> None:
        self.conf = None

    def __getattr__(self, item: str) -> Any:
        return getattr(self.conf, item)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self.__slots__:
            super().__setattr__(key, value)
        elif key in self.conf.keys():
            setattr(self.conf, key, value)
        else:
            raise AttributeError(f"Config has no attribute {key}")

    def load_config(self, config_file: os.PathLike[str]):
        conf = OmegaConf.create(Path(config_file).read_text())
        self.set_config(conf)

    def set_config(self, conf: DictConfig) -> None:
        self.conf = conf

    def get(self, key: DictKeyType, default_value: Any = None) -> Any:
        return self.conf.get(key, default_value)

    @property
    def database_dir(self) -> Path:
        pth = self.conf.database_dir
        if "~" in pth:
            database_dir = Path(pth.replace("~", str(Path.home())))
        elif "$home" in pth:
            database_dir = Path(pth.replace("$home", str(Path.home())))
        else:
            database_dir = Path(pth)

        return database_dir


def valid_config() -> bool:
    """Checks if the current config file in the user home directory is a valid config
    file for the current hdxms_datasets version

    """
    if not conf_home_pth.exists():
        return False
    else:
        with open(conf_home_pth, "r") as f:
            version_string = f.readline().strip("; ").split(" ")[-1]

        from hdxms_datasets.__version__ import __version__

        hdxms_datasets_version = version.parse(__version__)
        cfg_version = version.parse(version_string)

        return hdxms_datasets_version.public == cfg_version.public


# https://stackoverflow.com/questions/6198372/most-pythonic-way-to-provide-global-configuration-variables-in-config-py/25880082
class CfgClass(metaclass=Singleton):
    def __init__(self, config=None):
        self._config = {} if config is None else config

    def __getitem__(self, item):
        return self._config[item]


home_dir = Path.home()
config_dir = home_dir / f".{PACKAGE_NAME}"
config_dir.mkdir(parents=False, exist_ok=True)
conf_home_pth = config_dir / "config.yaml"

current_dir = Path(__file__).parent
conf_src_pth = current_dir / "config.yaml"

# Current config version is outdated
if not valid_config():
    try:
        reset_config()
        conf = OmegaConf.load(conf_home_pth)
    except FileNotFoundError:
        # This will happen on conda-forge docker build.
        # When no config.yaml file is in home_dir / '.{PACKAGE_NAME}'
        # ConfigurationSettings will use the hardcoded version
        conf = OmegaConf.load(conf_src_pth)
        # (this is run twice due to import but should be OK since conf is singleton)
else:
    conf = OmegaConf.load(conf_home_pth)


cfg = HDXMSDatasetsConfig()
cfg.set_config(conf)
