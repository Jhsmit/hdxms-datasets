"""
Reader functions for various file formats
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Union, Literal
import pandas as pd


def read_dynamx(
    filepath_or_buffer: Union[Path[str], str, StringIO],
    time_conversion: tuple[Literal["h", "min", "s"], Literal["h", "min", "s"]] = ("min", "s")
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

    if isinstance(filepath_or_buffer, StringIO):
        hdr = filepath_or_buffer.readline().strip("# \n\t")
        filepath_or_buffer.seek(0)
    else:
        with open(filepath_or_buffer, "r") as f_obj:
            hdr = f_obj.readline().strip("# \n\t")

    names = [name.lower().strip("\r\t\n") for name in hdr.split(",")]
    df = pd.read_csv(filepath_or_buffer, header=0, names=names)

    df.insert(df.columns.get_loc('end') + 1, 'stop', df['end'] + 1)

    time_lut = {"h": 3600, "min": 60, "s": 1}
    time_factor = time_lut[time_conversion[0]] / time_lut[time_conversion[1]]

    df["exposure"] *= time_factor
    df.columns = df.columns.str.replace(' ', '_')

    return df
