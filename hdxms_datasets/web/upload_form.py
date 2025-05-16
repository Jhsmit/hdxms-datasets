from dataclasses import replace
from functools import partial
import solara
import solara.lab


from typing import Optional, cast
from solara.components.file_drop import FileInfo
from solara.toestand import Ref
from hdxms_datasets.reader import read_csv
from hdxms_datasets.formats import identify_format
from hdxms_datasets.convert import from_dynamx_state, from_dynamx_cluster, from_hdexaminer
from pathlib import Path
import polars as pl
from hdxms_datasets.web.state import ListStore, PeptideStore
from hdxms_datasets.web.components import Snackbar, strong, td, th, tr, h2
from hdxms_datasets.web.models import PeptideInfo, UploadFile, PEPTIDE_TYPES
import narwhals as nw
from narwhals import typing as nwt

# %%


# %%

dynamx_state = Path("1665149400_SecA_Krishnamurthy/data/SecA.csv")
dynamx_cluster = Path("1744801204_SecA_cluster_Krishnamurthy/data/SecA_cluster.csv")
hd_examiner = Path("1745478702_hd_examiner_example_Sharpe/data/data_file.csv")

# %%
ROOT_DIR = Path(*Path(__file__).parts[:-3])
# %%
TEST_DIR = ROOT_DIR / "tests" / "datasets"

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

data_files = ListStore[UploadFile](ufiles)


@solara.component
def FileInputForm():
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

        # data_files.set(files)

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

    file_selection = solara.use_reactive(cast(int | None, None))

    with solara.v.SimpleTable():
        with solara.v.Html(tag="thead"):
            with tr():
                th("File name")
                th("Format")
                th("Size (rows)")
                th("Delete")
            for i, f in enumerate(data_files.value):
                with tr():

                    def on_delete(idx=i):
                        data_files.value.pop(idx)
                        file_selection.set(None)

                    td(f.name)
                    td(f.format.__class__.__name__)
                    td(str(f.dataframe.shape[0]))
                    td(
                        solara.Button(
                            icon_name="mdi-delete",
                            icon=True,
                            on_click=lambda: on_delete(i),
                        )
                    )

    solara.Text(str(file_selection.value))
    solara.Text(str(len(data_files.value)))
    # if data_files.items:
    #     f = data_files.items[0]
    #     solara.Text(f"File: {f.name}")
    #     solara.Text(f"Format: {f.format}")
    #     solara.DataFrame(f.dataframe)


@nw.narwhalify
def convert_df(df: nwt.FrameT, converter) -> nwt.FrameT:
    return converter(df)


def get_converted_df(upload_file: UploadFile) -> pl.DataFrame:
    df = nw.from_native(upload_file.dataframe)
    df_openhdx = upload_file.format.convert(df)
    return df_openhdx.to_native()


PEPTIDES_INITIAL_TESTING = {
    "state1": [
        PeptideInfo(type="partially_deuterated", state="state1", filename="SecA"),
        PeptideInfo(type="fully_deuterated", state="state1"),
        PeptideInfo(type="non_deuterated", state="state1"),
    ],
    "state2": [PeptideInfo(type="partially_deuterated", state="state2")],
    "state3": [
        PeptideInfo(type="partially_deuterated", state="state3"),
        PeptideInfo(type="fully_deuterated", state="state3"),
    ],
}

peptide_store = PeptideStore({k: ListStore(v) for k, v in PEPTIDES_INITIAL_TESTING.items()})
peptide_selection = solara.reactive(cast(tuple[str | None, int | None], (None, None)))


@solara.component
def PeptideList(state: str, peptides: ListStore[PeptideInfo]):
    selected_state, selected_peptide = peptide_selection.value

    def set_peptide_selection(idx: int | None):
        print("settings", idx)
        peptide_selection.set((state, idx))

    with solara.v.List(dense=True, nav=True):
        with solara.v.ListItemGroup(
            multiple=False, v_model=selected_peptide, on_v_model=set_peptide_selection
        ):
            for idx, f in enumerate(peptides.value):
                with solara.v.ListItem():
                    solara.v.ListItemContent(children=[f.type])
                    with solara.v.ListItemAction(class_="ml-auto"):
                        with solara.Row():
                            on_delete = partial(peptide_store.remove_peptide, state, idx)
                            solara.Button(
                                icon_name="mdi-delete",
                                icon=True,
                                on_click=on_delete,
                            )
                            # with solara.v.ListItemAction():
                            # solara.Button(
                            #     icon_name="mdi-pencil",
                            #     icon=True,
                            #     on_click=lambda: None,
                            # )


@solara.component
def StatePanels():
    selected = solara.use_reactive(None)
    # state = "state1"
    # peptides = peptide_store[state]
    # PeptideList(state, peptides)

    selected_state = peptide_selection.value[0]
    selected_idx = list(peptide_store.keys()).index(selected_state) if selected_state else None

    def update_state(state_idx: int | None):
        if state_idx is None:
            state = None
        else:
            state = list(peptide_store.keys())[state_idx]

        new_peptide_selection = (state, peptide_selection.value[1])
        peptide_selection.set(new_peptide_selection)

    # solara.Text(str(selected.value))
    with solara.v.ExpansionPanels(v_model=selected_idx, on_v_model=update_state):
        for i, (state, peptides) in enumerate(peptide_store.items()):
            with solara.v.ExpansionPanel():
                style = "" if i != selected_idx else "font-weight: bold"
                # print(i, selected_idx, hdr)
                solara.v.ExpansionPanelHeader(children=[state], style_=style)
                with solara.v.ExpansionPanelContent():
                    PeptideList(state, peptides)


