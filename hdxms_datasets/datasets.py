from __future__ import annotations
from operator import and_
import shutil
import time

import uuid
from dataclasses import dataclass, field
from functools import cached_property, reduce
from io import StringIO
from pathlib import Path
from string import Template
from typing import Union, Literal, Optional, Type
import warnings
import narwhals as nw

import yaml

# from hdxms_datasets.process import filter_peptides, convert_temperature, parse_data_files
import hdxms_datasets.process as process
from hdxms_datasets.reader import from_dynamx_cluster, from_hdexaminer, read_csv, from_dynamx_state


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
class DataFile:
    name: str

    format: Literal["DynamX", "HDExaminer_v3", "DynamX_v3_state", "DynamX_v3_cluster"]  # TOOD fix

    filepath_or_buffer: Union[Path, StringIO]

    extension: Optional[str] = None
    """File extension, e.g. .csv, in case of a file-like object"""

    def read(self) -> nw.DataFrame:
        if isinstance(self.filepath_or_buffer, StringIO):
            extension = self.extension
            assert isinstance(extension, str), "File-like object must have an extension"
        else:
            extension = self.filepath_or_buffer.suffix[1:]

        if extension == "csv":
            return read_csv(self.filepath_or_buffer)
        else:
            raise ValueError(f"Invalid file extension {self.extension!r}")

        # TODO convert time after reading
        # if self.format in ["DynamX_v3_state", "DynamX_v3_cluster"]:
        #     data = read_dynamx(self.filepath_or_buffer, time_conversion=self.time_conversion)
        # elif self.format == "HDExaminer_v3":
        #     data = read_hdexaminer(self.filepath_or_buffer)
        # else:
        #     raise ValueError(f"Invalid format {self.format!r}")

        # if isinstance(self.filepath_or_buffer, StringIO):
        #     self.filepath_or_buffer.seek(0)

        # return data


ValueType = str | float | int


@dataclass
class Peptides:
    data_file: DataFile
    filters: dict[str, ValueType | list[ValueType]]

    metadata: dict  #
    protein: dict

    _cache: dict[tuple[bool, bool, bool, bool], nw.DataFrame] = field(
        init=False, default_factory=dict
    )

    def load(self, convert=True, aggregate=True, sort=True, drop_null=True) -> nw.DataFrame:
        cache_key = (convert, aggregate, sort, drop_null)
        if cache_key in self._cache:
            return self._cache[cache_key]

        df = process.filter_from_spec(self.data_file.read(), **self.filters)

        if aggregate and self.data_file.format == "DynamX_v3_state":
            warnings.warn("DynamX_v3_state format is pre-aggregated. Aggregation will be skipped.")
            aggregate = False

        if not convert and aggregate:
            warnings.warn("Cannot aggregate data without conversion. Aggeregation will be skipped.")
            aggregate = False

        if not convert and sort:
            warnings.warn("Cannot sort data without conversion. Sorting will be skipped.")
            sort = False

        if convert:
            if self.data_file.format == "HDExaminer_v3":
                df = from_hdexaminer(df)
            elif self.data_file.format == "DynamX_v3_cluster":
                df = from_dynamx_cluster(df)
            elif self.data_file.format == "DynamX_v3_state":
                df = from_dynamx_state(df)
            else:
                raise ValueError(f"Invalid format {self.data_file.format!r}")

        if aggregate:
            df = process.aggregate(df)

        if sort:
            df = process.sort(df)

        if drop_null:
            df = process.drop_null_columns(df)

        self._cache[cache_key] = df

        return df

    def get_temperature(self, unit="K") -> Optional[float]:
        """Get the temperature of the experiment"""
        try:
            temperature = self.metadata["temperature"]
            return process.convert_temperature(temperature, unit)
        except KeyError:
            return None

    def get_pH(self) -> Optional[float]:
        """Get the pH of the experiment"""
        try:
            return self.metadata["pH"]
        except KeyError:
            return None


