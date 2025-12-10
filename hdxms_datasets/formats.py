from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass
import narwhals as nw

from hdxms_datasets.convert import (
    from_dynamx_cluster,
    from_dynamx_state,
    from_hdexaminer,
    from_hxms,
)


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


@dataclass(frozen=True)
class FormatSpec:
    """Specification for a data format

    Args:
        name: Name of the format.
        required_columns: List of columns required to identify this format.
        filter_columns: List of columns that can be used to filter data.
        converter: Function to convert a DataFrame to OpenHDX format.
        aggregated: Whether the format is aggregated, or a function to determine if a DataFrame is aggregated.

    """

    name: str
    required_columns: list[str]
    filter_columns: list[str]
    converter: Callable[[nw.DataFrame], nw.DataFrame]
    aggregated: bool | Callable[[nw.DataFrame], bool]

    def matches(self, df: nw.DataFrame) -> bool:
        """Check if a DataFrame matches this format."""
        df_cols = set(df.columns)
        required_cols = set(self.required_columns)
        return required_cols.issubset(df_cols)

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """Convert DataFrame to OpenHDX format."""
        return self.converter(df)

    def is_aggregated(self, df: nw.DataFrame | None = None) -> bool:
        """Check if a DataFrame is aggregated."""
        if self.aggregated is True:
            return True
        if callable(self.aggregated):
            if df is None:
                raise ValueError("DataFrame must be provided to check aggregation")
            return self.aggregated(df)
        return False


def hxms_is_aggregated(df: nw.DataFrame) -> bool:
    """
    The HXMS format both supports data which contains the individual measurements or as aggregated data.
    The "REP" column (experiment number) indicates replicate ID.
    However, some files have a unique "REP" value for all rows, but still contain multiple measurements per
    peptide timepoint, we check for this case here.

    """

    return len(df.unique(["START", "END", "TIME(Sec)"])) == len(df)


# Format registry - order matters for identification
FORMATS = [
    FormatSpec(
        name="DynamX_v3_state",
        required_columns=[
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
        ],
        filter_columns=["Protein", "State", "Exposure"],
        converter=from_dynamx_state,
        aggregated=True,
    ),
    # vx_state columns are subset of DynamX_v3_state; thus we need to make sure to check for
    # DynamX_v3_state first to ensure correct identification
    FormatSpec(
        name="DynamX_vx_state",
        required_columns=[
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
        ],
        filter_columns=["Protein", "State", "Exposure"],
        converter=from_dynamx_state,
        aggregated=True,
    ),
    FormatSpec(
        name="DynamX_v3_cluster",
        required_columns=[
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
        ],
        filter_columns=["Protein", "State", "Exposure"],  # filter by 'Protein' field?
        converter=from_dynamx_cluster,
        aggregated=False,
    ),
    FormatSpec(
        name="HDExaminer_v3",
        required_columns=[
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
        ],
        filter_columns=["Protein State", "Deut Time"],
        converter=from_hdexaminer,
        aggregated=False,
    ),
    FormatSpec(
        name="OpenHDX",
        required_columns=["start", "end", "sequence"],
        filter_columns=[],
        converter=lambda df: df,  # No conversion needed for OpenHDX
        aggregated=lambda df: "replicate" not in df.columns,
    ),
    FormatSpec(
        name="HXMS",
        required_columns=["START", "END", "SEQUENCE", "TIME(Sec)", "REP"],
        filter_columns=["TIME(Sec)"],
        converter=from_hxms,
        aggregated=hxms_is_aggregated,
    ),
]


# Create lookup by name
FORMAT_LUT = {fmt.name: fmt for fmt in FORMATS}


def identify_format_from_path(path: Path) -> Optional[FormatSpec]:
    """Identify format from file path by reading a sample of the data."""

    raise NotImplementedError("Function not yet implemented")


def identify_format_from_df(df: nw.DataFrame) -> Optional[FormatSpec]:
    """Identify format from DataFrame columns"""
    for fmt in FORMATS:
        if fmt.matches(df):
            return fmt
    return None


def identify_format(src: nw.DataFrame | Path) -> Optional[FormatSpec]:
    """Identify format from DataFrame columns"""
    if isinstance(src, Path):
        return identify_format_from_path(src)

    elif isinstance(src, nw.DataFrame):
        return identify_format_from_df(src)
