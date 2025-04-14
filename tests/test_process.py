import numpy as np
import pandas as pd
import pytest

from hdxms_datasets.process import convert_temperature, convert_time, filter_peptides


def test_convert_temperature_single_value_c_to_k():
    temp_dict = {"value": 25.0, "unit": "c"}
    result = convert_temperature(temp_dict, "k")
    assert result == 298.15


def test_convert_temperature_single_value_k_to_c():
    temp_dict = {"value": 298.15, "unit": "k"}
    result = convert_temperature(temp_dict, "c")
    assert result == 25.0


def test_convert_temperature_list_of_values():
    temp_dict = {"values": [0.0, 25.0, 100.0], "unit": "c"}
    result = convert_temperature(temp_dict, "k")
    assert result == [273.15, 298.15, 373.15]


def test_convert_temperature_case_insensitive():
    temp_dict = {"value": 25.0, "unit": "C"}
    result = convert_temperature(temp_dict, "K")
    assert result == 298.15


def test_convert_temperature_full_unit_names():
    temp_dict = {"value": 25.0, "unit": "celsius"}
    result = convert_temperature(temp_dict, "kelvin")
    assert result == 298.15


def test_convert_temperature_same_unit():
    temp_dict = {"value": 25.0, "unit": "c"}
    result = convert_temperature(temp_dict, "c")
    assert result == 25.0


def test_convert_temperature_invalid_dict():
    temp_dict = {"unit": "c"}
    with pytest.raises(ValueError, match="Invalid temperature dictionary"):
        convert_temperature(temp_dict)


@pytest.mark.parametrize(
    "time_dict, target_unit, expected",
    [
        ({"value": 60, "unit": "s"}, "min", 1.0),
        ({"value": 1, "unit": "min"}, "s", 60.0),
        ({"value": 2, "unit": "h"}, "min", 120.0),
        ({"value": 1, "unit": "d"}, "h", 24.0),
        ({"values": [60, 120], "unit": "s"}, "min", [1.0, 2.0]),
        ({"values": [1, 2], "unit": "min"}, "s", [60.0, 120.0]),
        ({"values": [1, 2], "unit": "h"}, "min", [60.0, 120.0]),
        ({"value": 60, "unit": "s"}, "s", 60.0),
    ],
)
def test_convert_time(time_dict, target_unit, expected):
    result = convert_time(time_dict, target_unit)
    assert result == expected


def test_convert_time_invalid_dict():
    time_dict = {"unit": "s"}
    with pytest.raises(ValueError, match="Invalid time dictionary"):
        convert_time(time_dict)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "state": ["state1", "state1", "state2", "state2"],
            "exposure": [10.0, 20.0, 10.0, 20.0],
            "uptake": [1.0, 2.0, np.nan, 4.0],
            "sequence": ["SEQ1", "SEQ2", "SEQ3", "SEQ4"],
        }
    )


def test_filter_peptides_by_state(sample_df):
    result = filter_peptides(sample_df, state="state1")
    assert len(result) == 2
    assert all(result["state"] == "state1")


def test_filter_peptides_by_exposure_single_value(sample_df):
    exposure = {"value": 10.0, "unit": "s"}
    result = filter_peptides(sample_df, exposure=exposure)
    assert len(result) == 1  # Only state1 with exposure 10.0 has non-NaN uptake
    assert all(result["exposure"] == 10.0)


def test_filter_peptides_by_exposure_multiple_values(sample_df):
    exposure = {"values": [10.0, 20.0], "unit": "s"}
    result = filter_peptides(sample_df, exposure=exposure)
    assert len(result) == 3  # All rows except state2/exposure 10.0 which has NaN uptake


def test_filter_peptides_with_unit_conversion(sample_df):
    exposure = {"value": 1 / 60, "unit": "min"}  # 1/60 min = 1s
    # Use a modified df where exposure is in minutes
    df_min = sample_df.copy()
    df_min["exposure"] = df_min["exposure"] / 60  # convert to minutes
    result = filter_peptides(df_min, exposure=exposure, time_unit="min")
    assert len(result) == 0  # Nothing matches 1s when converted to minutes


def test_filter_peptides_with_query(sample_df):
    result = filter_peptides(sample_df, query=["sequence == 'SEQ1'"])
    assert len(result) == 1
    assert result.iloc[0]["sequence"] == "SEQ1"


def test_filter_peptides_with_multiple_conditions(sample_df):
    result = filter_peptides(
        sample_df,
        state="state1",
        exposure={"value": 10.0, "unit": "s"},
        query=["sequence == 'SEQ1'"],
    )
    assert len(result) == 1
    assert result.iloc[0]["state"] == "state1"
    assert result.iloc[0]["exposure"] == 10.0
    assert result.iloc[0]["sequence"] == "SEQ1"


def test_filter_peptides_keep_na(sample_df):
    result = filter_peptides(sample_df, dropna=False)
    assert len(result) == 4  # All rows


def test_filter_peptides_drop_na(sample_df):
    result = filter_peptides(sample_df, dropna=True)
    assert len(result) == 3  # All rows except the one with NaN uptake
    assert not result["uptake"].isna().any()


def test_filter_peptides_empty_result(sample_df):
    result = filter_peptides(sample_df, state="non_existent_state")
    assert len(result) == 0
    assert isinstance(result, pd.DataFrame)
