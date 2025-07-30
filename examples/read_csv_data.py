from pathlib import Path
from typing import IO, Literal, Optional
from hdxms_datasets.process import dynamx_cluster_to_state
import narwhals as nw
import polars as pl


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

    df = nw.from_native(pl.read_csv(filepath_or_buffer))
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


# %%
ROOT = Path(__file__).parent.parent
TEST_PTH = ROOT / "tests"
DATA_ID = "1665149400_SecA_Krishnamurthy"

# read a state data file
csv_file = TEST_PTH / "datasets" / DATA_ID / "data" / "SecA.csv"
csv_dynamx = read_dynamx(csv_file).to_native()
csv_dynamx
# %%

# read a cluster data file, select a single state and convert to state data
csv_file = TEST_PTH / "test_data" / "quiescent state cluster data.csv"
cluster_data = read_dynamx(csv_file)

state = "SecA1-901 wt apo"
cluster_data = cluster_data.filter(nw.col("state") == state)

converted_state_data = dynamx_cluster_to_state(cluster_data)
df_out = converted_state_data.to_native()

print(df_out)

# %%
