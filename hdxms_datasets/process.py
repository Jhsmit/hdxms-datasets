from __future__ import annotations

import warnings
from collections import defaultdict
from functools import reduce
from operator import and_
from typing import Literal, Optional, TypedDict, Union

import narwhals as nw
from statsmodels.stats.weightstats import DescrStatsW
from uncertainties import Variable, ufloat

import hdxms_datasets.expr as hdx_expr
from hdxms_datasets.backend import BACKEND


TIME_FACTORS = {"s": 1, "m": 60.0, "min": 60.0, "h": 3600, "d": 86400}
TEMPERATURE_OFFSETS = {"C": 273.15, "K": 0.0}
PROTON_MASS = 1.0072764665789


STATE_DATA_COLUMN_ORDER = [
    "protein",
    "start",
    "end",
    "stop",
    "sequence",
    "modification",
    "fragment",
    "maxuptake",
    "mhp",
    "state",
    "exposure",
    "center",
    "center_sd",
    "uptake",
    "uptake_sd",
    "rt",
    "rt_sd",
]


def ufloat_stats(array, weights) -> Variable:
    """Calculate the weighted mean and standard deviation."""
    weighted_stats = DescrStatsW(array, weights=weights, ddof=0)
    return ufloat(weighted_stats.mean, weighted_stats.std)


def records_to_dict(records: list[dict]) -> dict[str, list]:
    """
    Convert a list of records to a dictionary of lists.

    Args:
        records: List of dictionaries.

    Returns:
        Dictionary with keys as column names and values as lists.
    """

    df_dict = defaultdict(list)
    for record in records:
        for key, value in record.items():
            df_dict[key].append(value)

    return dict(df_dict)


def dynamx_cluster_to_state(cluster_data: nw.DataFrame, nd_exposure: float = 0.0) -> nw.DataFrame:
    """
    convert dynamx cluster data to state data
    must contain only a single state
    """

    assert len(cluster_data["state"].unique()) == 1, "Multiple states found in data"

    # determine undeuterated masses per peptide
    nd_data = cluster_data.filter(nw.col("exposure") == nd_exposure)
    nd_peptides: list[tuple[int, int]] = sorted(
        {(start, end) for start, end in zip(nd_data["start"], nd_data["end"])}
    )

    peptides_nd_mass = {}
    for p in nd_peptides:
        start, end = p
        df_nd_peptide = nd_data.filter((nw.col("start") == start) & (nw.col("end") == end))

        masses = df_nd_peptide["z"] * (df_nd_peptide["center"] - PROTON_MASS)
        nd_mass = ufloat_stats(masses, df_nd_peptide["inten"])

        peptides_nd_mass[p] = nd_mass

    groups = cluster_data.group_by(["start", "end", "exposure"])
    unique_columns = [
        "end",
        "exposure",
        "fragment",
        "maxuptake",
        "mhp",
        "modification",
        "protein",
        "sequence",
        "start",
        "state",
        "stop",
    ]
    records = []
    for (start, end, exposure), df_group in groups:
        record = {col: df_group[col][0] for col in unique_columns}

        rt = ufloat_stats(df_group["rt"], df_group["inten"])
        record["rt"] = rt.nominal_value
        record["rt_sd"] = rt.std_dev

        # state data 'center' is mass as if |charge| would be 1
        center = ufloat_stats(
            df_group["z"] * (df_group["center"] - PROTON_MASS) + PROTON_MASS, df_group["inten"]
        )
        record["center"] = center.nominal_value
        record["center_sd"] = center.std_dev

        masses = df_group["z"] * (df_group["center"] - PROTON_MASS)
        exp_mass = ufloat_stats(masses, df_group["inten"])

        if (start, end) in peptides_nd_mass:
            uptake = exp_mass - peptides_nd_mass[(start, end)]
            record["uptake"] = uptake.nominal_value
            record["uptake_sd"] = uptake.std_dev
        else:
            record["uptake"] = None
            record["uptake_sd"] = None

        records.append(record)

    d = records_to_dict(records)
    df = nw.from_dict(d, backend=BACKEND)

    if set(df.columns) == set(STATE_DATA_COLUMN_ORDER):
        df = df[STATE_DATA_COLUMN_ORDER]

    return df


class TemperatureDict(TypedDict):
    """TypedDict for temperature dictionary."""

    value: float
    unit: Literal["C", "K"]


