from typing import Callable, Any, List
from hdxms_datasets.web.file_input import FileInput, FileInfo
from hdxms_datasets.reader import read_dynamx

import dataclasses
import uuid


import solara
from solara.alias import rv
print('joe')


class FileItem():


@solara.component
def NewFilesInput(on_add: Callable[[Any], None]):

    success, set_success = solara.use_state(False)
    key, set_key = solara.use_state(str(uuid.uuid4()))

    def on_file(file_info: List[FileInfo]):
        if len(file_info) == 0:
            return
        else:
            try:
                file_items = []
                for file in file_info:
                    read_dynamx(file["file_obj"])
                    file_items.append(FileItem(file))

            df = pd.read_csv(file_info[0]["file_obj"])
            print(df)
            set_df(df)
        else:
            raise ValueError("Expected 1 file, got {}".format(len(file_info)))

    file_input = FileInput(accept=".csv", multiple=True, lazy=False, on_file=on_file).key(key)

    with solara.Row() as main:

        if success:
            rv.Icon(children="mdi-check-bold", color="success")
        else:
            rv.Icon(children="mdi-close", color="error")


@solara.component
def Page():



