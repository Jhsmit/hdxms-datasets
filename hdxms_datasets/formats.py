from typing import Optional, Callable, Protocol, Type
from hdxms_datasets.convert import from_dynamx_cluster, from_dynamx_state, from_hdexaminer
import narwhals as nw


class HDXFormat(Protocol):
    columns: list[str]
    state_name: str
    exposure_name: str

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """
        ...


class DynamX_v3_state:
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
    state_name = "State"
    exposure_name = "Exposure"

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """
        return from_dynamx_state(df)


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

    def convert(self, df: nw.DataFrame) -> nw.DataFrame:
        """
        Convert the DataFrame to a standard format.
        """
        return from_hdexaminer(df)


# Define a registry of known formats
HDX_FORMATS: list[HDXFormat] = [
    DynamX_v3_state(),
    DynamX_v3_cluster(),
    HDExaminer_v3(),
]


def identify_format(cols: list[str], *, exact: bool = True) -> Optional[HDXFormat]:
    """
    Identify which HDXFormat subclass the given column list matches.

    Args:
        cols: The column names to check.
        exact: If True, order must match; otherwise, uses set equality.

    Returns:
        The matching HDXFormat subclass, or None if no match.
    """
    for fmt_class in HDX_FORMATS:
        template = fmt_class.columns
        if exact and cols == template:
            return fmt_class
        elif not exact and set(cols) == set(template):
            return fmt_class
    return None
