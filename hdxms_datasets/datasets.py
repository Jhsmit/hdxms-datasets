from __future__ import annotations
import shutil
import time

import uuid
from dataclasses import dataclass, field
from functools import cached_property
from io import StringIO
from pathlib import Path
from string import Template
from typing import Union, Literal, Optional, Type

import pandas as pd
import yaml

from hdxms_datasets.process import filter_peptides, convert_temperature, parse_data_files
from hdxms_datasets.reader import read_dynamx


TEMPLATE_DIR = Path(__file__).parent / "template"


def create_dataset(
    target_dir: Path,
    author_name: str,
    tag: Optional[str] = None,
    template_dir: Path = TEMPLATE_DIR,
) -> str:
    """
    Create a dataset in the specified target directory.

    Args:
        target_dir: The directory where the dataset will be created.
        author_name: The name of the author of the dataset.
        tag: An optional tag to append to the directory name. Defaults to None.
        template_dir: The directory containing the template files for the dataset. Defaults to TEMPLATE_DIR.

    Returns:
        The id of the created dataset.

    """
    dirname = str(int(time.time()))

    if tag:
        dirname += f"_{tag}"

    dirname += f"_{author_name}"

    target_dir.mkdir(parents=True, exist_ok=True)
    target_dir = target_dir / dirname

    shutil.copytree(template_dir, target_dir)

    (target_dir / "readme.md").write_text(f"# {dirname}")

    return dirname


@dataclass(frozen=True)
class DataFile(object):
    name: str

    format: Literal["DynamX"]

    filepath_or_buffer: Union[Path, StringIO]

    time_conversion: tuple[Literal["h", "min", "s"], Literal["h", "min", "s"]] = ("min", "s")
    # from, to time conversion

    @cached_property
    def data(self) -> pd.DataFrame:
        # TODO convert time after reading
        if self.format == "DynamX":
            data = read_dynamx(self.filepath_or_buffer, time_conversion=self.time_conversion)
        else:
            raise ValueError(f"Invalid format {self.format!r}")

        if isinstance(self.filepath_or_buffer, StringIO):
            self.filepath_or_buffer.seek(0)

        return data


@dataclass(frozen=True)
class DataSet(object):
    data_id: str
    """Unique identifier for the dataset"""

    data_files: dict[str, DataFile]
    """Dictionary of data files"""

    hdx_spec: dict
    """Dictionary with HDX-MS state specification"""

    metadata: dict = field(default_factory=dict)
    """Optional metadata"""

    _cache: dict[tuple[str, str], pd.DataFrame] = field(init=False, default_factory=dict)

    @classmethod
    def from_spec(
        cls,
        hdx_spec: dict,
        data_dir: Path,
        data_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        metadata = metadata or {}
        data_id = data_id or uuid.uuid4().hex
        data_files = parse_data_files(hdx_spec["data_files"], data_dir)

        return cls(data_id, data_files, hdx_spec, metadata)

    @property
    def state_spec(self) -> dict:
        return self.hdx_spec["states"]

    @property
    def states(self) -> list[str]:
        return list(self.state_spec.keys())

    def get_metadata(self, state: Union[str, int]) -> dict:
        """
        Returns metadata for a given state
        """

        state = self.states[state] if isinstance(state, int) else state
        return {**self.hdx_spec.get("metadata", {}), **self.state_spec[state].get("metadata", {})}

    @property
    def peptides_per_state(self) -> dict[str, list[str]]:
        """Dictionary of state names and list of peptide sets for each state"""
        return {state: list(spec["peptides"]) for state, spec in self.state_spec.items()}

    @property
    def peptide_sets(self) -> dict[str, dict[str, pd.DataFrame]]:
        peptides_dfs = {}
        peptides_per_state = {
            state: list(spec["peptides"]) for state, spec in self.state_spec.items()
        }
        for state, peptides in peptides_per_state.items():
            peptides_dfs[state] = {
                peptide_set: self.load_peptides(state, peptide_set) for peptide_set in peptides
            }

        return peptides_dfs

    def load(self) -> dict[str, dict[str, pd.DataFrame]]:
        """
        Loads all peptide sets for all states.

        Returns:
            Dictionary of state names and dictionary of peptide sets for each state.
        """
        return {state: self.load_state(state) for state in self.states}

    def load_state(self, state: Union[str, int]) -> dict[str, pd.DataFrame]:
        """
        Load all peptide sets for a given state.

        Args:
            state: State name or index of state in the HDX specification file.

        Returns:
            Dictionary of peptide sets for a given state.
        """

        state = self.states[state] if isinstance(state, int) else state
        return {
            peptide_set: self.load_peptides(state, peptide_set)
            for peptide_set in self.state_spec[state]["peptides"].keys()
        }

    def load_peptides(self, state: Union[str, int], peptides: str) -> pd.DataFrame:
        """
        Load a single set of peptides for a given state.

        Args:
            state: State name or index of state in the HDX specification file.
            peptides: Name of the peptide set.

        Returns:
            DataFrame with peptide data.
        """

        state = self.states[state] if isinstance(state, int) else state
        return self._load_peptides(state, peptides)

    def _load_peptides(self, state: str, peptides: str) -> pd.DataFrame:
        """
        Load a single set of peptides for a given state.

        Returned dataframes are cached for faster subsequent access.

        Args:
            state: State name.
            peptides: Name of the peptide set.

        Returns:
            DataFrame with peptide data.

        """

        if (state, peptides) in self._cache:
            return self._cache[(state, peptides)]

        peptide_spec = self.state_spec[state]["peptides"][peptides]
        df = self.data_files[peptide_spec["data_file"]].data

        filter_fields = {"state", "exposure", "query", "dropna"}
        peptide_df = filter_peptides(
            df, **{k: v for k, v in peptide_spec.items() if k in filter_fields}
        )

        self._cache[(state, peptides)] = peptide_df

        return peptide_df

    def describe(
        self,
        peptide_template: Optional[
            str
        ] = "Total peptides: $num_peptides, timepoints: $num_timepoints",
        metadata_template: Optional[str] = "Temperature: $temperature, pH: $pH",
        return_type: Union[Type[str], type[dict]] = str,
    ) -> Union[dict, str]:
        output_dict = {}
        for state, peptides in self.peptides_per_state.items():
            state_desc = {}
            if peptide_template:
                for peptide_set_name in peptides:
                    peptide_df = self.peptide_sets[state][peptide_set_name]
                    timepoints = peptide_df["exposure"].unique()
                    mapping = {
                        "num_peptides": len(peptide_df),
                        "num_timepoints": len(timepoints),
                        "timepoints": ", ".join([f"{t:.1f}" for t in timepoints]),
                    }
                    mapping["timepoints"]
                    state_desc[peptide_set_name] = Template(peptide_template).substitute(**mapping)
            if metadata_template:
                mapping = self.get_metadata(state)
                if temperature_dict := mapping.pop("temperature", None):
                    mapping["temperature"] = f"{convert_temperature(temperature_dict)} C"

                state_desc["metadata"] = Template(metadata_template).substitute(**mapping)

            output_dict[state] = state_desc

        if return_type is str:
            return yaml.dump(output_dict, sort_keys=False)
        elif return_type is dict:
            return output_dict
        else:
            raise TypeError(f"Invalid return type {return_type!r}")

    def cite(self) -> str:
        """
        Returns citation information
        """
        try:
            return self.metadata["publications"]
        except KeyError:
            return "No publication information available"

    def __len__(self) -> int:
        return len(self.states)


# was refactored to DataSet
HDXDataSet = DataSet
