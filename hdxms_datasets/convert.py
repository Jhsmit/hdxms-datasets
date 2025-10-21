from hdxms_datasets.expr import centroid_mass


import narwhals as nw
from narwhals.exceptions import InvalidOperationError


def from_dynamx_cluster(dynamx_df: nw.DataFrame) -> nw.DataFrame:
    """
    Convert a DynamX cluster DataFrame to OpenHDX format.
    """
    column_mapping = {
        "State": "state",
        "Exposure": "exposure",
        "Start": "start",
        "End": "end",
        "Sequence": "sequence",
        "File": "replicate",
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
        .sort(by=["state", "exposure", "start", "end", "replicate"])
    )

    return df


def from_dynamx_state(dynamx_df: nw.DataFrame) -> nw.DataFrame:
    """
    Convert a DynamX state DataFrame to OpenHDX format.
    """
    column_mapping = {
        "State": "state",
        "Exposure": "exposure",
        "Start": "start",
        "End": "end",
        "Sequence": "sequence",
        "Uptake": "uptake",
        "Uptake SD": "uptake_sd",
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


def convert_rt(rt_str: str) -> float:
    """Convert HDExaminer retention time string to float
    example: "7.44-7.65" -> 7.545

    !!! warning "Lossy conversion"
        This conversion loses information. The full range is not preserved. This was done such that
        retention time can be stored as float and thus be aggregated.
        Future versions may store the full range with additional `rt_min` and `rt_max` columns.

    """
    vmin, vmax = rt_str.split("-")
    mean = (float(vmin) + float(vmax)) / 2.0
    return mean


def cast_exposure(df):
    try:
        df = df.with_columns(nw.col("exposure").str.strip_chars("s").cast(nw.Float64))
    except InvalidOperationError:
        pass
    return df


def _fmt_extra_columns(columns: list[str] | dict[str, str] | str | None) -> dict[str, str]:
    if isinstance(columns, dict):
        return columns
    elif isinstance(columns, list):
        return {col: col for col in columns}
    elif isinstance(columns, str):
        return {columns: columns}
    elif columns is None:
        return {}
    else:
        raise ValueError("additional_columns must be a list or dict, not {}".format(type(columns)))


def from_hdexaminer(
    hd_examiner_df: nw.DataFrame,
    extra_columns: list[str] | dict[str, str] | str | None = None,
) -> nw.DataFrame:
    """
    Convert an HDExaminer DataFrame to OpenHDX format.

    Args:
        hd_examiner_df: DataFrame in HDExaminer format.
        extra_columns: Additional columns to include, either as a list/str of column name(s)
                       or a dictionary mapping original column names to new names.

    Returns:
        A DataFrame in OpenHDX format.

    """
    from hdxms_datasets.loader import BACKEND

    column_mapping = {
        "Protein State": "state",
        "Deut Time": "exposure",
        "Start": "start",
        "End": "end",
        "Sequence": "sequence",
        "Experiment": "replicate",
        "Charge": "charge",
        "Exp Cent": "centroid_mz",
        "Max Inty": "intensity",
    }

    column_order = list(column_mapping.values())
    column_order.insert(column_order.index("charge") + 1, "centroid_mass")
    column_order.append("rt")

    cols = _fmt_extra_columns(extra_columns)

    column_mapping.update(cols)
    column_order.extend(cols.values())

    rt_values = [convert_rt(rt_str) for rt_str in hd_examiner_df["Actual RT"]]
    rt_series = nw.new_series(values=rt_values, name="rt", backend=BACKEND)

    df = (
        hd_examiner_df.rename(column_mapping)
        .with_columns([centroid_mass, rt_series])
        .select(column_order)
        .sort(by=["state", "exposure", "start", "end", "replicate"])
    )

    return cast_exposure(df)
