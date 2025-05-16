from typing import Literal, Optional
from hdxms_datasets.formats import HDXFormat


import polars as pl


from dataclasses import dataclass, field


PEPTIDE_TYPES = [
    "partially_deuterated",
    "fully_deuterated",
    "non_deuterated",
]


@dataclass
class UploadFile:
    name: str
    format: HDXFormat
    dataframe: pl.DataFrame
    extension: str = ".csv"


@dataclass
class PeptideInfo:
    type: Literal["partially_deuterated", "fully_deuterated", "non_deuterated"] = (
        "partially_deuterated"
    )

    state: str | None = None
    filename: str | None = None
    exposure: str | float | None = None  # used for fd, nd
    exposure_values: list[float] | list[str] = field(default_factory=list)  # used for pd

    pH: Optional[float] = 7.5
    temperature: Optional[float] = 25.0
    d_percentage: Optional[float] = 90.0

    def validate(self) -> tuple[bool, str]:
        if self.state is None:
            return False, "State must be provided"
        if self.filename is None:
            return False, "Filename must be provided"
        if self.type not in PEPTIDE_TYPES:
            return False, f"Type must be one of {PEPTIDE_TYPES}"
        if self.pH is not None and (self.pH < 0 or self.pH > 14):
            return False, "pH must be between 0 and 14"
        if self.temperature is not None and (self.temperature < -273.15):
            return False, "Temperature cannot be below absolute zero"
        if self.d_percentage is not None and (self.d_percentage < 0 or self.d_percentage > 100):
            return False, "Deuteration percentage must be between 0 and 100"
        return True, ""
