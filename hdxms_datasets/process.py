from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union, TYPE_CHECKING

import narwhals as nw


if TYPE_CHECKING:
    from hdxms_datasets import DataFile


TIME_FACTORS = {"s": 1, "m": 60.0, "min": 60.0, "h": 3600, "d": 86400}
TEMPERATURE_OFFSETS = {"c": 273.15, "celsius": 273.15, "k": 0.0, "kelvin": 0.0}


# overload typing to get correct return type
def convert_temperature(
    temperature_dict: dict, target_unit: str = "c"
) -> Union[float, list[float]]:
    """
    Convenience function to convert temperature values.

    Args:
        temperature_dict: Dictionary with temperature value(s) and unit.
        target_unit: Target unit for temperature. Must be "c", "k", "celsius", or "kelvin" and is
            case-insensitive.

    Returns:
        Converted temperature value(s).
    """

    src_unit = temperature_dict["unit"].lower()
    temp_offset = TEMPERATURE_OFFSETS[src_unit] - TEMPERATURE_OFFSETS[target_unit.lower()]
    if values := temperature_dict.get("values"):
        return [v + temp_offset for v in values]
    elif value := temperature_dict.get("value"):
        return value + temp_offset
    else:
        raise ValueError("Invalid temperature dictionary")


def convert_time(
    time_dict: dict, target_unit: Literal["s", "min", "h"] = "s"
) -> Union[float, list[float]]:
    """
    Convenience function to convert time values.

    Args:
        time_dict: Dictionary with time value(s) and unit.
        target_unit: Target unit for time.

    Returns:
        Converted time value(s).
    """

    src_unit = time_dict["unit"]

    time_factor = TIME_FACTORS[src_unit] / TIME_FACTORS[target_unit]
    if values := time_dict.get("values"):
        return [v * time_factor for v in values]
    elif value := time_dict.get("value"):
        return value * time_factor
    else:
        raise ValueError("Invalid time dictionary")


def filter_peptides(
    df: nw.DataFrame,
    state: Optional[str] = None,
    exposure: Optional[dict] = None,
    dropna: bool = True,
    time_unit: Literal["s", "min", "h"] = "s",
) -> nw.DataFrame:
    """
    Convenience function to filter a peptides DataFrame. .

    Args:
        df: Input dataframe.
        state: Name of protein state to select.
        exposure: Exposure value(s) to select. Exposure is given as a :obj:`dict`, with keys "value" or "values" for
            exposure value, and "unit" for the time unit.
        query: Additional queries to pass to [pandas.DataFrame.query][].
        dropna: Drop rows with `NaN` or `null` uptake entries.
        time_unit: Time unit for exposure column of supplied dataframe.

    Examples:
        Filter peptides for a specific protein state and exposure time:

        >>> d = {"state", "SecB WT apo", "exposure": {"value": 0.167, "unit": "min"}
        >>> filtered_df = filter_peptides(df, **d)

    Returns:
        Filtered dataframe.
    """

    if state is not None:
        df = df.filter(nw.col("state") == state)

    if exposure is not None:
        t_val = convert_time(exposure, time_unit)
        if isinstance(t_val, list):
            df = df.filter(nw.col("exposure").is_in(t_val))
        else:
            df = df.filter(nw.col("exposure") == t_val)

    if dropna:
        df = df.drop_nulls("uptake").filter(~nw.col("uptake").is_nan())

    return df


def parse_data_files(data_file_spec: dict, data_dir: Path) -> dict[str, DataFile]:
    """
    Parse data file specifications from a YAML file.

    Args:
        data_file_spec: Dictionary with data file specifications.
        data_dir: Path to data directory.

    Returns:
        Dictionary with parsed data file specifications.
    """

    from hdxms_datasets import DataFile

    data_files = {}
    for name, spec in data_file_spec.items():
        datafile = DataFile(
            name=name,
            filepath_or_buffer=Path(data_dir / spec["filename"]),
            **{k: v for k, v in spec.items() if k != "filename"},
        )
        data_files[name] = datafile

    return data_files
