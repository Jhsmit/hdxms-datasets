from hdxms_datasets.backend import BACKEND
from hdxms_datasets.expr import centroid_mass


import narwhals as nw

from hdxms_datasets.reader import cast_exposure


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


def convert_rt(rt_str: str) -> float:
    """convert hd examiner rt string to float
    example: "7.44-7.65" -> 7.545
    """
    lower, upper = rt_str.split("-")
    mean = (float(lower) + float(upper)) / 2.0
    return mean


def from_hdexaminer(
    hd_examiner_df: nw.DataFrame,
    extra_columns: list[str] | dict[str, str] | str | None = None,
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
