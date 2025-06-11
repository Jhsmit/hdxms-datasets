# %%


from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Union
from ipymolstar import PDBeMolstar

# %%
root = Path(__file__).resolve().parent.parent
structure_file = Path(r"tests\datasets\1704204434_SecB_Krishnamurthy\data\1qyn.cif")
fpath = root / structure_file
# %%

# %%
custom_data = {
    "data": (root / structure_file).read_bytes(),
    "format": "cif",
    "binary": False,
}
view = PDBeMolstar(
    custom_data=custom_data,
    hide_water=True,
    hide_carbs=True,
)
view


# %%
@dataclass(frozen=True)
class StructureFile:
    name: str

    filepath_or_buffer: Union[Path, BytesIO]

    format: str

    extension: Optional[str] = None
    """File extension, e.g. .pdf, in case of a file-like object"""

    def pdbemolstar_custom_data(self):
        """
        Returns a dictionary with custom data for PDBeMolstar visualization.
        """

        if self.format in ["bcif"]:
            binary = True
        else:
            binary = False

        if isinstance(self.filepath_or_buffer, BytesIO):
            data = self.filepath_or_buffer.getvalue()
        elif isinstance(self.filepath_or_buffer, Path):
            if self.filepath_or_buffer.is_file():
                data = self.filepath_or_buffer.read_bytes()
            else:
                raise ValueError(f"Path {self.filepath_or_buffer} is not a file.")

        return {
            "data": data,
            "format": self.format,
            "binary": binary,
        }


bio = BytesIO(fpath.read_bytes())

data_file = StructureFile(
    name="1qyn",
    filepath_or_buffer=bio,
    format="cif",
    extension=".cif",
)

custom_data = data_file.pdbemolstar_custom_data()
view = PDBeMolstar(
    custom_data=custom_data,
    hide_water=True,
    hide_carbs=True,
)
view
# %%

data = [
    {"start_residue_number": 60, "end_residue_number": 70, "struct_asym_id": "F", "color": "red"},
]

data = [
    {
        "start_auth_residue_number": 60,
        "end_auth_residue_number": 70,
        "auth_asym_id": "G",
        "color": "red",
    },
]

color_data = {"data": data, "nonSelectedColor": "lightgray"}

view = PDBeMolstar(
    molecule_id="1cbw",
    color_data=color_data,
    hide_water=True,
    hide_carbs=True,
)
view
# %%