def convert_temperature(temperature_dict: TemperatureDict, target_unit: str = "C") -> float:
    """
    Convenience function to convert temperature values.

    Args:
        temperature_dict: Dictionary with temperature value(s) and unit.
        target_unit: Target unit for temperature. Must be "C, or "K"

    Returns:
        Converted temperature value(s).
    """

    src_unit = temperature_dict["unit"]
    temp_offset = TEMPERATURE_OFFSETS[src_unit] - TEMPERATURE_OFFSETS[target_unit]
    return temperature_dict["value"] + temp_offset


def convert_time(
    time_dict: dict, target_unit: Literal["s", "min", "h"] = "s"
) -> Union[float, list[float]]:
    """
    Convenience function to convert time values.

    Args:
        time_dict: Dictionary with time value(s) and unit.
        target_unit: Target unit for time.

    Returns:
        Converted time value(s).
    """
    raise DeprecationWarning()
    src_unit = time_dict["unit"]

    time_factor = TIME_FACTORS[src_unit] / TIME_FACTORS[target_unit]
    if values := time_dict.get("values"):
        return [v * time_factor for v in values]
    elif value := time_dict.get("value"):
        return value * time_factor
    else:
        raise ValueError("Invalid time dictionary")


def filter_df(df: nw.DataFrame, **filters) -> nw.DataFrame:
    exprs = [nw.col(k) == val for k, val in filters.items()]
    f_expr = reduce(and_, exprs)
    return df.filter(f_expr)


# TODO move this method to load _peptides since it specific and not used elswhere?
def filter_peptides(
    df: nw.DataFrame,
    state: Optional[str] = None,
    exposure: Optional[dict] = None,
) -> nw.DataFrame:
    """
    Convenience function to filter a peptides DataFrame. .

    Args:
        df: Input dataframe.
        state: Name of protein state to select.
        exposure: Exposure value(s) to select. Exposure is given as a :obj:`dict`, with keys "value" or "values" for
            exposure value, and "unit" for the time unit.
        time_unit: Time unit for exposure column of supplied dataframe.

    Examples:
        Filter peptides for a specific protein state and exposure time:

        >>> d = {"state", "SecB WT apo", "exposure": {"value": 0.167, "unit": "min"}
        >>> filtered_df = filter_peptides(df, **d)

    Returns:
        Filtered dataframe.
    """
    raise DeprecationWarning()
    if state is not None:
        df = df.filter(nw.col("state") == state)

    if exposure is not None:
        # NA unit is used when exposure is given as string, in case of HD examiner this can be 'FD'
        if exposure["unit"] == "NA":
            t_val = exposure["value"]
        else:
            t_val = convert_time(exposure, "s")
        if isinstance(t_val, list):
            if all(isinstance(v, float) for v in t_val):
                col = nw.col("exposure")
            elif all(isinstance(v, str) for v in t_val):
                col = nw.col("exposure").cast(nw.Float64)
            else:
                raise ValueError("Invalid exposure values")
            df = df.filter(col.is_in(t_val))
        else:
            df = df.filter(nw.col("exposure") == t_val)

    return df


def aggregate_columns(
    df: nw.DataFrame, columns: list[str], by: list[str] = ["start", "end", "exposure"]
):
    """
    Aggregate the DataFrame the specified columns by intensity-weighted average.
    """
    groups = df.group_by(by)
    output = {k: [] for k in by}
    for col in columns:
        output[col] = []
        output[f"{col}_sd"] = []

    for (start, end, exposure), df_group in groups:
        output["start"].append(start)
        output["end"].append(end)
        output["exposure"].append(exposure)

        for col in columns:
            val = ufloat_stats(df_group[col], df_group["intensity"])
            output[col].append(val.nominal_value)
            output[f"{col}_sd"].append(val.std_dev)

    agg_df = nw.from_dict(output, backend=BACKEND)
    return agg_df


