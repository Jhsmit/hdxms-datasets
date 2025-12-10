"""
Module for loading various HDX-MS formats.
"""

from __future__ import annotations

from io import StringIO
import warnings
from pathlib import Path
from typing import IO, Literal, NotRequired, TypedDict, overload
from collections.abc import Iterable, Iterator

import narwhals as nw

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
HXMS_SCHEMA = {
    "INDEX": nw.Int32(),
    "MOD": nw.String(),
    "START": nw.Int64(),
    "END": nw.Int64(),
    "REP": nw.Int64(),
    "PTM_ID": nw.Int64(),
    "TIME(Sec)": nw.Float64(),
    "UPTAKE": nw.Float64(),
    "ENVELOPE": nw.List(nw.Float64()),
}


# schema for hdx examiner peptide pool initial 8 columns
HDEXAMINER_PEPTIDE_POOL_INITIAL_SCHEMA = nw.Schema(
    {
        "State": nw.String(),
        "Protein": nw.String(),
        "Start": nw.Int64(),
        "End": nw.Int64(),
        "Sequence": nw.String(),
        "Search RT": nw.Float64(),
        "Charge": nw.Int64(),
        "Max D": nw.Int64(),
    }
)

# schema for hdx examiner peptide pool repeated columns
HDEXAMINER_PEPTIDE_POOL_REPEATED_SCHEMA = nw.Schema(
    {
        "Start RT": nw.Float64(),
        "End RT": nw.Float64(),
        "#D": nw.Float64(),
        "%D": nw.Float64(),
        "#D right": nw.String(),
        "%D right": nw.String(),
        "Score": nw.Float64(),
        "Conf": nw.String(),
    }
)


def deduplicate_name(name: str):
    """Deduplicate column name by removing trailing '_duplicated_xx"""
    import re

    return re.sub(r"_duplicated_\d+$", "", name)


def read_hdexaminer_peptide_pool(source: Path | StringIO) -> nw.DataFrame:
    """
    Read an HDX-Examiner peptide pool file and return a Narwhals DataFrame.

    Args:
        source: Source object representing the HDX-Examiner peptide pool data.

    """

    # read the data
    if isinstance(source, StringIO):
        try:
            import polars as pl

            df = nw.from_native(pl.read_csv(source, skip_rows=1, has_header=True))
        except ImportError:
            import pandas as pd

            df = nw.from_native(pd.read_csv(source, skiprows=[0]))

    else:
        df = nw.read_csv(source.as_posix(), backend=BACKEND, skip_rows=1, has_header=True)

    # read the header
    if isinstance(source, StringIO):
        source.seek(0)
        exposure_line = source.readline()
        header_line = source.readline()
    else:
        with open(source, "r") as fh:
            exposure_line = fh.readline()
            header_line = fh.readline()

    exposure_columns = exposure_line.strip().split(",")
    header_columns = header_line.strip().split(",")

    found_schema = df[:, 0:8].schema
    if found_schema != HDEXAMINER_PEPTIDE_POOL_INITIAL_SCHEMA:
        raise ValueError("HDX-Examiner peptide pool file has an unexpected columns schema.")

    # find indices of exposure markers in header
    has_entry_with_end = [i for i, col in enumerate(exposure_columns) if col] + [
        len(exposure_columns)
    ]

    output_dfs = []
    dtype_lut = dict(HDEXAMINER_PEPTIDE_POOL_REPEATED_SCHEMA.items())

    # to be repeated row-wise initial 8 columns
    initial_df = df[:, :8]

    for i, j in zip(has_entry_with_end[1:-1], has_entry_with_end[2:]):
        exposure = exposure_columns[i]

        sub_frame = df[:, i:j]

        expected_columns = header_columns[i:j]

        drop_cols = set(expected_columns) - set(HDEXAMINER_PEPTIDE_POOL_REPEATED_SCHEMA.names())
        # rename duplicated columns, drop non-accepted columns, cast to correct dtype, add exposure column
        sub_frame = (
            sub_frame.rename({col: name for col, name in zip(sub_frame.columns, expected_columns)})
            .drop(drop_cols)
            .with_columns(
                [
                    nw.col(name).cast(dtype_lut[name])
                    for name in expected_columns
                    if name not in drop_cols
                ]
                + [nw.lit(str(exposure)).alias("Exposure")]
            )
        )

        combined_i = nw.concat([initial_df, sub_frame], how="horizontal")
        output_dfs.append(combined_i)

    final_output = nw.concat(output_dfs, how="diagonal")

    return final_output


