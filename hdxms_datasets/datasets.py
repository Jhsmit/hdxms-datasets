from __future__ import annotations

import os
import shutil
import urllib.parse, urllib.error
from dataclasses import dataclass
from functools import cached_property
from io import StringIO
from pathlib import Path
from typing import Union, Literal, Optional, Protocol, Type

import pandas as pd
import yaml
from sphinx.util import requests

from hdxms_datasets.process import filter_peptides
from hdxms_datasets.reader import read_dynamx

from hdxms_datasets.config import cfg


@dataclass(frozen=True)
class DataFile(object):

    name: str

    format: Literal['DynamX']

    filepath_or_buffer: Union[Path, StringIO]

    @cached_property
    def data(self) -> pd.DataFrame:
        if self.format == 'DynamX':
            # from, to time conversion
            time_conversion = (cfg.dynamx.time_unit, cfg.time_unit)

            data = read_dynamx(self.filepath_or_buffer, time_conversion=time_conversion)
        else:
            raise ValueError(f"Invalid format {self.format!r}")

        if isinstance(self.filepath_or_buffer, StringIO):
            self.filepath_or_buffer.seek(0)

        return data


class StateParser(object):
    """

    Args:
        hdx_spec: Dictionary with HDX-MS state specification.
        data_src: Optional data source with input data files. If not specified, current
            directory is used. Otherwise, either a data source path can be specified or
            data can be given as a dictionary, where keys are filenames and values are
            :class:`~io.StringIO` with file contents.
    """

    def __init__(
        self,
        hdx_spec: dict,
        data_src: Union[os.PathLike[str], str, dict[str, DataFile], None],
    ) -> None:

        self.hdx_spec = hdx_spec
        self.data_files: dict[str, DataFile] = {}

        if isinstance(data_src, (os.PathLike, str)):
            data_src = Path(data_src) or Path(".")
            for name, spec in self.hdx_spec['data_files'].items():
                datafile = DataFile(name=name,
                                    filepath_or_buffer= data_src / spec['filename'],
                                    **{k: v for k, v in spec.items() if k != 'filename'},
                                    )
                self.data_files[name] = datafile

        elif isinstance(data_src, dict):
            self.data_files = data_src
        else:
            raise TypeError(
                f"Invalid data type {type(data_src)!r}, must be path or dict"
            )

    def load_peptides(self, state: Union[str, int], peptides: str) -> pd.DataFrame:
        #todo allow peptides as int, None
        state = self.states[state] if isinstance(state, int) else state
        peptide_spec = self.hdx_spec["states"][state]['peptides'][peptides]

        df = self.data_files[peptide_spec['data_file']].data

        filter_fields = {'state', 'exposure', 'query', 'dropna'}
        peptides = filter_peptides(df, **{k: v for k, v in peptide_spec.items() if k in filter_fields})

        return peptides

    @property
    def states(self) -> list[str]:
        return list(self.hdx_spec['states'].keys())


@dataclass
class HDXDataSet(object):

    parser: StateParser

    data_id: str

    metadata: Optional[dict]

    def describe(self):
        """
        Returns states and peptides in the dataset
        """
        ...

    def cite(self) -> str:
        """
        Returns citation information
        """

        return "Not implemented"


    # metadata:
        # publications:
        # institute:
        # papers:


class DataVault(object):
    def __init__(self, cache_dir: Optional[Union[Path[str], str]] = None,
                 parser: Type[StateParser] = StateParser):

        if cache_dir is None:
            self.cache_dir = Path.home() / '.hdxms_datasets' / 'datasets'
            self.cache_dir.mkdir(exist_ok=True, parents=True)
        else:
            self.cache_dir: Path = Path(cache_dir)
            if not self.cache_dir.exists():
                raise FileNotFoundError(f"Cache directory '{self.cache_dir}' does not exist")

        self.parser = parser

    def filter(self, *spec: dict):
        # filters list of available datasets
        ...

    @cached_property
    def index(self) -> list[str]:
        """List of available datasets in the remote database"""

        url = urllib.parse.urljoin(cfg.database_url, 'index.txt')
        response = requests.get(url)
        if response.ok:
            index = response.text.split('\n')[1:]
            return index
        else:
            return []

    @property
    def datasets(self) -> list[str]:
        """List of available datasets in the cache dir"""
        return [d.stem for d in self.cache_dir.iterdir() if self.is_dataset(d)]

    @staticmethod
    def is_dataset(path: Path) -> bool:
        """
        Checks if the supplied path is a HDX-MS dataset.
        """

        return (path / 'hdx_spec.yaml').exists()

    async def fetch_datasets(self, n: Optional[str] = None, data_ids: Optional[list[str]] = None):
        """
        Asynchronously download multiple datasets
        """
        if n is None and data_ids is None:
            n = 10

        if data_ids:
            # Download specified datasets to cache_dir
            ...

        elif n:
            # Download n new datasets to cache_dir
            ...

    def fetch_dataset(self, data_id: str) -> bool:
        """
        Download a dataset from the online repository to the cache dir

        :param data_id:
        :return:
        """

        output_pth = cfg.database_dir / data_id
        if output_pth.exists():
            return False
        else:
            output_pth.mkdir()

        dataset_url = urllib.parse.urljoin(cfg.database_url, data_id + "/")

        files = ['hdx_spec.yaml', 'metadata.yaml']
        optional_files = ['CITATION.cff']
        for f in files + optional_files:
            url = urllib.parse.urljoin(dataset_url, f)
            response = requests.get(url)

            if response.ok:
                (output_pth / f).write_bytes(response.content)

            elif f in files:
                raise urllib.error.HTTPError(url, response.status_code, f"Error for file {f!r}", response.headers, None)

            if f == 'hdx_spec.yaml':
                hdx_spec = yaml.safe_load(response.text)

        data_pth = output_pth / 'data'
        data_pth.mkdir()

        for file_spec in hdx_spec['data_files'].values():
            filename = file_spec["filename"]
            f_url = urllib.parse.urljoin(dataset_url, filename)
            response = requests.get(f_url)

            if response.ok:
                (output_pth / filename).write_bytes(response.content)
            else:
                raise urllib.error.HTTPError(f_url, response.status_code, f"Error for data file {filename!r}", response.headers, None)

        return True

    def clear_cache(self) -> None:
        for dir in self.cache_dir.iterdir():
            shutil.rmtree(dir)

    def load_dataset(self, data_id: str) -> HDXDataSet:
        ...
        # if not in cache dir -> fetch

        hdx_spec = yaml.safe_load((self.cache_dir / data_id / "hdx_spec.yaml").read_text())
        parser = self.parser(hdx_spec, self.cache_dir / data_id)
        metadata = yaml.safe_load((self.cache_dir / data_id / "metadata.yaml").read_text())
        return HDXDataSet(
            parser=parser, data_id=data_id, metadata=metadata)


def load_dataset(pth):
    state_dict = yaml.safe_load((pth / "hdx_spec.yaml").read_text())

    data_files_dict = state_dict["data_files"]
    data_files = {}
    for file_name, spec in data_files_dict.items():
        file_pth = pth / spec["filename"]
        fmt = spec["format"]
        if fmt.lower() == "dynamx":
            df = read_dynamx(file_pth)  # lazy?
            data_files[file_name] = df
        elif fmt.lower == "pdb":
            data_files[file_name] = file_pth.read_text()