def aggregate(df: nw.DataFrame) -> nw.DataFrame:
    assert df["state"].n_unique() == 1, (
        "DataFrame must be filtered to a single state before aggregation."
    )

    # columns which are intesity weighed averaged
    intensity_wt_avg_columns = ["centroid_mz", "centroid_mass", "rt"]

    output_columns = df.columns[:]

    for col in intensity_wt_avg_columns:
        col_idx = output_columns.index(col)
        output_columns.insert(col_idx + 1, f"{col}_sd")
    output_columns += ["n_replicates", "n_cluster"]

    output = {k: [] for k in output_columns}
    groups = df.group_by(["start", "end", "exposure"])
    for (start, end, exposure), df_group in groups:
        record = {}
        record["start"] = start
        record["end"] = end
        record["exposure"] = exposure
        record["n_replicates"] = df_group["file"].n_unique()
        record["n_cluster"] = len(df_group)

        # add intensity-weighted average columns
        for col in intensity_wt_avg_columns:
            val = ufloat_stats(df_group[col], df_group["intensity"])
            record[col] = val.nominal_value
            record[f"{col}_sd"] = val.std_dev

        # add other columns, taking the first value if unique, otherwise None
        other_columns = set(df.columns) - record.keys()
        for col in other_columns:
            if df_group[col].n_unique() == 1:
                record[col] = df_group[col][0]
            else:
                record[col] = None

        # add record to output
        assert output.keys() == record.keys()
        for k in record:
            output[k].append(record[k])

    agg_df = nw.from_dict(output, backend=BACKEND)

    return agg_df


def sort(df: nw.DataFrame) -> nw.DataFrame:
    """Sorts the DataFrame by state, exposure, start, end, file."""
    all_by = ["state", "exposure", "start", "end", "file"]
    by = [col for col in all_by if col in df.columns]
    return df.sort(by=by)


def drop_null_columns(df: nw.DataFrame) -> nw.DataFrame:
    """Drop columns that are all null from the DataFrame."""
    all_null_columns = [col for col in df.columns if df[col].is_null().all()]
    return df.drop(all_null_columns)


def filter_from_spec(df, **filters):
    exprs = []
    for col, val in filters.items():
        if isinstance(val, list):
            expr = nw.col(col).is_in(val)
        else:
            expr = nw.col(col) == val
        exprs.append(expr)
    f_expr = reduce(and_, exprs)
    return df.filter(f_expr)


def left_join(df_left, df_right, column: str, prefix: str, include_sd: bool = True):
    select = [nw.col("start"), nw.col("end")]
    select.append(nw.col(column).alias(f"{prefix}_{column}"))
    if include_sd:
        select.append(nw.col(f"{column}_sd").alias(f"{prefix}_{column}_sd"))

    merge = df_left.join(
        df_right.select(select),
        on=["start", "end"],
        how="left",  # 'left' join ensures all rows from pd_peptides are kept
    )

    return merge


def merge_peptides(
    partially_deuterated: nw.DataFrame,
    column: Optional[str] = None,
    non_deuterated: Optional[nw.DataFrame] = None,
    fully_deuterated: Optional[nw.DataFrame] = None,
) -> nw.DataFrame:
    if column is not None:
        join_column = column
    elif "centroid_mass" in partially_deuterated.columns:
        join_column = "centroid_mass"
    elif "uptake" in partially_deuterated.columns:
        join_column = "uptake"

    output = partially_deuterated
    if non_deuterated is not None:
        output = left_join(output, non_deuterated, column=join_column, prefix="nd")
    if fully_deuterated is not None:
        output = left_join(output, fully_deuterated, column=join_column, prefix="fd")
    return output


def compute_uptake_metrics(df: nw.DataFrame, exception="raise") -> nw.DataFrame:
    """
    Tries to add derived columns to the DataFrame.
    Possible columns to add are: uptake, uptake_sd, fd_uptake, fd_uptake_sd, rfu, max_uptake.
    """
    all_columns = {
        "uptake": hdx_expr.uptake,
        "uptake_sd": hdx_expr.uptake_sd,
        "fd_uptake": hdx_expr.fd_uptake,
        "fd_uptake_sd": hdx_expr.fd_uptake_sd,
        "rfu": hdx_expr.rfu,
        "max_uptake": hdx_expr.max_uptake,
    }

    for col, expr in all_columns.items():
        if col not in df.columns:
            try:
                df = df.with_columns(expr)
            except Exception as e:
                if exception == "raise":
                    raise e
                elif exception == "warn":
                    warnings.warn(f"Failed to add column {col}: {e}")
                elif exception == "ignore":
                    pass
                else:
                    raise ValueError("Invalid exception handling option")

    return df
