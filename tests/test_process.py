from pathlib import Path
import numpy as np
import polars as pl
import narwhals as nw
import pytest

from hdxms_datasets.process import (
    convert_temperature,
    dynamx_cluster_to_state,
)
from hdxms_datasets.reader import read_dynamx

TEST_PTH = Path(__file__).parent


@pytest.fixture
def cluster_data() -> nw.DataFrame:
    return read_dynamx(TEST_PTH / "test_data" / "quiescent state cluster data.csv")


@pytest.fixture
def state_data() -> nw.DataFrame:
    return read_dynamx(TEST_PTH / "test_data" / "quiescent state data.csv")


@pytest.fixture
def sample_df() -> nw.DataFrame:
    df = pl.DataFrame(
        {
            "state": ["state1", "state1", "state2", "state2"],
            "exposure": [10.0, 20.0, 10.0, 20.0],
            "uptake": [1.0, 2.0, np.nan, 4.0],
            "sequence": ["SEQ1", "SEQ2", "SEQ3", "SEQ4"],
        }
    )
    return nw.from_native(df)


def test_convert_dynamx_cluster_to_state(cluster_data, state_data):
    test_columns = ["uptake", "uptake_sd", "rt", "rt_sd", "center", "center_sd"]
    on = ["exposure", "start", "end"]

    for state in cluster_data["state"].unique():
        data = cluster_data.filter(nw.col("state") == state)
        converted_state_data = dynamx_cluster_to_state(data)

        state_data_f = state_data.filter(nw.col("state") == state)
        combined = state_data_f.join(converted_state_data, on=on, how="inner")

        combined.to_native()

        for col in test_columns:
            sq = (combined[col] - combined[f"{col}_right"]) ** 2
            mse = sq.mean()
            # uptake sd differs more since in state data directly from dynamx
            # there are several entries with zero s.d.
            if col == "uptake_sd":
                assert mse < 1e-2
            else:
                assert mse < 1e-12


def test_convert_temperature_single_value_c_to_k():
    temp_dict = {"value": 25.0, "unit": "C"}
    result = convert_temperature(temp_dict, "K")
    assert result == 298.15


def test_convert_temperature_single_value_k_to_c():
    temp_dict = {"value": 298.15, "unit": "K"}
    result = convert_temperature(temp_dict, "C")
    assert result == 25.0
