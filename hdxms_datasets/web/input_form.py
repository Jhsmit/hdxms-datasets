from typing import Callable, Any, List, Literal
from hdxms_datasets.web.file_input import FileInput, FileInfo
from hdxms_datasets.reader import read_dynamx

import dataclasses
import uuid
import pandas as pd

import solara
from solara.alias import rv
print('joe')


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
        file_input = FileInput(accept=".csv", multiple=True, lazy=True, on_file=on_file, dense=True, outlined=True).key(key)
        btn = solara.Button(label="Add", on_click=btn_click)
        if success:
            rv.Icon(children="mdi-check-bold", color="success")
        else:
            rv.Icon(children="mdi-close", color="error")



@solara.component
def Page():

    file_items, set_file_items = solara.use_state([])

    def on_new_file(new_file_items: List[FileItem]):
        new_items = new_file_items + file_items
        set_file_items(new_items)

    # with solara.Sidebar():
    #     solara.Button("Submit", class_='ma-2', block=True)
    #     solara.FileDownload(label="Download", data=lambda *args: "howdoe", class_='ma-2', block=True)

    with solara.Card(title="Input files", subtitle="Add your input peptide table files") as card_input_files:
        NewFilesInput(on_new_file=on_new_file)

        list_items = []
        for idx, file_item in enumerate(file_items):

            def on_delete(idx=idx):
                new_items = file_items.copy()
                del new_items[idx]
                set_file_items(new_items)

            list_item = rv.ListItem(children = [
                rv.ListItemIcon(left=True, children=[rv.Icon(children=['mdi-file-delimited'])]),
                rv.ListItemTitle(children=[file_item.name]),
                rv.ListItemSubtitle(children=[f"{len(file_item.df)} peptides"]),
                solara.IconButton(color='primary', small=True, rounded=True, icon_name='mdi-delete', on_click=lambda *args: on_delete())
            ])
            list_items.append(list_item)

        rv.List(children=list_items)

    with solara.Card(title="Set global metadata", subtitle="Set metadata applying to all protein states"):
        solara.Markdown("Metadata can be overriden on a per-state basis in the next step.")

        solara.InputFloat(label="pH")
        solara.InputFloat(label="Temperature (C)")


    with solara.Card(title="Set global metadata", subtitle="Set metadata applying to all protein states"):

        # this should be some kind of component
        with solara.Column() as exp_column:
            with solara.Tooltip("Uncorrected pH as read with a pH meter"):
                solara.InputFloat(label="pH*")
            with solara.Tooltip("Temperature of the HD exchange reaction."):
                solara.InputFloat(label="Temperature (C).*")
            with solara.Tooltip("The percentage deuterium in the exchange buffer."):
                solara.InputFloat(label="Percentage deuterium.*")

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
            rv.ExpansionPanelContent(children=['Metadata relating to the protein of interest', protein_column])
        ])


        panels = rv.ExpansionPanels(children=[exp_panel, prot_panel])

    vepc1 = rv.ExpansionPanel(children=[
        rv.ExpansionPanelHeader(children=['item1']),
        rv.ExpansionPanelContent(children=['First Text'])])

    vep = rv.ExpansionPanels(children=[vepc1])

    with solara.Card(title="Define states", subtitle="Define protein states"):
        solara.Markdown("Placeholder")




