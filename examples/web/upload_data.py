import solara
import solara.lab
from typing import cast
from solara.components.file_drop import FileInfo
from hdxms_datasets.formats import identify_format
from pathlib import Path
import polars as pl
from hdxms_datasets.web.state import ListStore, peptide_store
from hdxms_datasets.web.models import UploadFile

# %%

# %%

ROOT_DIR = Path(*Path(__file__).parts[:-3])
TEST_DIR = ROOT_DIR / "tests" / "datasets"

dynamx_state = Path("1665149400_SecA_Krishnamurthy/data/SecA.csv")
dynamx_cluster = Path("1744801204_SecA_cluster_Krishnamurthy/data/SecA_cluster.csv")
hd_examiner = Path("1745478702_hd_examiner_example_Sharpe/data/data_file.csv")

# %%
f1 = TEST_DIR / dynamx_state
f2 = TEST_DIR / dynamx_cluster
f3 = TEST_DIR / hd_examiner

# %%
files = [f1, f2, f3]
ufiles = []
for f in files:
    df = pl.read_csv(f)
    format = identify_format(df.columns, exact=False)
    assert format
    ufile = UploadFile(
        name=f.stem,
        format=format,
        dataframe=df,
    )
    ufiles.append(ufile)

ufiles

# %%

data_files = ListStore[UploadFile](ufiles)

peptide_store.value

peptides = peptide_store["state1"]
p = peptides.value[0]

# %%

str.title("fully_deuterated").replace("_", " ")
print("todo cont update new state")
# %%

output = {}

for state, peptides in peptide_store.items():
    if not peptides:
        continue

    s_dict = {}
    for p in peptides:
        upload_file = data_files.find_item(name=p.filename)
        assert upload_file is not None

        fmt = upload_file.format
        p_dict = p.to_dict(fmt)
        s_dict[p.type] = p_dict
    output[state] = s_dict

output


# %%

p_dict = {}
p_dict["data_file"] = p.filename

f_dict = {}
f_dict[fmt.state_name] = p.state
f_dict[fmt.exposure_name] = p.exposure or p.exposure_values
p_dict["filters"] = f_dict

m_dict = {}
m_dict["pH"] = p.pH
assert p.temperature is not None
m_dict["temperature"] = {"value": p.temperature + 273.15, "unit": "K"}
m_dict["d_percentage"] = p.d_percentage
p_dict["metadata"] = m_dict

p_dict
# %%


# %%


@solara.component
def Page():
    file_info = solara.use_reactive(cast(list[FileInfo], []))

    def load_files():
        files = cast(list[UploadFile], [])
        for info in file_info.value:
            fname = Path(info["name"])
            if fname.suffix != ".csv":
                continue

            dataframe = pl.read_csv(info["file_obj"])
            format = identify_format(dataframe.columns, exact=False)
            if format is None:
                # TODO handle invalid format
                continue

            f = UploadFile(
                name=fname.name,
                format=format,
                dataframe=dataframe,
            )
            files.append(f)

        data_files.set(files)

    load_task = solara.lab.use_task(load_files, dependencies=[file_info.value])

    solara.FileDropMultiple(
        label="Drag and drop files(s) here.",
        on_file=file_info.set,
        lazy=True,
    )
    solara.ProgressLinear(load_task.pending)

    if file_info.value:
        solara.Text(str(len(file_info.value)))
        solara.Text(str(file_info.value))

    if load_task.finished:
        if data_files.value:
            f = data_files.value[0]
            solara.Text(f"File: {f.name}")
            solara.Text(f"Format: {f.format}")
            solara.DataFrame(f.dataframe)


page = Page()
page

# %%
