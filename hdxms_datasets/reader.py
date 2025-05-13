"""
Reader functions for various file formats
"""

from __future__ import annotations

from pathlib import Path
from typing import Union, Literal, IO, Optional

from narwhals.exceptions import InvalidOperationError

from hdxms_datasets.backend import BACKEND
import narwhals as nw

from hdxms_datasets.expr import centroid_mass
from hdxms_datasets.process import ufloat_stats


def read_csv(filepath_or_buffer) -> nw.DataFrame:
    if isinstance(filepath_or_buffer, str):
        return nw.read_csv(filepath_or_buffer, backend=BACKEND)
    elif isinstance(filepath_or_buffer, Path):
        return nw.read_csv(filepath_or_buffer.as_posix(), backend=BACKEND)
    else:
        try:
            import polars as pl

            return nw.from_native(pl.read_csv(filepath_or_buffer))
        except ImportError:
            pass
        try:
            import pandas as pd

            return nw.from_native(pd.read_csv(filepath_or_buffer))
        except ImportError:
            raise ValueError("No suitable backend found for reading file-like objects.")


def read_dynamx(
    filepath_or_buffer: Union[Path, str, IO],
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


def convert_rt(rt_str: str) -> float:
    """convert hd examiner rt string to float
    example: "7.44-7.65" -> 7.545
    """
    lower, upper = rt_str.split("-")
    mean = (float(lower) + float(upper)) / 2.0
    return mean


def cast_exposure(df):
    try:
        df = df.with_columns(nw.col("exposure").str.strip_chars("s").cast(nw.Float64))
    except InvalidOperationError:
        pass
    return df


# move to module 'convert'
def from_hdexaminer(
    hd_examiner_df: nw.DataFrame,
    extra_columns: Optional[list[str] | dict[str, str] | str] = None,
) -> nw.DataFrame:
    column_mapping = {
        "Protein State": "state",
        "Deut Time": "exposure",
        "Start": "start",
        "End": "end",
        "Sequence": "sequence",
        "Experiment": "file",
        "Charge": "charge",
        "Exp Cent": "centroid_mz",
        "Max Inty": "intensity",
    }

    column_order = list(column_mapping.values())
    column_order.insert(column_order.index("charge") + 1, "centroid_mass")
    column_order.append("rt")

    if isinstance(extra_columns, dict):
        cols = extra_columns
    elif isinstance(extra_columns, list):
        cols = {col: col for col in extra_columns}
    elif isinstance(extra_columns, str):
        cols = {extra_columns: extra_columns}
    elif extra_columns is None:
        cols = {}
    else:
        raise ValueError(
            "additional_columns must be a list or dict, not {}".format(type(extra_columns))
        )

    column_mapping.update(cols)
    column_order.extend(cols.values())

    rt_values = [convert_rt(rt_str) for rt_str in hd_examiner_df["Actual RT"]]
    rt_series = nw.new_series(values=rt_values, name="rt", backend=BACKEND)

    df = (
        hd_examiner_df.rename(column_mapping)
        .with_columns([centroid_mass, rt_series])
        .select(column_order)
        .sort(by=["state", "exposure", "start", "end", "file"])
    )

    return cast_exposure(df)


def from_dynamx_cluster(dynamx_df: nw.DataFrame) -> nw.DataFrame:
    column_mapping = {
        "State": "state",
        "Exposure": "exposure",
        "Start": "start",
        "End": "end",
        "Sequence": "sequence",
        "File": "file",
        "z": "charge",
        "Center": "centroid_mz",
        "Inten": "intensity",
        "RT": "rt",
    }

    column_order = list(column_mapping.values())
    column_order.insert(column_order.index("charge") + 1, "centroid_mass")

    df = (
        dynamx_df.rename(column_mapping)
        .with_columns([centroid_mass, nw.col("exposure") * 60.0])
        .select(column_order)
        .sort(by=["state", "exposure", "start", "end", "file"])
    )

    return df


def from_dynamx_state(dynamx_df: nw.DataFrame) -> nw.DataFrame:
    column_mapping = {
        "State": "state",
        "Exposure": "exposure",
        "Start": "start",
        "End": "end",
        "Sequence": "sequence",
        "Uptake": "uptake",
        "Uptake SD": "uptake_sd",
        # "File": "file",
        # "z": "charge",
        "Center": "centroid_mz",
        "RT": "rt",
        "RT SD": "rt_sd",
    }

    column_order = list(column_mapping.values())

    df = (
        dynamx_df.rename(column_mapping)
        .with_columns([nw.col("exposure") * 60.0])
        .select(column_order)
        .sort(by=["state", "exposure", "start", "end"])
    )

    return df
