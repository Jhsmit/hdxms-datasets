from typing import Literal, get_args
from hdxms_datasets.formats import HDXFormat


import polars as pl


from dataclasses import dataclass, field


PeptideType = Literal["partially_deuterated", "fully_deuterated", "non_deuterated"]
PEPTIDE_TYPES = list(get_args(PeptideType))


@dataclass
class UploadFile:
    name: str
    format: HDXFormat
    dataframe: pl.DataFrame
    extension: str = ".csv"

    @property
    def states(self) -> list[str]:
        return sorted(self.dataframe[self.format.state_name].unique().to_list())

    def get_exposures(self, state: str | None) -> list[str | float]:
        if state is None:
            df_f = self.dataframe
        else:
            df_f = self.dataframe.filter(pl.col(self.format.state_name) == state)
        return sorted(df_f[self.format.exposure_name].unique().to_list())


@dataclass
class PeptideMetaData:
    pH: float = 8.0
    temperature: float = 30.0
    d_percentage: float = 90.0


DEFAULT_METADATA = PeptideMetaData()


@dataclass
class PeptideInfo:
    type: PeptideType = "partially_deuterated"

    state: str | None = None
    filename: str | None = None
    exposure: str | float | None = None  # used for fd, nd
    exposure_values: list[float] | list[str] = field(default_factory=list)  # used for pd

    # values are ignored for fd, nd
    pH: float = DEFAULT_METADATA.pH
    temperature: float = DEFAULT_METADATA.temperature
    d_percentage: float = DEFAULT_METADATA.d_percentage

    def validate(self) -> tuple[bool, str]:
        if self.state is None:
            return False, "State must be provided"
        if self.filename is None:
            return False, "Filename must be provided"
        if self.state is None:
            return False, "State must be provided"
        if self.exposure is None and self.exposure_values is None:
            return False, "Exposure must be provided"
        if self.type not in PEPTIDE_TYPES:
            return False, f"Type must be one of {PEPTIDE_TYPES}"
        if self.pH is not None and (self.pH < 0 or self.pH > 14):
            return False, "pH must be between 0 and 14"
        if self.temperature is not None and (self.temperature < -273.15):
            return False, "Temperature cannot be below absolute zero"
        if self.d_percentage is not None and (self.d_percentage < 0 or self.d_percentage > 100):
            return False, "Deuteration percentage must be between 0 and 100"
        return True, ""

    def to_dict(self, format: HDXFormat):
        p_dict = {}
        p_dict["data_file"] = self.filename

        f_dict = {}
        f_dict[format.state_name] = self.state
        if self.exposure is not None:
            f_dict[format.exposure_name] = self.exposure
        elif self.exposure_values:
            f_dict[format.exposure_name] = self.exposure_values
        p_dict["filters"] = f_dict

        if self.type == "partially_deuterated":
            m_dict = {}
            m_dict["pH"] = self.pH
            m_dict["temperature"] = self.temperature
            m_dict["d_percentage"] = self.d_percentage
            p_dict["metadata"] = m_dict

        return p_dict
