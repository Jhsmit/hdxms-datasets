"""
Reader functions for various file formats
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Union, Literal, IO

import pandas as pd


def read_dynamx(
    filepath_or_buffer: Union[Path[str], str, IO],
    time_conversion: Optional[tuple[Literal["h", "min", "s"], Literal["h", "min", "s"]]] = (
        "min",
        "s",
    ),
) -> pd.DataFrame:
    """
    Reads DynamX .csv files and returns the resulting peptide table as a pandas DataFrame.

    Args:
        filepath_or_buffer: File path of the .csv file or :class:`~io.StringIO` object.
        time_conversion: How to convert the time unit of the field 'exposure'. Format is ('<from>', <'to'>).
            Unit options are 'h', 'min' or 's'.

    Returns:
        Peptide table as a pandas DataFrame.
    """

    df = pd.read_csv(filepath_or_buffer)
    df.columns = df.columns.str.replace(" ", "_").str.lower()

    df.insert(df.columns.get_loc("end") + 1, "stop", df["end"] + 1)

    if time_conversion is not None:
        time_lut = {"h": 3600, "min": 60, "s": 1}
        time_factor = time_lut[time_conversion[0]] / time_lut[time_conversion[1]]
        df["exposure"] *= time_factor

    return df