@dataclass
class DataSet:
    data_id: str
    """Unique identifier for the dataset"""

    data_files: dict[str, DataFile]
    """Dictionary of data files"""

    hdx_specification: dict
    """Dictionary with HDX-MS state specification"""

    metadata: dict = field(default_factory=dict)

    peptides: dict[tuple[str, str], Peptides] = field(init=False, default_factory=dict)

    def __post_init__(self):
        # create peptide dictionary
        peptides = {}
        for state, state_spec in self.hdx_specification["states"].items():
            for peptide_set, peptide_spec in state_spec["peptides"].items():
                peptides[(state, peptide_set)] = Peptides(
                    data_file=self.data_files[peptide_spec["data_file"]],
                    filters=peptide_spec["filters"],
                    metadata=peptide_spec.get("metadata", {}),
                    protein=peptide_spec.get("protein", {}),
                )
        self.peptides = peptides

    def __getitem__(self, key: tuple[str, str]) -> Peptides:
        """
        Get the Peptides object for a given state and peptide set.

        Args:
            key: Tuple of state name and peptide set name.

        Returns:
            Peptides object for the given state and peptide set.

        """
        return self.peptides[key]

    @classmethod
    def from_spec(
        cls,
        hdx_spec: dict,
        data_dir: Path,
        data_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        data_id = data_id or uuid.uuid4().hex
        data_files = process.parse_data_files(hdx_spec["data_files"], data_dir)

        return cls(
            data_id=data_id,
            data_files=data_files,
            hdx_specification=hdx_spec,
            metadata=metadata or {},
        )

    @property
    def state_spec(self) -> dict:
        return self.hdx_specification["states"]

    @property
    def states(self) -> list[str]:
        return list(self.state_spec.keys())

    # def get_metadata(self, state: Union[str, int], peptides: str) -> dict:
    #     """
    #     Returns metadata for a given state
    #     """

    #     state = self.states[state] if isinstance(state, int) else state
    #     return {**self.hdx_specification.get("metadata", {}), **self.state_spec[state].get("metadata", {})}

    @property
    def peptides_per_state(self) -> dict[str, list[str]]:
        """Dictionary of state names and list of peptide sets for each state"""
        return {state: list(spec["peptides"]) for state, spec in self.state_spec.items()}

    # @property
    # def peptide_sets(self) -> dict[str, dict[str, nw.DataFrame]]:
    #     peptides_dfs = {}
    #     peptides_per_state = {
    #         state: list(spec["peptides"]) for state, spec in self.state_spec.items()
    #     }
    #     for state, peptides in peptides_per_state.items():
    #         peptides_dfs[state] = {
    #             peptide_set: self.load_peptides(state, peptide_set) for peptide_set in peptides
    #         }

    #     return peptides_dfs

    # def load(self) -> dict[str, dict[str, nw.DataFrame]]:
    #     """
    #     Loads all peptide sets for all states.

    #     Returns:
    #         Dictionary of state names and dictionary of peptide sets for each state.
    #     """
    #     return {state: self.load_state(state) for state in self.states}

    # def load_state(self, state: Union[str, int]) -> dict[str, nw.DataFrame]:
    #     """
    #     Load all peptide sets for a given state.

    #     Args:
    #         state: State name or index of state in the HDX specification file.

    #     Returns:
    #         Dictionary of peptide sets for a given state.
    #     """

    #     state = self.states[state] if isinstance(state, int) else state
    #     return {
    #         peptide_set: self.load_peptides(state, peptide_set)
    #         for peptide_set in self.state_spec[state]["peptides"].keys()
    #     }

    def get_peptides(self, state: str | int, peptide_set: str) -> Peptides:
        """
        Get the Peptides object for a given state and peptide set.

        Args:
            state: State name.
            peptide_set: Name of the peptide set.

        Returns:
            Peptides object for the given state and peptide set.

        """
        state = self.states[state] if isinstance(state, int) else state
        return self.peptides[(state, peptide_set)]

    # def load_peptides(
    #     self,
    #     state: str | int,
    #     peptides: str,
    #     convert=True,
    #     aggregate=True,
    #     sort=True,
    #     drop_null=True,
    # ) -> nw.DataFrame:
    #     """
    #     Load a single set of peptides for a given state.

    #     Returned dataframes are cached for faster subsequent access.

    #     Args:
    #         state: State name.
    #         peptides: Name of the peptide set.
    #         convert: Whether to convert the data to open-hdxms standard
    #         aggregate: Whether to aggregate the data. must be converted first.
    #         sort: Whether to sort the data. must be converted first.
    #         drop_null: Whether to drop all-null columns.

    #     Returns:
    #         DataFrame with peptide data.

    #     """

    #     state = self.states[state] if isinstance(state, int) else state
    #     peptide_spec = self.state_spec[state]["peptides"][peptides]
    #     data_file = self.data_files[peptide_spec["data_file"]]

    #     df = process.filter_from_spec(data_file.read(), **peptide_spec["filters"])

    #     if not convert and aggregate:
    #         warnings.warn("Cannot aggregate data without conversion. Aggeregation will be skipped.")
    #         aggregate = False

    #     if not convert and sort:
    #         warnings.warn("Cannot sort data without conversion. Sorting will be skipped.")
    #         sort = False

    #     if convert:
    #         if data_file.format == "HDExaminer_v3":
    #             df = from_hdexaminer(df)
    #         elif data_file.format == "DynamX_v3_cluster":
    #             df = from_dynamx(df)
    #         else:
    #             raise ValueError(f"Invalid format {data_file.format!r}")

    #     if aggregate:
    #         df = process.aggregate(df)

    #     if sort:
    #         df = process.sort(df)

    #     if drop_null:
    #         df = process.drop_null_columns(df)

    #     return df

    def describe(
        self,
        peptide_template: Optional[str] = "Total peptides: $num_peptides, timepoints: $timepoints",
        return_type: Union[Type[str], type[dict]] = str,
    ) -> Union[dict, str]:
        def fmt_t(val: str | float | int) -> str:
            if isinstance(val, str):
                return val
            elif isinstance(val, (int, float)):
                return f"{val:.1f}"
            else:
                raise TypeError(f"Invalid type {type(val)} for value {val!r}")

        output_dict = {}
        for state, peptide_types in self.peptides_per_state.items():
            state_desc = {}
            if peptide_template:
                for peptide_set_name in peptide_types:
                    peptides = self.peptides[(state, peptide_set_name)]
                    peptide_df = peptides.load()
                    timepoints = peptide_df["exposure"].unique()
                    mapping = {
                        "num_peptides": len(peptide_df),
                        "num_timepoints": len(timepoints),
                        "timepoints": ", ".join([fmt_t(t) for t in timepoints]),
                    }
                    mapping["timepoints"]
                    state_desc[peptide_set_name] = Template(peptide_template).substitute(**mapping)

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

        raise NotImplementedError("Citation information is not yet implemented")
        try:
            return self.metadata["publications"]
        except KeyError:
            return "No publication information available"

    def __len__(self) -> int:
        return len(self.states)


# was refactored to DataSet
HDXDataSet = DataSet
