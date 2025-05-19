# %%
from dataclasses import replace
from functools import partial
import solara
import solara.lab

from typing import Callable, cast
from solara.components.file_drop import FileInfo
from solara.toestand import Ref
from hdxms_datasets.formats import identify_format
from pathlib import Path
import polars as pl
from hdxms_datasets.web.state import (
    ListStore,
    peptide_selection,
    peptide_store,
    snackbar,
    unsaved_changes,
)
from hdxms_datasets.web.components import InputNumeric, Snackbar, td, th, tr
from hdxms_datasets.web.models import PeptideInfo, UploadFile, PEPTIDE_TYPES
import narwhals as nw
from narwhals import typing as nwt

from hdxms_datasets.web.utils import diff_sequence

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

# %%


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


@solara.component
def PeptideList(state: str, peptides: ListStore[PeptideInfo]):
    selected_state, selected_peptide = peptide_selection.value

    def set_peptide_selection(idx: int | None):
        if unsaved_changes.value:
            snackbar.info("Please save or discard your changes before selecting a peptide")
            return

        peptide_selection.set((state, idx))

    def delete_peptide(state: str, idx: int):
        if unsaved_changes.value:
            snackbar.info("Please save or discard your changes before deleting a peptide")
            return

        peptide_store.remove_peptide(state, idx)
        # reset the peptide selection
        peptide_selection.set((state, None))
        # reset the unsaved changes
        unsaved_changes.set(False)

    with solara.v.List(dense=True, nav=True):
        with solara.v.ListItemGroup(
            multiple=False, v_model=selected_peptide, on_v_model=set_peptide_selection
        ):
            for idx, f in enumerate(peptides.value):
                with solara.v.ListItem():
                    solara.v.ListItemContent(children=[f.type])
                    with solara.v.ListItemAction(class_="ml-auto"):
                        with solara.Row():
                            on_delete = partial(delete_peptide, state, idx)
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
    selected_state = peptide_selection.value[0]
    selected_idx = list(peptide_store.keys()).index(selected_state) if selected_state else None

    def update_state(state_idx: int | None):
        if state_idx is None:
            state = None
        else:
            state = list(peptide_store.keys())[state_idx]

        new_peptide_selection = (state, None)
        peptide_selection.set(new_peptide_selection)

    with solara.v.ExpansionPanels(v_model=selected_idx, on_v_model=update_state):
        for i, (state, peptides) in enumerate(peptide_store.items()):
            with solara.v.ExpansionPanel():
                style = "" if i != selected_idx else "font-weight: bold"
                solara.v.ExpansionPanelHeader(children=[state], style_=style)
                with solara.v.ExpansionPanelContent():
                    PeptideList(state, peptides)


counter = 0

# check out https://solara.dev/ for documentation
# or https://github.com/widgetti/solara/
# And check out https://py.cafe/maartenbreddels for more examples
import solara
import dataclasses
from solara.toestand import Ref
# reactive variables will trigger a component rerender
# when changed.
# When you change the default (now 0), hit the embedded browser
# refresh button to reset the state


