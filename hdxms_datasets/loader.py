from __future__ import annotations

from pathlib import Path
from typing import Literal, IO, Optional
import warnings

from narwhals.exceptions import InvalidOperationError

import narwhals as nw

import narwhals as nw
from pathlib import Path
from hdxms_datasets.formats import FORMAT_LUT
from hdxms_datasets.models import Peptides


def get_backend():
    """
    Returns the backend used for data handling.
    """
    try:
        import polars  # NOQA: F401 # type: ignore[import]

        return "polars"
    except ImportError:
        pass

    try:
        import pandas  # NOQA: F401 # type: ignore[import]

        return "pandas"
    except ImportError:
        pass

    try:
        import modin  # NOQA: F401 # type: ignore[import]

        return "modin"
    except ImportError:
        pass

    try:
        import pyarrow  # NOQA: F401 # type: ignore[import]

        return "pyarrow"
    except ImportError:
        pass

    raise ImportError("No suitable backend found. Please install pandas, polars, pyarrow or modin.")


BACKEND = get_backend()


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

            return nw.from_native(pd.read_csv(source))  # type: ignore
        except ImportError:
            raise ValueError("No suitable backend found for reading file-like objects or bytes.")


def load_peptides(
    peptides: Peptides,
    base_dir: Path = Path.cwd(),
    convert: bool = True,
    aggregate: bool | None = None,
    sort_rows: bool = True,
    sort_columns: bool = True,
    drop_null: bool = True,
) -> nw.DataFrame:
    # Resolve the data file path
    if peptides.data_file.is_absolute():
        data_path = peptides.data_file
    else:
        data_path = base_dir / peptides.data_file

    # Load the raw data
    df = read_csv(data_path)

    from hdxms_datasets import process

    df = process.apply_filters(df, **peptides.filters)

    format_spec = FORMAT_LUT.get(peptides.data_format)
    assert format_spec is not None, f"Unknown format: {peptides.data_format}"

    if callable(format_spec.aggregated):
        is_aggregated = format_spec.aggregated(df)
    else:
        is_aggregated = format_spec.aggregated

    # if aggregation is not specified, by default aggregate if the data is not already aggregated
    if aggregate is None:
        aggregate = not is_aggregated

    if aggregate and is_aggregated:
        warnings.warn("Data format is pre-aggregated. Aggregation will be skipped.")
        aggregate = False

    if not convert and aggregate:
        warnings.warn("Cannot aggregate data without conversion. Aggeregation will be skipped.")
        aggregate = False

    if not convert and sort_rows:
        warnings.warn("Cannot sort rows without conversion. Sorting will be skipped.")
        sort_rows = False

    if not convert and sort_columns:
        warnings.warn("Cannot sort columns without conversion. Sorting will be skipped.")
        sort_columns = False

    if convert:
        df = format_spec.convert(df)

    if aggregate:
        df = process.aggregate(df)

    if drop_null:
        df = process.drop_null_columns(df)

    if sort_rows:
        df = process.sort_rows(df)

    if sort_columns:
        df = process.sort_columns(df)

    return df
