from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from io import StringIO
from pathlib import Path
from typing import Union, Literal, Optional

import pandas as pd

from hdxms_datasets.process import filter_peptides
from hdxms_datasets.reader import read_dynamx

from hdxms_datasets.config import cfg


@dataclass(frozen=True)
class DataFile(object):

    name: str

    format: Literal["DynamX"]

    filepath_or_buffer: Union[Path, StringIO]

    @cached_property
    def data(self) -> pd.DataFrame:
        if self.format == "DynamX":
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
            for name, spec in self.hdx_spec["data_files"].items():
                datafile = DataFile(
                    name=name,
                    filepath_or_buffer=data_src / spec["filename"],
                    **{k: v for k, v in spec.items() if k != "filename"},
                )
                self.data_files[name] = datafile

        elif isinstance(data_src, dict):
            self.data_files = data_src
        else:
            raise TypeError(f"Invalid data type {type(data_src)!r}, must be path or dict")

    def load_peptides(self, state: Union[str, int], peptides: str) -> pd.DataFrame:
        # todo allow peptides as int, None
        state = self.states[state] if isinstance(state, int) else state
        peptide_spec = self.hdx_spec["states"][state]["peptides"][peptides]

        df = self.data_files[peptide_spec["data_file"]].data

        filter_fields = {"state", "exposure", "query", "dropna"}
        peptides = filter_peptides(
            df, **{k: v for k, v in peptide_spec.items() if k in filter_fields}
        )

        return peptides

    @property
    def states(self) -> list[str]:
        return list(self.hdx_spec["states"].keys())

    @property
    def state_peptide_sets(self) -> dict[str, list[str]]:
        """Dictionary of state names and list of peptide sets for each state"""
        return {state: list(spec["peptides"]) for state, spec in self.hdx_spec["states"].items()}

    @cached_property
    def peptide_sets(self) -> dict[str, dict[str, pd.DataFrame]]:

        peptides_dfs = {}
        for state, peptides in self.state_peptide_sets.items():
            peptides_dfs[state] = {
                peptide_set: self.load_peptides(state, peptide_set) for peptide_set in peptides
            }

        return peptides_dfs


# TODO remove parser and merge with HDXDataSet
@dataclass(frozen=True)
class HDXDataSet(object):

    data_id: str
    """Unique identifier for the dataset"""

    data_files: dict[str, DataFile]
    """Dictionary of data files"""

    state_spec: dict
    """Dictionary with HDX-MS state specification"""

    metadata: Optional[dict]
    """Optional metadata"""

    @property
    def states(self) -> list[str]:
        return list(self.state_spec.keys())

    @property
    def state_peptide_sets(self) -> dict[str, list[str]]:
        """Dictionary of state names and list of peptide sets for each state"""
        return {state: list(spec["peptides"]) for state, spec in self.state_spec.items()}

    @cached_property
    def peptide_sets(self) -> dict[str, dict[str, pd.DataFrame]]:
        peptides_dfs = {}
        for state, peptides in self.state_peptide_sets.items():
            peptides_dfs[state] = {
                peptide_set: self.load_peptides(state, peptide_set) for peptide_set in peptides
            }

        return peptides_dfs

    def load_peptides(self, state: Union[str, int], peptides: str) -> pd.DataFrame:
        """
        Load a single set of peptides for a given state
        """
        state = self.states[state] if isinstance(state, int) else state
        peptide_spec = self.state_spec[state]["peptides"][peptides]

        df = self.data_files[peptide_spec["data_file"]].data

        filter_fields = {"state", "exposure", "query", "dropna"}
        peptides = filter_peptides(
            df, **{k: v for k, v in peptide_spec.items() if k in filter_fields}
        )

        return peptides

    def describe(self):
        """
        Returns states and peptides in the dataset
        """
        ...
        output = {}

    def cite(self) -> str:
        """
        Returns citation information
        """

        return "Not implemented"

    def __len__(self) -> int:
        return len(self.parser.states)
