# %%

from pathlib import Path
from hdxms_datasets.process import PROTON_MASS, ufloat_stats
import narwhals as nw
from uncertainties import Variable
from hdxms_datasets.backend import BACKEND
import numpy as np

# %%
ROOT = Path(__file__).parent.parent
TEST_PTH = ROOT / "tests"
ND_EXPOSURE = "0s"

# read a cluster data file, select a single state and convert to state data
csv_file = TEST_PTH / "test_data" / "hd_examiner_example.csv"
hd_examiner_data = nw.read_csv(csv_file.as_posix(), backend=BACKEND)


def peptide_mass(df) -> dict[tuple[int, int], Variable]:
    nd_peptides: list[tuple[int, int]] = sorted(
        {(start, end) for start, end in zip(df["Start"], df["End"])}
    )

    peptides_mass = {}
    for p in nd_peptides:
        start, end = p
        df_f = df.filter((nw.col("Start") == start) & (nw.col("End") == end))
        masses = df_f["Charge"] * (df_f["Exp Cent"] - PROTON_MASS)
        nd_mass = ufloat_stats(masses, df_f["Max Inty"])

        peptides_mass[p] = nd_mass

    return peptides_mass


def calc_uptake(df, nd_mass_dict: dict[tuple[int, int], Variable]) -> np.ndarray:
    output = np.empty_like(df["mass"])
    for i, row in enumerate(df.iter_rows(named=True)):
        start, end = row["Start"], row["End"]
        nd_mass = nd_mass_dict.get((start, end), None)
        exp_mass = row["mass"]
        if nd_mass is not None and exp_mass is not None:
            uptake = exp_mass - nd_mass.nominal_value
            output[i] = uptake
        else:
            output[i] = np.nan

    return output


states = list(hd_examiner_data["Protein State"].unique())


def test_calc_uptake():
    for state in states:
        data = hd_examiner_data.filter(nw.col("Protein State") == state)
        nd_data = data.filter(nw.col("Deut Time") == ND_EXPOSURE)
        peptides_nd_mass = peptide_mass(nd_data)

        col_mass = (nw.col("Charge") * (nw.col("Exp Cent") - PROTON_MASS)).alias("mass")
        pd_data = data.filter(nw.col("Deut Time") != "FD").with_columns(col_mass)
        uptake = calc_uptake(pd_data, peptides_nd_mass)

        d_uptake = nw.new_series(values=uptake, name="uptake", backend=BACKEND)
        compare_data = (
            pd_data.select(d_uptake, nw.col("# Deut"), nw.col("Cent Diff"), nw.col("Charge"))
            .filter(nw.col("# Deut") != "n/a")
            .with_columns(nw.col("# Deut").cast(nw.Float64))
        )

        diff = compare_data["uptake"] / (0.9) - compare_data["# Deut"]
        mean_diff = np.mean(np.abs(diff))
        max_diff = np.max(np.abs(diff))
        assert np.mean(np.abs(diff)) < 0.0022, mean_diff
        print(state, mean_diff, max_diff)

        # calculate uptake from 'Cent Diff', compare to 'uptake'
        compare_data = compare_data.with_columns(
            (nw.col("Cent Diff").cast(nw.Float64) * nw.col("Charge").cast(nw.Int32)).alias(
                "uptake_from_cent_diff"
            )
        )
        diff_cent = compare_data["uptake"] - compare_data["uptake_from_cent_diff"]

        mean_diff_cent = np.mean(np.abs(diff_cent))
        assert mean_diff_cent < 0.002, mean_diff_cent


# %%
