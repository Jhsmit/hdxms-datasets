"""
Module for loading various HDX-MS formats.
"""

from __future__ import annotations

from collections import defaultdict
from io import StringIO
import itertools
import warnings
from pathlib import Path
from typing import IO, Any, Literal, NotRequired, TypedDict, overload
from collections.abc import Iterable, Iterator

import narwhals as nw


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

    raise ImportError(
        "No suitable backend found. Please install pandas, polars, pyarrow or modin."
    )


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

    # read the data and header
    if isinstance(source, StringIO):
        try:
            import polars as pl

            df = nw.from_native(pl.read_csv(source, skip_rows=1, has_header=True))
        except ImportError:
            import pandas as pd

            df = nw.from_native(pd.read_csv(source, skiprows=[0]))

        source.seek(0)
        exposure_line = source.readline()
        header_line = source.readline()

    else:
        kwargs = {
            "polars": {"skip_rows": 1, "has_header": True},
            "pandas": {"skiprows": [0]},
        }
        if BACKEND not in kwargs:
            raise ValueError(f"Unsupported backend: {BACKEND}")
        df = nw.read_csv(source.as_posix(), backend=BACKEND, **kwargs[BACKEND])
        with open(source, "r") as fh:
            exposure_line = fh.readline()
            header_line = fh.readline()

    exposure_columns = exposure_line.strip().split(",")
    header_columns = header_line.strip().split(",")

    found_schema = df[:, 0:8].schema
    if found_schema != HDEXAMINER_PEPTIDE_POOL_INITIAL_SCHEMA:
        raise ValueError(
            "HDX-Examiner peptide pool file has an unexpected columns schema."
        )

    # find indices of exposure markers in header
    has_entry_with_end = [i for i, col in enumerate(exposure_columns) if col] + [
        len(exposure_columns)
    ]

    num_blocks = len(has_entry_with_end) - 1
    initial_df = nw.concat([df[:, :8]] * num_blocks, how="vertical")

    has_entry_with_end = [i for i, col in enumerate(exposure_columns) if col] + [
        len(exposure_columns)
    ]

    output = defaultdict(list)
    for i, j in zip(has_entry_with_end[:-1], has_entry_with_end[1:]):
        exposure = exposure_columns[i]
        found_columns = header_columns[i:j]

        # iterate over the expected columns, extract the series and append to output
        # for missing columns, create a series of nulls
        for col, dtype in HDEXAMINER_PEPTIDE_POOL_REPEATED_SCHEMA.items():
            if col in found_columns:
                column_index = found_columns.index(col) + i
                frame = df[:, column_index].cast(dtype).alias(col).to_frame()
            else:
                c = itertools.repeat(None, len(df))
                frame = nw.Series.from_iterable(
                    name=col, values=c, dtype=dtype, backend=BACKEND
                ).to_frame()

            output[col].append(frame)

        c = itertools.repeat(exposure, len(df))
        frame = nw.Series.from_iterable(
            name="Exposure", values=c, dtype=dtype, backend=BACKEND
        ).to_frame()
        output["Exposure"].append(frame)

    # combine all 1-column frames first vertically and then horizontally with initial_df
    concatenated = {k: nw.concat(v, how="vertical") for k, v in output.items()}
    final_output = nw.concat([initial_df, *concatenated.values()], how="horizontal")

    return final_output


def read_csv(source: Path | StringIO | bytes, **kwargs) -> nw.DataFrame:
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
    elif isinstance(source, StringIO):
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
        raise TypeError(
            f"Source must be a Path, bytes, or file-like object, got: {type(source)}"
        )


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


def _cast_envelope(data_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Cast the ENVELOPE field in the data dictionary to a list of floats.

    Args:
        data_dict: A dictionary containing HXMS data.
    Returns:
        The updated dictionary with the ENVELOPE field cast to a list of floats.
    """
    if "ENVELOPE" in data_dict:
        envelope_str = data_dict["ENVELOPE"]
        if envelope_str:
            data_dict["ENVELOPE"] = [float(val) for val in envelope_str.split(",")]
        else:
            data_dict["ENVELOPE"] = []
    return data_dict


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
    data_dict: dict[str, Any] = dict(zip(used_columns, content))
    data_dict["sequence"] = sequence[
        int(data_dict["START"]) - 1 : int(data_dict["END"])
    ]
    data_dict = _cast_envelope(data_dict)
    dicts.append(data_dict)

    # continue parsing data rows
    for line in line_gen:
        if not line.startswith("TP"):
            continue
        content = _line_content(line)
        data_dict = dict(zip(used_columns, content))
        data_dict["sequence"] = sequence[
            int(data_dict["START"]) - 1 : int(data_dict["END"])
        ]
        data_dict = _cast_envelope(data_dict)
        dicts.append(data_dict)

    schema = nw.Schema(
        {col: HXMS_SCHEMA[col] for col in used_columns} | {"sequence": nw.String()}
    )
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
    df = _parse_hxms_TP_lines(
        line_iter, sequence=result["METADATA"]["PROTEIN_SEQUENCE"]
    )
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
def read_hxms(
    source: Path | IO | bytes, returns: Literal["HXMSResult"]
) -> HXMSResult: ...


@overload
def read_hxms(
    source: Path | IO | bytes, returns: Literal["DataFrame"]
) -> nw.DataFrame: ...


def read_hxms(
    source: Path | IO | bytes,
    returns: Literal["HXMSResult", "DataFrame"] = "HXMSResult",
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
