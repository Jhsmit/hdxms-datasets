# %%
import asyncio
from dataclasses import replace
from functools import partial
import solara
import solara.lab
from typing import Callable, Literal, cast
from solara.components.file_drop import FileInfo
from solara.toestand import Ref
import yaml
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
from hdxms_datasets.web.components import Snackbar, td, th, tr
from hdxms_datasets.web.models import PeptideInfo, UploadFile, PEPTIDE_TYPES
import narwhals as nw
from narwhals import typing as nwt

from hdxms_datasets.utils import diff_sequence

# %%

USE_AUTOSAVE = True

# %%


# %%
# dynamx_state = Path("1665149400_SecA_Krishnamurthy/data/SecA.csv")
# dynamx_cluster = Path("1744801204_SecA_cluster_Krishnamurthy/data/SecA_cluster.csv")
# hd_examiner = Path("1745478702_hd_examiner_example_Sharpe/data/data_file.csv")
secb_data = Path("1704204434_SecB_Krishnamurthy_fmt_v2")

# # %%
ROOT_DIR = Path(*Path(__file__).parts[:-3])

data_dir = ROOT_DIR / "seca_data"


TEST_DIR = ROOT_DIR / "tests" / "datasets"

data_dir = TEST_DIR / secb_data / "data"
files = list(data_dir.iterdir())


# f1 = TEST_DIR / dynamx_state
# f2 = TEST_DIR / dynamx_cluster
# f3 = TEST_DIR / hd_examiner
# %%
# files = [f3]  # , f2, f3]
print(files)
ufiles = []
for f in files:
    df = pl.read_csv(f)
    format = identify_format(df.columns, exact=False)
    if format is None:
        print(df.columns)
    assert format, f
    print(format, f.stem)
    ufile = UploadFile(
        name=f.stem,
        format=format,
        dataframe=df,
    )
    ufiles.append(ufile)
    print(df["State"].unique())
ufiles

data_files = ListStore[UploadFile](ufiles)


# %%
def make_dict(f: Path):
    df = pl.read_csv(f)
    format = identify_format(df.columns, exact=False)
    return {"filename": (Path("data") / f.name).as_posix(), "format": format.__class__.__name__}


data_files_spec = {f.stem: make_dict(f) for f in files}

s = yaml.dump(data_files_spec, sort_keys=False)
print(s)

# %%
format = "DynamX_v3_state"


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

        # reset the peptide selection
        peptide_selection.set((state, None))
        # remove the peptide
        peptide_store.remove_peptide(state, idx)
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

    def remove_state(state: str):
        if unsaved_changes.value:
            snackbar.info("Please save or discard your changes before removing a state")
            return

        peptide_selection.set((None, None))
        peptide_store.remove_state(state)

    with solara.Column(style={"max-height": "500px", "overflow-y": "auto"}):
        with solara.v.ExpansionPanels(
            v_model=selected_idx, on_v_model=update_state, focusable=True
        ):
            for i, (state, peptides) in enumerate(peptide_store.items()):
                with solara.v.ExpansionPanel():
                    style = "" if i != selected_idx else "font-weight: bold"
                    with solara.v.ExpansionPanelHeader(style_=style):
                        solara.Text(state)
                    with solara.v.ExpansionPanelContent():
                        PeptideList(state, peptides)
                        solara.Button(
                            "Remove state",
                            on_click=partial(remove_state, state),
                            block=True,
                            outlined=True,
                            dense=True,
                            small=True,
                        )


@solara.component
def PeptideInfoForm(
    peptide_info: PeptideInfo,
    peptide_state: str,
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

    subtitle = f"Editing: {peptide_state}  / {local_peptide_info.value.type}"
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
            exposure_values = upload_file.get_exposures(local_peptide_info.value.state)

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
                    state_values, key=lambda state: diff_sequence(peptide_state, state)
                )
                local_peptide_info.update(state=most_similar_state)

            solara.IconButton("mdi-auto-fix", disabled=disable_filters, on_click=auto_state)

        if local_peptide_info.value.type == "partially_deuterated":

            def auto_exposure():
                nulls = ["0s", "0", 0.0, None, "None", "n/a", "FD"]
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


# TODO move elsewhere
def make_yaml_export(invalid_peptides: Literal["skip", "raise"] = "skip") -> str:
    output = {}
    for state, peptides in peptide_store.items():
        if not peptides:
            continue

        s_dict = {}
        for p in peptides:
            valid, error = p.validate()
            if not valid:
                if invalid_peptides == "skip":
                    continue
                elif invalid_peptides == "raise":
                    raise ValueError(error)

            upload_file = data_files.find_item(name=p.filename)
            assert upload_file is not None

            fmt = upload_file.format
            p_dict = p.to_dict(fmt)
            s_dict[p.type] = p_dict

        if s_dict:
            output[state] = s_dict

    class NoAliasDumper(yaml.Dumper):
        def ignore_aliases(self, data):
            return True

    if not output:
        return ""

    s = yaml.dump(output, Dumper=NoAliasDumper, sort_keys=False)
    return s


