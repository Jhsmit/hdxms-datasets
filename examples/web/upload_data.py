# %%
%load_ext autoreload
%autoreload 2
#%%
from dataclasses import dataclass
import solara
import solara.lab
from typing import Optional, cast, Literal
from solara.components.file_drop import FileInfo
from hdxms_datasets.reader import read_csv
from hdxms_datasets.formats import HDXFormat, identify_format
from hdxms_datasets.convert import from_dynamx_state, from_dynamx_cluster, from_hdexaminer
from pathlib import Path
import polars as pl
from hdxms_datasets.web.state import ListStore
from hdxms_datasets.web.models import PeptideInfo, PeptideType

#%%

kwargs = {'pH': 7.5, 'temperature': 25.0, 'd_percentage': 90.0}

p1 = PeptideInfo(**kwargs)
p2 = PeptideInfo(**kwargs)

p2.state = "test"

p1 == p2

#%%
PEPTIDE_TYPES = [
    "partially_deuterated",
    "fully_deuterated",
    "non_deuterated",
]


peptide_types = Literal["partially_deuterated", "fully_deuterated", "non_deuterated"]

peptide_types

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
# columns = read_csv(f).columns

# %%


@dataclass
class UploadFile:
    name: str
    format: HDXFormat
    dataframe: pl.DataFrame
    extension: str = ".csv"


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


# create a list of UploadFile objects for testing


# %%
data_files = ListStore[UploadFile](ufiles)


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
