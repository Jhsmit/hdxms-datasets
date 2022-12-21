from __future__ import annotations

import pandas as pd
import numpy.typing as npt
from hdxms_datasets.config import cfg

from typing import Literal, Optional, Union, TypeVar


time_factors = {"s": 1, "m": 60.0, "min": 60.0, "h": 3600, "d": 86400}
temperature_offsets = {"c": 273.15, "celsius": 273.15, "k": 0.0, "kelvin": 0.0}

A = TypeVar("A", npt.ArrayLike, pd.Series, pd.DataFrame)


def convert_time(
    values: A, src_unit: Literal["h", "min", "s"], target_unit: Literal["h", "min", "s"]
) -> A:

    time_lut = {"h": 3600.0, "min": 60.0, "s": 1.0}
    time_factor = time_lut[src_unit] / time_lut[target_unit]

    if isinstance(values, list):
        return [v * time_factor for v in values]
    else:
        return values * time_factor


def filter_peptides(
    df: pd.DataFrame,
    state: Optional[str] = None,
    exposure: Union[dict, float, None] = None,
    query: Optional[list[str]] = None,
    dropna: bool = True,
) -> pd.DataFrame:
    """
    Convenience function to filter a peptides DataFrame.

    Args:
        df: Input :class:`pandas.DataFrame`
        state: Name of protein state to select.
        exposure: Exposure value(s) to select. Exposure is given as a :obj:`dict`, with keys "value" or "values" for
            exposure value, and "unit" for the time unit.
        query: Additional queries to pass to :meth:`pandas.DataFrame.query`.
        dropna: Drop rows with NaN uptake entries.

    Example:
        ::

        d = {"state", "SecB WT apo", "exposure": {"value": 0.167, "unit": "min"}
        filtered_df = filter_peptides(df, **d)

    Returns:

    """

    if state:
        df = df[df["state"] == state]

    if isinstance(exposure, dict):
        if values := exposure.get("values"):
            values = convert_time(values, exposure.get("unit", "s"), cfg.time_unit)
            df = df[df["exposure"].isin(values)]
        elif value := exposure.get("value"):
            value = convert_time(value, exposure.get("unit", "s"), cfg.time_unit)
            df = df[df["exposure"] == value]
    elif isinstance(exposure, float):
        df = df[df["exposure"] == exposure]

    if query:
        for q in query:
            df = df.query(q)

    if dropna:
        df = df.dropna(subset=["uptake"])

    return df