@solara.component
def Main():
    new_state_name = solara.use_reactive("")
    peptide_type = solara.use_reactive(PEPTIDE_TYPES[0])

    selected_state, selected_peptides = peptide_selection.value
    peptide_tooltip = "Add new peptide" if selected_state else "Select a state to add peptides"

    all_states = {state for ufile in data_files.value for state in ufile.states}
    available_states = sorted(all_states - set(peptide_store.keys()))

    if selected_state is not None and selected_peptides is not None:
        try:
            peptides = peptide_store[selected_state][selected_peptides]
        except IndexError:
            # in principle deleting peptides first sets selected peptie to none
            # but it looks like somewhere it being kept as the previous index

            # print(f"Invalid peptide index {selected_peptides} for state {selected_state}")
            peptides = None
    else:
        peptides = None

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
        peptide_selection.set((state, None))

    def add_peptide():
        selected_state = peptide_selection.value[0]
        if selected_state is None:
            snackbar.info("Select a state to add peptides")
            return

        current_peptide_types = [p.type for p in peptide_store[selected_state]]
        if peptide_type.value in current_peptide_types:
            snackbar.warning(
                f"Peptide type {peptide_type.value!r} already exists in state {selected_state!r}"
            )
            return

        peptide_idx = len(peptide_store[selected_state])
        peptide_store.add_peptide(selected_state, peptide_type.value)
        peptide_selection.set((selected_state, peptide_idx))

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
                            # continuous_update=True, this doesnt exist
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
                with solara.Column():
                    with solara.FileDownload(make_yaml_export, "hdx_spec.yaml"):
                        solara.Button("Export .yaml File", color="primary", block=True)
                    if USE_AUTOSAVE:
                        AutoSaveButton()

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

            if peptides is not None and selected_state is not None:
                PeptideInfoForm(
                    peptides, selected_state, on_save=update_peptide, on_cancel=on_cancel
                )


@solara.component
def AutoSaveButton():
    open_dialog = solara.use_reactive(False)
    enable_autosave = solara.use_reactive(True)
    selected_file = solara.use_reactive(cast(Path | None, None))

    def filter(pth: Path):
        if pth.is_dir():
            return True
        if pth.suffix == ".yaml":
            return True
        return False

    async def do_autosave():
        while True:
            # make_yaml_export now skips invalid peptides
            # errors = peptide_store.validate()
            # if errors:
            #     continue

            await asyncio.sleep(1.0)

            if selected_file.value is None:
                continue
            if not enable_autosave.value:
                continue

            try:
                yaml_str = make_yaml_export()
                selected_file.value.write_text(yaml_str)
            except AssertionError:
                pass

    # solara.lab.use_task(do_autosave, dependencies=[selected_file.value, enable_autosave.value])  # noqa: SH101
    # lets run it only once and keep running to avoid multiple tasks running after hot reload
    solara.lab.use_task(do_autosave, dependencies=[], raise_error=False)  # noqa: SH101

    autosave_on = enable_autosave.value and selected_file.value is not None
    color = "green" if autosave_on else "grey"
    label = "Autosave ON" if autosave_on else "Enable autosave"

    solara.Button(label, on_click=lambda: open_dialog.set(True), color=color)

    def try_set_file(pth):
        if pth is None:
            selected_file.set(pth)
            return
        if pth.is_dir():
            return

        selected_file.set(pth)

    with solara.v.Dialog(
        v_model=open_dialog.value,
        on_v_model=open_dialog.set,
    ):
        with solara.Div(style={"width": "100%", "overflow-x": "hidden"}):
            with solara.Card("Choose file for autosave"):
                solara.FileBrowser(
                    can_select=True,
                    filter=filter,
                    on_path_select=try_set_file,
                )
                solara.Switch(label="Enable autosave", value=enable_autosave)
                solara.Text("Selected file: " + str(selected_file.value))
                with solara.CardActions():
                    solara.Button(
                        label="Close",
                        on_click=lambda: open_dialog.set(False),
                    )


@solara.component
def Page():
    # solara.Text(str(peptide_selection.value))
    # solara.Text(str(unsaved_changes.value))
    Main()
    # with solara.ColumnsResponsive([4, 8]):
    #     StatePanels()


# %%
