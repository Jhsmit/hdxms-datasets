from __future__ import annotations

from typing import Literal, Optional, Union, TypeVar

import numpy.typing as npt
import pandas as pd

from hdxms_datasets.config import cfg

TIME_FACTORS = {"s": 1, "m": 60.0, "min": 60.0, "h": 3600, "d": 86400}
TEMPERATURE_OFFSETS = {"c": 273.15, "celsius": 273.15, "k": 0.0, "kelvin": 0.0}

A = TypeVar("A", npt.ArrayLike, pd.Series, pd.DataFrame)


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
    df: pd.DataFrame,
    state: Optional[str] = None,
    exposure: Optional[dict] = None,
    query: Optional[list[str]] = None,
    dropna: bool = True,
) -> pd.DataFrame:
    """
    Convenience function to filter a peptides DataFrame. .

    Args:
        df: Input dataframe.
        state: Name of protein state to select.
        exposure: Exposure value(s) to select. Exposure is given as a :obj:`dict`, with keys "value" or "values" for
            exposure value, and "unit" for the time unit.
        query: Additional queries to pass to [pandas.DataFrame.query][].
        dropna: Drop rows with `NaN` uptake entries.

    Examples:
        Filter peptides for a specific protein state and exposure time:

        >>> d = {"state", "SecB WT apo", "exposure": {"value": 0.167, "unit": "min"}
        >>> filtered_df = filter_peptides(df, **d)

    Returns:
        Filtered dataframe.
    """

    if state is not None:
        df = df[df["state"] == state]

    if exposure is not None:
        t_val = convert_time(exposure, target_unit=cfg.time_unit)
        if isinstance(t_val, list):
            df = df[df["exposure"].isin(t_val)]
        else:
            df = df[df["exposure"] == t_val]

    if query:
        for q in query:
            df = df.query(q)

    if dropna:
        df = df.dropna(subset=["uptake"])

    return df.reset_index()
