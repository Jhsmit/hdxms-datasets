from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Literal, Optional, Union, TYPE_CHECKING

import narwhals as nw
from statsmodels.stats.weightstats import DescrStatsW
from uncertainties import ufloat, Variable

from hdxms_datasets.backend import BACKEND


if TYPE_CHECKING:
    from hdxms_datasets import DataFile


TIME_FACTORS = {"s": 1, "m": 60.0, "min": 60.0, "h": 3600, "d": 86400}
TEMPERATURE_OFFSETS = {"c": 273.15, "celsius": 273.15, "k": 0.0, "kelvin": 0.0}
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


# overload typing to get correct return type
def convert_temperature(
    temperature_dict: dict, target_unit: str = "c"
) -> Union[float, list[float]]:
    """
    Convenience function to convert temperature values.

    Args:
        temperature_dict: Dictionary with temperature value(s) and unit.
        target_unit: Target unit for temperature. Must be "c", "k", "celsius", or "kelvin" and is
            case-insensitive.

    Returns:
        Converted temperature value(s).
    """

    src_unit = temperature_dict["unit"].lower()
    temp_offset = TEMPERATURE_OFFSETS[src_unit] - TEMPERATURE_OFFSETS[target_unit.lower()]
    if values := temperature_dict.get("values"):
        return [v + temp_offset for v in values]
    elif value := temperature_dict.get("value"):
        return value + temp_offset
    else:
        raise ValueError("Invalid temperature dictionary")


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

    src_unit = time_dict["unit"]

    time_factor = TIME_FACTORS[src_unit] / TIME_FACTORS[target_unit]
    if values := time_dict.get("values"):
        return [v * time_factor for v in values]
    elif value := time_dict.get("value"):
        return value * time_factor
    else:
        raise ValueError("Invalid time dictionary")


def filter_peptides(
    df: nw.DataFrame,
    state: Optional[str] = None,
    exposure: Optional[dict] = None,
    dropna: bool = True,
    time_unit: Literal["s", "min", "h"] = "s",
) -> nw.DataFrame:
    """
    Convenience function to filter a peptides DataFrame. .

    Args:
        df: Input dataframe.
        state: Name of protein state to select.
        exposure: Exposure value(s) to select. Exposure is given as a :obj:`dict`, with keys "value" or "values" for
            exposure value, and "unit" for the time unit.
        query: Additional queries to pass to [pandas.DataFrame.query][].
        dropna: Drop rows with `NaN` or `null` uptake entries.
        time_unit: Time unit for exposure column of supplied dataframe.

    Examples:
        Filter peptides for a specific protein state and exposure time:

        >>> d = {"state", "SecB WT apo", "exposure": {"value": 0.167, "unit": "min"}
        >>> filtered_df = filter_peptides(df, **d)

    Returns:
        Filtered dataframe.
    """

    if state is not None:
        df = df.filter(nw.col("state") == state)

    if exposure is not None:
        t_val = convert_time(exposure, time_unit)
        if isinstance(t_val, list):
            df = df.filter(nw.col("exposure").is_in(t_val))
        else:
            df = df.filter(nw.col("exposure") == t_val)

    if dropna:
        df = df.drop_nulls("uptake").filter(~nw.col("uptake").is_nan())

    return df


def parse_data_files(data_file_spec: dict, data_dir: Path) -> dict[str, DataFile]:
    """
    Parse data file specifications from a YAML file.

    Args:
        data_file_spec: Dictionary with data file specifications.
        data_dir: Path to data directory.

    Returns:
        Dictionary with parsed data file specifications.
    """

    from hdxms_datasets import DataFile

    data_files = {}
    for name, spec in data_file_spec.items():
        datafile = DataFile(
            name=name,
            filepath_or_buffer=Path(data_dir / spec["filename"]),
            **{k: v for k, v in spec.items() if k != "filename"},
        )
        data_files[name] = datafile

    return data_files