def read_csv(source: Path | IO | bytes, **kwargs) -> nw.DataFrame:
    """
    Read a CSV file and return a Narwhals DataFrame.

    Args:
        source: Source object representing the CSV data.

    Returns:
        A Narwhals DataFrame containing the CSV data.

    """

    if isinstance(source, Path):
        return nw.read_csv(source.as_posix(), backend=BACKEND, **kwargs)
    elif isinstance(source, bytes):
        import polars as pl

        return nw.from_native(pl.read_csv(source), **kwargs)
    elif isinstance(source, IO):
        try:
            import polars as pl

            return nw.from_native(pl.read_csv(source), **kwargs)
        except ImportError:
            pass
        try:
            import pandas as pd

            return nw.from_native(pd.read_csv(source), **kwargs)  # type: ignore
        except ImportError:
            raise ValueError("No suitable backend found for reading file-like objects")
    else:
        raise TypeError("source must be a Path, bytes, or file-like object")


def hxms_line_generator(source: Path) -> Iterator[str]:
    """
    Generate lines from an HXMS file.
    """
    with source.open("r", encoding="utf-8") as fh:
        for line in fh:
            yield line.rstrip("\r\n")


def _hxms_splitlines(source: Path | IO | bytes) -> list[str]:
    """
    Split the HXMS source into lines.
    Args:
        source: Source object representing the HXMS data.
    Returns:
        A list of lines from the HXMS data.
    """

    if isinstance(source, Path):
        content = source.read_text()
    elif isinstance(source, bytes):
        content = source.decode("utf-8")
    elif isinstance(source, (bytearray, memoryview)):
        content = bytes(source).decode("utf-8")
    elif hasattr(source, "read") and callable(getattr(source, "read")):
        raw = source.read()
        if isinstance(raw, bytes):
            content = raw.decode("utf-8")
        elif isinstance(raw, str):
            content = raw
        else:
            raise TypeError("file-like object's read() must return str or bytes")

    else:
        raise TypeError("source must be a Path, str, bytes, or file-like object")

    return content.splitlines()


def _line_content(line: str) -> list[str]:
    """
    Extract content from a line by removing the prefix.
    Args:
        line: A line from the HXMS file.
    Returns:
        A list of content items from the line.
    """

    name, *raw_content = line.strip().split(" ")
    content = [item for item in raw_content if item]
    return content


def _parse_hxms_TP_lines(lines: Iterable[str], sequence: str) -> nw.DataFrame:
    """
    Parse the TITLE_TP section of an HXMS file and return a Narwhals DataFrame.

    Args:
        lines: An iterable of lines from the HXMS file.
        sequence: The protein sequence for peptide extraction.
            Assumed to be 1-indexed in START; END is inclusive interval, ie sequence[START-1:END]


    Returns:
        A Narwhals DataFrame containing the HXMS data.
    """

    # parse the rest of the data into list of dicts
    # we first need to check how many data rows there are
    # since the "EVELOPE" field might be unpopulated
    dicts = []
    line_gen = iter(lines)
    first_row = next(line_gen)
    content = _line_content(first_row)

    used_columns = list(HXMS_SCHEMA)[: len(content)]
    data_dict = dict(zip(used_columns, content))
    data_dict["sequence"] = sequence[int(data_dict["START"]) - 1 : int(data_dict["END"])]
    dicts.append(data_dict)

    # continue parsing data rows
    for line in line_gen:
        if not line.startswith("TP"):
            continue
        content = _line_content(line)
        data_dict = dict(zip(used_columns, content))
        data_dict["sequence"] = sequence[int(data_dict["START"]) - 1 : int(data_dict["END"])]

        dicts.append(data_dict)

    schema = nw.Schema({col: HXMS_SCHEMA[col] for col in used_columns} | {"sequence": nw.String()})
    df = nw.from_dicts(dicts, schema=schema, backend=BACKEND)

    return df


class HXMSResult(TypedDict):
    HEADER: list[str]
    METADATA: dict[str, str]
    REMARK: dict[str, str]
    DATA: NotRequired[nw.DataFrame]


