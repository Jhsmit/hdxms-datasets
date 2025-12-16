from pathlib import Path
import warnings
import narwhals as nw
from abc import ABC, abstractmethod
from hdxms_datasets.convert import (
    from_dynamx_cluster,
    from_dynamx_state,
    from_hdexaminer_all_results,
    from_hdexaminer_peptide_pool,
    from_hdexaminer_uptake_summary,
    from_hxms,
)

from hdxms_datasets.reader import read_csv, read_hdexaminer_peptide_pool, read_hxms


# a list of supported columns for open HDX peptide tables
STANDARD_COLUMNS = [
    "start",
    "end",
    "sequence",
    "state",
    "replicate",
    "exposure",
    "centroid_mass",
    "centroid_mass_sd",
    "centroid_mz",
    "centroid_mz_sd",
    "rt",
    "rt_sd",
    "charge",
    "intensity",
    "pH",
    "temperature",
]

OPTIONAL_COLUMNS = [
    "uptake",
    "uptake_sd",
    "max_uptake",
]

COMPUTED_COLUMS = [
    "frac_fd_control",
    "frac_fd_control_sd",
    "frac_max_uptake",
    "frac_max_uptake_sd",
]

OPEN_HDX_COLUMNS = STANDARD_COLUMNS + OPTIONAL_COLUMNS + COMPUTED_COLUMS

FMT_REGISTRY: dict[str, type["FormatSpec"]] = {}


class FormatSpec(ABC):
    """Specification for a HDX data format

    Args:
        name: Name of the format.
        returned_columns: List of columns returned by .read(). May return
            additional columns depending on the format.
        filter_columns: List of columns that can be used to filter data.
        is_valid_file: Function to check if a file is valid for this format.
        reader: Function to read a file into a DataFrame.
        converter: Function to convert a DataFrame to OpenHDX format.
        aggregated: Whether the format is aggregated, not aggregated, or None if
            it depends on the data.
        doc: Optional documentation string.

    """

    doc: str = ""
    returned_columns: list[str]
    filter_columns: list[str] = []
    aggregated: bool | None = None

    def __init_subclass__(cls):
        """Register format in global registry."""

        required_class_attrs = ["returned_columns"]
        for attr in required_class_attrs:
            if not hasattr(cls, attr):
                raise NotImplementedError(
                    f"Class attribute '{attr}' must be defined in subclass '{cls.__name__}'"
                )

        if cls.__name__ in FMT_REGISTRY:
            warnings.warn((f"Format '{cls.__name__}' is already registered. Overwriting."))
        FMT_REGISTRY[cls.__name__] = cls

    @classmethod
    @abstractmethod
    def read(cls, path: Path) -> nw.DataFrame:
        """Read the data to a dataframe using the format's reader."""

    @classmethod
    @abstractmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        """Convert DataFrame to OpenHDX format."""

    @classmethod
    @abstractmethod
    def valid_file(cls, path: Path) -> bool:
        """Default format identification based on file extension."""

    @classmethod
    @abstractmethod
    def load(cls, path: Path, convert=True) -> nw.DataFrame:
        """Load and convert a file to OpenHDX format."""
        df = cls.read(path)
        if convert:
            df = cls.convert(df)
        return df


def read_columns(path: Path, line: int = 0) -> list[str]:
    with open(path, "r") as fh:
        for _ in range(line):
            fh.readline()
        header = fh.readline().strip()

    columns = [col.strip() for col in header.split(",")]
    return columns


class DynamX_v3_state(FormatSpec):
    returned_columns = [
        "Protein",
        "Start",
        "End",
        "Sequence",
        "Modification",
        "Fragment",
        "MaxUptake",
        "MHP",
        "State",
        "Exposure",
        "Center",
        "Center SD",
        "Uptake",
        "Uptake SD",
        "RT",
        "RT SD",
    ]

    filter_columns = ["Protein", "State", "Exposure"]
    aggregated = True

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_csv(path)

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return from_dynamx_state(df)

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        columns = read_columns(path)
        return set(cls.returned_columns).issubset(set(columns))


# vx_state columns are subset of DynamX_v3_state; thus we need to make sure to check for
# DynamX_v3_state first to ensure correct identification
class DynamX_vx_state(FormatSpec):
    returned_columns = [
        "Protein",
        "Start",
        "End",
        "Sequence",
        "MaxUptake",
        "MHP",
        "State",
        "Exposure",
        "Center",
        "Center SD",
        "Uptake",
        "Uptake SD",
        "RT",
        "RT SD",
    ]

    filter_columns = ["Protein", "State", "Exposure"]
    aggregated = True

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_csv(path)

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return from_dynamx_state(df)

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        columns = read_columns(path)
        return set(cls.returned_columns).issubset(set(columns))


class DynamX_v3_cluster(FormatSpec):
    returned_columns = [
        "Protein",
        "Start",
        "End",
        "Sequence",
        "Modification",
        "Fragment",
        "MaxUptake",
        "MHP",
        "State",
        "Exposure",
        "File",
        "z",
        "RT",
        "Inten",
        "Center",
    ]

    filter_columns = ["Protein", "State", "Exposure"]
    aggregated = False

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_csv(path)

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return from_dynamx_cluster(df)

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        columns = read_columns(path)
        return set(cls.returned_columns).issubset(set(columns))


