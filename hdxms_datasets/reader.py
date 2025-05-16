"""
Reader functions for various file formats
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, IO, Optional

from narwhals.exceptions import InvalidOperationError

from hdxms_datasets.backend import BACKEND
import narwhals as nw


def read_csv(source: Path | str | IO | bytes) -> nw.DataFrame:
    if isinstance(source, str):
        return nw.read_csv(source, backend=BACKEND)
    elif isinstance(source, Path):
        return nw.read_csv(source.as_posix(), backend=BACKEND)
    elif isinstance(source, bytes):
        import polars as pl

        return nw.from_native(pl.read_csv(source))
    else:
        try:
            import polars as pl

            return nw.from_native(pl.read_csv(source))
        except ImportError:
            pass
        try:
            import pandas as pd

            return nw.from_native(pd.read_csv(source))
        except ImportError:
            raise ValueError("No suitable backend found for reading file-like objects or bytes.")


def read_dynamx(
    filepath_or_buffer: Path | str | IO | bytes,
    time_conversion: Optional[tuple[Literal["h", "min", "s"], Literal["h", "min", "s"]]] = (
        "min",
        "s",
    ),
) -> nw.DataFrame:
    """
    Reads DynamX .csv files and returns the resulting peptide table as a narwhals DataFrame.

    Args:
        filepath_or_buffer: File path of the .csv file or :class:`~io.StringIO` object.
        time_conversion: How to convert the time unit of the field 'exposure'. Format is ('<from>', <'to'>).
            Unit options are 'h', 'min' or 's'.

    Returns:
        Peptide table as a narwhals DataFrame.
    """

    df = read_csv(filepath_or_buffer)
    df = df.rename({col: col.replace(" ", "_").lower() for col in df.columns})

    # insert 'stop' column (which is end + 1)
    columns = df.columns
    columns.insert(columns.index("end") + 1, "stop")
    df = df.with_columns((nw.col("end") + 1).alias("stop")).select(columns)

    if time_conversion is not None:
        time_lut = {"h": 3600, "min": 60, "s": 1}
        time_factor = time_lut[time_conversion[0]] / time_lut[time_conversion[1]]
        df = df.with_columns((nw.col("exposure") * time_factor))

    return df


def cast_exposure(df):
    try:
        df = df.with_columns(nw.col("exposure").str.strip_chars("s").cast(nw.Float64))
    except InvalidOperationError:
        pass
    return df


# move to module 'convert'