def PeptideInfoForm(peptide_info: PeptideInfo, on_submit: solara.Callable[[PeptideInfo], None]):
    file_name = solara.use_reactive(cast(str | None, None))
    upload_file = data_files.find_item(name=file_name.value)
    local_peptide_info = solara.use_reactive(replace(peptide_info))

    subtitle = f"Editing: {local_peptide_info.value.state}  / {local_peptide_info.value.type}"
    with solara.Card("Peptides metadata", subtitle=subtitle):
        # solara.Markdown(f"**Protein State**: {local_peptide_info.value.state}")
        # solara.Markdown(f"**Peptide type**: {local_peptide_info.value.type}")
        solara.Select(
            label="Choose file",
            values=[ufile.name for ufile in ufiles],
            value=Ref(local_peptide_info.fields.filename),
        )
        # solara.Select(label="Type", values=PEPTIDE_TYPES, value=Ref(peptide.fields.type))

        # if upload_file is not None:
        solara.Div(style={"height": "10px"})
        solara.v.Divider()
        solara.Div(style={"height": "10px"})

        if upload_file is None:
            disable_filters = True
            state_values = []
            state_label = "< select file to enable >"
            exposure_label = "< select file to enable >"
            exposure_values = []
        else:
            disable_filters = False
            fmt = upload_file.format
            state_label = fmt.state_name
            exposure_label = fmt.exposure_name
            state_values = upload_file.dataframe[fmt.state_name].unique().to_list()
            exposure_values = upload_file.dataframe[fmt.exposure_name].unique().to_list()

        solara.Select(
            label=state_label,
            value=Ref(local_peptide_info.fields.state),
            values=state_values,
            disabled=disable_filters,
            dense=True,
        )

        if local_peptide_info.value.type == "partially_deuterated":
            solara.SelectMultiple(
                label=exposure_label,
                values=Ref(local_peptide_info.fields.exposure_values),
                all_values=exposure_values,
                disabled=disable_filters,
                dense=True,
            )
        else:
            solara.Select(
                label=exposure_label,
                value=Ref(local_peptide_info.fields.exposure),
                values=exposure_values,
                disabled=disable_filters,
                dense=True,
            )
        if local_peptide_info.value.type == "partially_deuterated":
            # with solara.Card("Experimental conditions"):
            solara.Div(style={"height": "10px"})
            solara.v.Divider()
            solara.Div(style={"height": "30px"})
            solara.Text("Experiment metadata:")

            solara.InputFloat(
                label="Temperature °C", value=Ref(local_peptide_info.fields.temperature)
            )
            solara.InputFloat(label="pH", value=Ref(local_peptide_info.fields.pH))
            solara.InputFloat(
                label="Deuteration percentage", value=Ref(local_peptide_info.fields.d_percentage)
            )

        with solara.CardActions():
            solara.Button(
                "Submit",
                color="primary",
                on_click=lambda: on_submit(local_peptide_info.value),
            )
            solara.Button(
                "Cancel",
                color="secondary",
                on_click=lambda: None,
            )


@solara.component
def Main():
    new_state_name = solara.use_reactive("")
    selected_state, selected_peptides = peptide_selection.value
    peptide_type = solara.use_reactive(PEPTIDE_TYPES[0])

    peptide_tooltip = "Add new peptide" if selected_state else "Select a state to add peptides"

    if selected_state is not None and selected_peptides is not None:
        peptides = peptide_store[selected_state][selected_peptides]
    else:
        peptides = None

    Snackbar()
    with solara.ColumnsResponsive([5, 7]):
        with solara.Column():
            with solara.Card("Add new state"):
                with solara.Row():
                    solara.InputText("State Name", value=new_state_name)
                    solara.IconButton(
                        "mdi-plus",
                        fab=True,
                        x_large=True,
                        color="primary",
                        on_click=lambda: peptide_store.add_state(new_state_name.value),
                    )

            with solara.Card("Current States"):
                StatePanels()

            with solara.Card("Export"):
                solara.Button(
                    "Export .yaml File", color="primary", on_click=lambda: None, block=True
                )

        def add_peptide():
            # assert peptide_selection.value[0] is not None
            peptide_store.add_peptide(peptide_selection.value[0], peptide_type.value)

        with solara.Column():
            # todo check for duplicate peptide type
            with solara.Card("Add new peptides"):
                with solara.Row():
                    solara.Select(
                        label="Peptide type",
                        values=PEPTIDE_TYPES,
                        value=peptide_type,
                        on_value=peptide_type.set,
                    )

                    with solara.Tooltip(peptide_tooltip):
                        solara.IconButton(
                            "mdi-plus",
                            fab=True,
                            x_large=True,
                            color="primary",
                            on_click=add_peptide,
                        )

            # if editing:
            if peptides is not None:
                PeptideInfoForm(peptides, on_submit=lambda x: None)

    # if converted_df is not None:
    #     solara.DataFrame(converted_df)

    # solara.Text(str(peptide.value))


@solara.component
def Page():
    solara.Text(str(peptide_selection.value))
    Main()
    # with solara.ColumnsResponsive([4, 8]):
    #     StatePanels()


# %%