class HDExaminer_all_results(FormatSpec):
    returned_columns = [
        "Protein State",
        "Deut Time",
        "Experiment",
        "Start",
        "End",
        "Sequence",
        "Charge",
        "Search RT",
        "Actual RT",
        "# Spectra",
        "Peak Width",
        "m/z Shift",
        "Max Inty",
        "Exp Cent",
        "Theor Cent",
        "Score",
        "Cent Diff",
        "# Deut",
        "Deut %",
        "Confidence",
    ]

    filter_columns = ["Protein State", "Deut Time"]
    aggregated = False

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_csv(path)

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return from_hdexaminer_all_results(df)

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        columns = read_columns(path)
        return set(cls.returned_columns).issubset(set(columns))


class HDExaminer_all_results_with_units(HDExaminer_all_results):
    """
    There are some 'all results' files out there which have a variation on the standard columns
    where the units are incuded in the column names:
    - Peak Width > Peak Width Da
    - m/z Shift > m/z Shift Da
    """

    returned_columns = [
        "Protein State",
        "Deut Time",
        "Experiment",
        "Start",
        "End",
        "Sequence",
        "Charge",
        "Search RT",
        "Actual RT",
        "# Spectra",
        "Peak Width Da",
        "m/z Shift Da",
        "Max Inty",
        "Exp Cent",
        "Theor Cent",
        "Score",
        "Cent Diff",
        "# Deut",
        "Deut %",
        "Confidence",
    ]


class HDExaminer_peptide_pool(FormatSpec):
    """HDExaminer Peptide Pool format specification

    This file consists of an inital block of 8 columns (first 8 in returned_columns),
    followed by a repeating number of typically 8 columns per exposure (the last 8 in returned_columns).
    The repeating columns blocks might have 6 columns for FD control blocks. These columns are:

    >> ['Start RT', 'End RT', '#D', '%Max D', 'Score', 'Conf']

    The first line in this file is header with exposure times, in seconds formatted as '10s', or 'Full-D'
    for the full deuterated control.

    Reading the file returns an additional "Exposure" column with values derived from the header line.

    """

    returned_columns = [
        "State",
        "Protein",
        "Start",
        "End",
        "Sequence",
        "Search RT",
        "Charge",
        "Max D",
        "Start RT",
        "End RT",
        "#D",
        "%D",
        "#D right",
        "%D right",
        "Score",
        "Conf",
        "Exposure",
    ]

    filter_columns = ["Protein", "State", "Exposure"]
    aggregated = False

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_hdexaminer_peptide_pool(path)

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return from_hdexaminer_peptide_pool(df)

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        columns = read_columns(path, line=1)
        return set(cls.returned_columns[:-1]).issubset(set(columns))


class HDExaminer_uptake_summary(FormatSpec):
    """HDExaminer Uptake Summary Table format specification.

    This is the output of HD Examiner's "Uptake Summary Table" report.

    The resulting table is aggregated, ie only one row per peptide/timepoint.

    Full deuterated control is labelled as 'MAX', exposure times are in seconds,
    e.g. '10', '100', etc.

    Typically includes nondeuterated control as '0'.

    """

    returned_columns = [
        "Protein State",
        "Protein",
        "Start",
        "End",
        "Sequence",
        "Peptide Mass",
        "RT (min)",
        "Deut Time (sec)",
        "maxD",
        "Theor Uptake #D",
        "#D",
        "%D",
        "Conf Interval (#D)",
        "#Rep",
        "Confidence",
        "Stddev",
        "p",
    ]
    filter_columns = ["Protein", "Protein State", "Deut Time (sec)"]
    aggregated = True

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_csv(path)

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return from_hdexaminer_uptake_summary(df)

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        columns = read_columns(path)
        return set(cls.returned_columns).issubset(set(columns))


class OpenHDX(FormatSpec):
    returned_columns = ["start", "end", "sequence"]
    filter_columns = []

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_csv(path)

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return df  # No conversion needed for OpenHDX

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        columns = read_columns(path)
        return set(cls.returned_columns).issubset(set(columns))


class HXMS(FormatSpec):
    returned_columns = ["START", "END", "SEQUENCE", "TIME(Sec)", "REP"]
    filter_columns = ["TIME(Sec)"]

    @classmethod
    def read(cls, path: Path) -> nw.DataFrame:
        return read_hxms(path, returns="DataFrame")

    @classmethod
    def convert(cls, df: nw.DataFrame) -> nw.DataFrame:
        return from_hxms(df)

    @classmethod
    def valid_file(cls, path: Path) -> bool:
        if path.suffix.lower() != ".hxms":
            return False

        with open(path, "r") as fh:
            while line := fh.readline():
                if line.startswith("TITLE_TP"):
                    return True

        return False


def is_aggregated(df: nw.DataFrame) -> bool:
    """Checks if a open-hdx formatted DataFrame is aggregated.

    A DataFrame is considered aggregated if it containns only one replicate or
    replicates are already averaged, ie if there is only one entry per
    unique combination of protein, state, start, end, and exposure.

    """
    identifier_columns = ["protein", "state", "start", "end", "exposure"]
    by = set(identifier_columns) & set(df.columns)
    unique = df.unique(subset=list(by))
    return len(unique) == len(df)


def identify_format(path: Path) -> type[FormatSpec]:
    """Identify format from file path by reading a sample of the data."""

    for fmt in FMT_REGISTRY.values():
        if fmt.valid_file(path):
            return fmt
    raise ValueError(f"Could not identify format for file: {path}")
