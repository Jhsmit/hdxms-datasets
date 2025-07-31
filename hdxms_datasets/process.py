from __future__ import annotations

from pathlib import Path
import warnings
from functools import reduce
from operator import and_
from typing import Optional
import narwhals as nw
from statsmodels.stats.weightstats import DescrStatsW
from uncertainties import Variable, ufloat

import hdxms_datasets.expr as hdx_expr
from hdxms_datasets.formats import OPEN_HDX_COLUMNS
from hdxms_datasets.loader import load_peptides, BACKEND
from hdxms_datasets.models import DeuterationType, Peptides
from hdxms_datasets.utils import peptides_are_unique, records_to_dict


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


def apply_filters(df, **filters):
    exprs = []
    for col, val in filters.items():
        if isinstance(val, list):
            expr = nw.col(col).is_in(val)
        else:
            expr = nw.col(col) == val
        exprs.append(expr)
    if not exprs:
        return df
    f_expr = reduce(and_, exprs)
    return df.filter(f_expr)


@nw.narwhalify
def aggregate_columns(
    df: nw.DataFrame, columns: list[str], by: list[str] = ["start", "end", "exposure"]
) -> nw.DataFrame:
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
        record["n_replicates"] = df_group["replicate"].n_unique()
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


def sort_rows(df: nw.DataFrame) -> nw.DataFrame:
    """Sorts the DataFrame by state, exposure, start, end, file."""
    all_by = ["state", "exposure", "start", "end", "replicate"]
    by = [col for col in all_by if col in df.columns]
    return df.sort(by=by)


def sort_columns(df: nw.DataFrame, columns: list[str] = OPEN_HDX_COLUMNS) -> nw.DataFrame:
    matching_columns = [col for col in columns if col in df.columns]
    other_columns = [col for col in df.columns if col not in matching_columns]

    assert set(df.columns) == set(matching_columns + other_columns)

    return df[matching_columns + other_columns]


def drop_null_columns(df: nw.DataFrame) -> nw.DataFrame:
    """Drop columns that are all null from the DataFrame."""
    all_null_columns = [col for col in df.columns if df[col].is_null().all()]
    return df.drop(all_null_columns)


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


# TODO narwhalify
def merge_peptide_tables(
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
        assert peptides_are_unique(non_deuterated), "Non-deuterated peptides must be unique."
        output = left_join(output, non_deuterated, column=join_column, prefix="nd")
    if fully_deuterated is not None:
        assert peptides_are_unique(fully_deuterated), "Fully deuterated peptides must be unique."
        output = left_join(output, fully_deuterated, column=join_column, prefix="fd")
    return output


def merge_peptides(peptides: list[Peptides], base_dir: Path = Path.cwd()) -> nw.DataFrame:
    """Merge peptide tables from different deuteration types into a single DataFrame."""
    peptide_types = {p.deuteration_type for p in peptides}
    if not peptides:
        raise ValueError("No peptides provided for merging.")

    if len(peptide_types) != len(peptides):
        raise ValueError(
            "Multiple peptides of the same type found. Please ensure unique deuteration types."
        )

    if DeuterationType.partially_deuterated not in peptide_types:
        raise ValueError("Partially deuterated peptide is required for uptake metrics calculation.")

    loaded_peptides = {
        p.deuteration_type.value: load_peptides(p, base_dir=base_dir) for p in peptides
    }

    merged = merge_peptide_tables(**loaded_peptides, column=None)
    return merged


def compute_uptake_metrics(df: nw.DataFrame, exception="raise") -> nw.DataFrame:
    """
    Tries to add derived columns to the DataFrame.
    Possible columns to add are: uptake, uptake_sd, fd_uptake, fd_uptake_sd, rfu, max_uptake.
    """
    all_columns = {
        "max_uptake": hdx_expr.max_uptake,
        "uptake": hdx_expr.uptake,
        "uptake_sd": hdx_expr.uptake_sd,
        "fd_uptake": hdx_expr.fd_uptake,
        "fd_uptake_sd": hdx_expr.fd_uptake_sd,
        "frac_fd_control": hdx_expr.frac_fd_control,
        "frac_fd_control_sd": hdx_expr.frac_fd_control_sd,
        "frac_max_uptake": hdx_expr.frac_max_uptake,
        "frac_max_uptake_sd": hdx_expr.frac_max_uptake_sd,
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
