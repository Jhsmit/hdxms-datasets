"""Top-level package for HDXMS Datasets."""

from hdxms_datasets.datasets import DataVault, StateParser
from hdxms_datasets.config import cfg

from . import _version
__version__ = _version.get_versions()['version']