def parse_hxms_lines(lines: Iterable[str], read_content: bool = True) -> HXMSResult:
    """Parse the different sections of an HXMS file.

    Returns a dictionary with keys:
        - "HEADER": list of header lines
        - "METADATA": dict of metadata key-value pairs
        - "REMARK": dict of remark key-value pairs
        - "DATA": Narwhals DataFrame containing the HXMS data (if read_content is True)

    Args:
        lines: An iterable of lines from the HXMS file.

    Returns:
        A dictionary containing the parsed information.

    """
    result: HXMSResult = {
        "HEADER": [],
        "METADATA": {},
        "REMARK": {},
    }
    columns = []
    line_iter = iter(lines)
    for line in line_iter:
        if line.startswith("HEADER"):
            content = line.lstrip("HEADER").strip()
            result["HEADER"].append(content)
        elif line.startswith("METADATA"):
            name, *raw_content = line.strip().split(" ")
            content = [item for item in raw_content if item]
            if len(content) == 2:
                key, value = content
                result["METADATA"][key] = value
        elif line.startswith("REMARK"):
            name, *raw_content = line.strip().split(" ")
            content = [item for item in raw_content if item]
            if len(content) == 2:
                key, value = content
                result["REMARK"][key] = value
        elif line.startswith("TITLE_TP") and not read_content:
            return result
        elif line.startswith("TITLE_TP") and read_content:
            columns = _line_content(line)
            break

    # the rest of the lines are data lines
    df = _parse_hxms_TP_lines(line_iter, sequence=result["METADATA"]["PROTEIN_SEQUENCE"])
    result["DATA"] = df

    # check read columns against expected columns
    if columns:
        expected_columns = list(HXMS_SCHEMA)[: len(columns)]
        if columns != expected_columns:
            warnings.warn(
                f"Columns in HXMS file do not match expected columns. "
                f"Found: {columns}, Expected: {expected_columns}"
            )

    return result


@overload
def read_hxms(source: Path | IO | bytes, returns: Literal["HXMSResult"]) -> HXMSResult: ...


@overload
def read_hxms(source: Path | IO | bytes, returns: Literal["DataFrame"]) -> nw.DataFrame: ...


def read_hxms(
    source: Path | IO | bytes, returns: Literal["HXMSResult", "DataFrame"] = "HXMSResult"
) -> HXMSResult | nw.DataFrame:
    """
    Read an HXMS file and return a HXMSResult or Narwhals DataFrame.

    Args:
        source: Source object representing the HXMS data.

    Returns:
        A Narwhals DataFrame containing the HXMS data.
    """

    lines = _hxms_splitlines(source)
    # TODO make generator based on input type
    line_gen = iter(lines)

    # first get column names
    result = parse_hxms_lines(line_gen, read_content=True)

    if returns == "HXMSResult":
        return result
    elif returns == "DataFrame":
        assert "DATA" in result, "No data found in HXMS file"
        return result["DATA"]
    else:
        raise ValueError(f"Unsupported returns value: {returns!r}")


def read_peptide_data(data_file: Path) -> nw.DataFrame:
    """
    Read peptide data from the specified file and return a Narwhals DataFrame.

    Args:
        data_file: Path to the data file.

    Returns:
        A Narwhals DataFrame containing the loaded data.

    """

    # TODO identify format and then load

    if data_file.suffix.lower() == ".csv":
        df = read_csv(data_file)
    elif data_file.suffix.lower() == ".hxms":
        result = read_hxms(data_file)
        assert "DATA" in result, "No data found in HXMS file"
        df = result["DATA"]
    else:
        raise ValueError(f"Unsupported file format: {data_file.suffix}")

    return df


def load_peptides(
    peptides: Peptides,
    base_dir: Path = Path.cwd(),
    convert: bool = True,
    aggregate: bool | None = None,
    sort_rows: bool = True,
    sort_columns: bool = True,
    drop_null: bool = True,
) -> nw.DataFrame:
    """
    Load peptides from the data file and return a Narwhals DataFrame.

    Args:
        peptides: Peptides object containing metadata and file path.
        base_dir: Base directory to resolve relative file paths. Defaults to the current working directory.
        convert: Whether to convert the data to a standard format.
        aggregate: Whether to aggregate the data. If None, will aggregate if the data is not already aggregated.
        sort_rows: Whether to sort the rows.
        sort_columns: Whether to sort the columns in a standard order.
        drop_null: Whether to drop columns that are entirely null.

    Returns:
        A Narwhals DataFrame containing the loaded peptide data.

    """

    # Resolve the data file path
    if peptides.data_file.is_absolute():
        data_path = peptides.data_file
    else:
        data_path = base_dir / peptides.data_file

    # Load the raw data
    # TODO via fmt.read( .. )
    df = read_peptide_data(data_path)

    from hdxms_datasets import process

    df = process.apply_filters(df, **peptides.filters)

    from hdxms_datasets.formats import FORMAT_LUT

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
