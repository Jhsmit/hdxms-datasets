from dataclasses import dataclass
from typing import Optional, Protocol
from hdxms_datasets.convert import from_dynamx_cluster, from_dynamx_state, from_hdexaminer
import narwhals as nw


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


class HDXFormat(Protocol):
    columns: list[str]
    state_name: str
    exposure_name: str
    # aggregated: bool = False  # whether the data is aggregated or expanded as multiple replicates

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """
        ...

    @property
    def aggregated(self) -> bool: ...


@dataclass
class OpenHDXFormat:
    """A format where columns names are standardized to a common set.

    Hence OpenHDXFormat.convert() is a no-op.

    """

    columns = STANDARD_COLUMNS + OPTIONAL_COLUMNS
    state_name = "state"
    exposure_name = "exposure"
    aggregated: bool  #  = True  # whether the data is aggregated or expanded as multiple replicates

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """

        return df


class DynamX_vx_state:
    """There are also DynamX state data files which do not have 'Modification' and 'Fragment' columns.
    not sure which version this is.
    """

    columns = [
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

    state_name = "State"
    exposure_name = "Exposure"
    aggregated = True

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """
        return from_dynamx_state(df)


class DynamX_v3_state(DynamX_vx_state):
    columns = [
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


class DynamX_v3_cluster:
    columns = [
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
    state_name = "State"
    exposure_name = "Exposure"
    aggregated = False

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """
        return from_dynamx_cluster(df)


class HDExaminer_v3:
    columns = [
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
    state_name = "Protein State"
    exposure_name = "Deut Time"
    aggregated = False

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """
        return from_hdexaminer(df)


# Define a registry of known formats
HDX_FORMATS: list[HDXFormat] = [
    DynamX_vx_state(),
    DynamX_v3_state(),
    DynamX_v3_cluster(),
    HDExaminer_v3(),
    # OpenHDXFormat(),
]

# lookup table to get instance from name
FMT_LUT = {fmt.__class__.__name__: fmt for fmt in HDX_FORMATS}


def identify_format(df: nw.DataFrame, *, exact: bool = True) -> Optional[HDXFormat]:
    """
    Identify which HDXFormat subclass the given column list matches. If there is no match,
    return an OpenHDXFormat instance with aggregated set to True if 'replicate' is in the columns.

    Args:
        cols: The column names to check.
        exact: If True, order must match; otherwise, uses set equality.

    Returns:
        The matching HDXFormat subclass, or None if no match.
    """
    cols = df.columns
    for fmt in HDX_FORMATS:
        template = fmt.columns
        if exact and cols == template:
            return fmt
        elif not exact and set(cols) == set(template):
            return fmt

    # it there is no match, we try to return the OpenHDXFormat
    aggregated = "replicate" not in cols
    fmt = OpenHDXFormat(aggregated=aggregated)

    return fmt
