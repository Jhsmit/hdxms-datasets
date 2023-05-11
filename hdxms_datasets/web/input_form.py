from typing import Callable, Any, List, Literal

from hdxms_datasets.web.components import ValidationForm
from hdxms_datasets.web.file_input import FileInput, FileInfo
from hdxms_datasets.reader import read_dynamx

import dataclasses
import uuid
import pandas as pd

import solara
from solara.alias import rv

from hdxms_datasets.web.models import ExperimentMetadata

print('joe')


# USE STEPPER: https://v2.vuetifyjs.com/en/components/steppers/

DEBUG = True

@dataclasses.dataclass
class FileItem():
    name: str
    format: Literal["dynamx", 'hdexaminer']
    df: pd.DataFrame


@solara.component
def NewFilesInput(on_new_file: Callable[[List[FileItem]], None]):

    success, set_success = solara.use_state(False)
    file_items, set_file_items = solara.use_state([])
    key, set_key = solara.use_state(str(uuid.uuid4()))

    def on_file(file_info: List[FileInfo]):

        if len(file_info) == 0:
            return
        else:
            print(file_info[0]["name"])
            try:
                file_items = []
                for file in file_info:
                    file_item = FileItem(
                        name=file["name"],
                        df=read_dynamx(file["file_obj"]), #todo select reader from dict
                        format="dynamx", # todo dropdown
                    )
                    file_items.append(file_item)

                # how many triggers does this give?
                set_success(True)
                set_file_items(file_items)
            except Exception as e:
                print(e)
                set_success(False)

    def btn_click(*args):
        set_key(str(uuid.uuid4()))
        on_new_file(file_items)

    with solara.Row() as main:
        file_input = FileInput(accept=".csv", multiple=True, lazy=True, on_file=on_file, dense=True, outlined=True, style_={'width': '100%'}).key(key)
        btn = solara.Button(label="Add", on_click=btn_click)
        if success:
            rv.Icon(children="mdi-check-bold", color="success")
        else:
            rv.Icon(children="mdi-close", color="error")



@solara.component
def Page():

    file_items, set_file_items = solara.use_state([])
    step, set_step = solara.use_state(1)

    global_exp_metadata = solara.use_reactive(ExperimentMetadata())

    def on_new_file(new_file_items: List[FileItem]):
        new_items = new_file_items + file_items
        set_file_items(new_items)



    print("current step", step)
    with rv.Stepper(non_linear=True, v_model=step, on_v_model=set_step,):
        with rv.StepperHeader():
            with rv.StepperStep(step=1, editable=True):
                solara.Text("Input data files")

            with rv.StepperStep(step=2, editable=True):
                solara.Text("Define global metadata")
            with rv.StepperStep(step=3, editable=True):
                solara.Text("Define protein states")
            with rv.StepperStep(step=4, editable=True):
                solara.Text("Submit dataset")

        with rv.StepperItems():
            with rv.StepperContent(step=1):
                with solara.Card(title="Input files",
                                 subtitle="Add your input peptide table files") as card_input_files:
                    NewFilesInput(on_new_file=on_new_file)

                    list_items = []
                    for idx, file_item in enumerate(file_items):
                        def on_delete(idx=idx):
                            new_items = file_items.copy()
                            del new_items[idx]
                            set_file_items(new_items)

                        list_item = rv.ListItem(children=[
                            rv.ListItemIcon(left=True, children=[rv.Icon(children=['mdi-file-delimited'])]),
                            rv.ListItemTitle(children=[file_item.name]),
                            rv.ListItemSubtitle(children=[f"{len(file_item.df)} peptides"]),
                            solara.IconButton(color='primary', small=True, rounded=True, icon_name='mdi-delete',
                                              on_click=lambda *args: on_delete())
                        ])
                        list_items.append(list_item)

                    rv.List(children=list_items)
                with solara.Row():
                    solara.Button("next", on_click=lambda *args: set_step(2), color='primary')


            with rv.StepperContent(step=2):
                with solara.Card(title="Set global metadata", subtitle="Set metadata applying to all protein states"):

                    exp_column = ValidationForm(global_exp_metadata)

                    exp_panel = rv.ExpansionPanel(children=[
                        rv.ExpansionPanelHeader(children=['HDX Experiment']),
                        rv.ExpansionPanelContent(children=['Metadata relating to the HDX experiment', exp_column])
                    ])

                    with solara.Column() as protein_column:
                        with solara.Tooltip("The protein concentration in the exchange buffer."):
                            solara.InputFloat(label="Protein concentration (M)")
                        with solara.Tooltip("Oligomeric state of the protein."):
                            solara.InputFloat(label="Oligomeric state.")  # TODO input int
                        with solara.Tooltip("The protein concentration in the exchange buffer."):
                            solara.InputFloat(label="Protein concentration (mg/mL)")

                    prot_panel = rv.ExpansionPanel(children=[
                        rv.ExpansionPanelHeader(children=['Protein of interest']),
                        rv.ExpansionPanelContent(
                            children=['Metadata relating to the protein of interest', protein_column])
                    ])

                    panels = rv.ExpansionPanels(children=[exp_panel, prot_panel])
                    rv.CardActions(children=[solara.Button("Save", text=True)])

            with rv.StepperContent(step=3):
                with solara.Card():
                    solara.Markdown("This is step 2")









