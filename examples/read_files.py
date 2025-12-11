# %%

from pathlib import Path

from hdxms_datasets import identify_format

# %%

cwd = Path(__file__).parent

# %%

# read a hxms file
f = cwd / "test_data" / "ecDHFR" / "ecDHFR_2025-09-23_APO.hxms"

fmt_spec = identify_format(f)
# read to dataframe
df = fmt_spec.read(f)

# convert to open-hdx format
df_converted = fmt_spec.convert(df)
df_converted.to_native()

# %%
# read an dynamx file
f = cwd / "test_data" / "ecSecB" / "ecSecB_apo.csv"
fmt_spec = identify_format(f)
# read to dataframe
df = fmt_spec.read(f)

# convert to open-hdx format
df_converted = fmt_spec.convert(df)
df_converted.to_native()
# %%