@solara.component
def PeptideInfoForm(
    peptide_info: PeptideInfo,
    on_save: Callable[[PeptideInfo], None],
    on_cancel: Callable[[], None],
):
    local_peptide_info = solara.use_reactive(solara.use_memo(lambda: replace(peptide_info)))
    upload_file = data_files.find_item(name=local_peptide_info.value.filename)

    # check if there are unsaved changes, if so set the reactive
    if local_peptide_info.value != peptide_info:
        unsaved_changes.set(True)
    else:
        unsaved_changes.set(False)

    subtitle = f"Editing: {local_peptide_info.value.state}  / {local_peptide_info.value.type}"
    with solara.Card("Peptides metadata", subtitle=subtitle):
        solara.Select(
            label="Choose file",
            values=[ufile.name for ufile in ufiles],
            value=Ref(local_peptide_info.fields.filename),
        )

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
            state_values = upload_file.states
            exposure_values = upload_file.exposures

        with solara.Row():
            solara.Select(
                label=state_label,
                value=Ref(local_peptide_info.fields.state),
                values=state_values,
                disabled=disable_filters,
                dense=True,
            )

            def auto_state():
                most_similar_state = max(
                    state_values, key=lambda state: diff_sequence(test_state, state)
                )
                local_peptide_info.update(state=most_similar_state)

            solara.IconButton("mdi-auto-fix", disabled=disable_filters, on_click=auto_state)

        if local_peptide_info.value.type == "partially_deuterated":

            def auto_exposure():
                nulls = ["0s", "0", 0.0, pl.nan, None, "None", "n/a"]
                non_null_exposure_values = [v for v in exposure_values if v not in nulls]
                local_peptide_info.update(exposure_values=non_null_exposure_values)

            with solara.Row():
                solara.SelectMultiple(
                    label=exposure_label,
                    values=Ref(local_peptide_info.fields.exposure_values),
                    all_values=exposure_values,
                    disabled=disable_filters,
                    dense=True,
                )
                with solara.Tooltip("Auto select nonzero exposure values"):
                    solara.IconButton(
                        "mdi-auto-fix",
                        disabled=disable_filters,
                        on_click=auto_exposure,
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
            solara.Div(style={"height": "10px"})
            solara.v.Divider()
            solara.Div(style={"height": "30px"})
            solara.Text("Experimental metadata:")

            # issue continous_update: https://py.cafe/jhsmit/solara-dataclass-ref-continous
            continuous_update = False
            solara.InputFloat(
                label="Temperature °C",
                value=Ref(local_peptide_info.fields.temperature),
                continuous_update=continuous_update,
            )
            with solara.Tooltip("Uncorrected pH value (pH read)"):
                solara.InputFloat(
                    label="pH",
                    value=Ref(local_peptide_info.fields.pH),
                    continuous_update=continuous_update,
                )
            solara.InputFloat(
                label="Deuteration percentage",
                value=Ref(local_peptide_info.fields.d_percentage),
                continuous_update=continuous_update,
            )

        with solara.CardActions():
            solara.Button(
                "Save",
                color="primary",
                on_click=lambda: on_save(local_peptide_info.value),
                disabled=not unsaved_changes.value,
            )
            solara.Button(
                "Cancel",
                color="secondary",
                on_click=on_cancel,
            )


@solara.component
def Main():
    new_state_name = solara.use_reactive("")
    peptide_type = solara.use_reactive(PEPTIDE_TYPES[0])

    selected_state, selected_peptides = peptide_selection.value
    peptide_tooltip = "Add new peptide" if selected_state else "Select a state to add peptides"

    all_states = {state for ufile in data_files.value for state in ufile.states}
    available_states = sorted(all_states - set(peptide_store.keys()))
    solara.Text(new_state_name.value)

    if selected_state is not None and selected_peptides is not None:
        peptides = peptide_store[selected_state][selected_peptides]
        update_peptide = partial(peptide_store.update_peptide, selected_state, selected_peptides)
    else:
        peptides = None
        # update_peptide = lambda *args: None

    def update_peptide(peptide: PeptideInfo):
        if selected_state is None or selected_peptides is None:
            snackbar.info("Select a state/peptide to update peptides")
            # should be impossible to reach this point
            return

        valid, msg = peptide.validate()
        if not valid:
            snackbar.warning(msg)
            return

        peptide_store.update_peptide(selected_state, selected_peptides, peptide)

    def add_state():
        state = new_state_name.value
        if not state:
            snackbar.warning("State name cannot be empty")
            return
        if state in peptide_store.keys():
            snackbar.warning(f"State {state!r} already exists")
            return
        peptide_store.add_state(state)
        new_state_name.set("")

    def add_peptide():
        state = peptide_selection.value[0]
        if state is None:
            snackbar.info("Select a state to add peptides")
            return

        current_peptide_types = [p.type for p in peptide_store[state].value]
        if peptide_type in current_peptide_types:
            snackbar.warning(f"Peptide type {peptide_type!r} already exists in state {state!r}")
            return

        peptide_store.add_peptide(peptide_selection.value[0], peptide_type.value)

    def on_cancel():
        # reset the peptide selection
        peptide_selection.set((selected_state, None))
        # reset the unsaved changes
        unsaved_changes.set(False)

    Snackbar()
    with solara.ColumnsResponsive([5, 7]):
        with solara.Column():
            with solara.Card("Add new state"):
                with solara.Row():
                    with solara.Tooltip(
                        "Add a new custom state name or add from a list of available states"
                    ):
                        solara.v.Combobox(
                            label="State name",
                            items=available_states,
                            v_model=new_state_name.value,
                            on_v_model=new_state_name.set,
                        )
                    solara.IconButton(
                        "mdi-plus",
                        fab=True,
                        x_large=True,
                        color="primary",
                        on_click=add_state,
                    )

            with solara.Card("Current States"):
                StatePanels()

            with solara.Card("Export"):
                solara.Button(
                    "Export .yaml File", color="primary", on_click=lambda: None, block=True
                )

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

            if peptides is not None:
                PeptideInfoForm(peptides, on_save=update_peptide, on_cancel=on_cancel)


@solara.component
def Page():
    solara.Text(str(peptide_selection.value))
    solara.Text(str(unsaved_changes.value))
    Main()
    # with solara.ColumnsResponsive([4, 8]):
    #     StatePanels()


# %%
