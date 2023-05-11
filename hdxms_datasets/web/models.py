
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class ExperimentMetadata(BaseModel):

    pH: Annotated[float, Field(le=14, ge=2., description="Uncorrected pH as read with a pH meter")] = 7.0

    # pint temperature ?
    temperature: Annotated[float, Field(ge=0., le=100,  title="Temperature (C)", description="Temperature of the HD exchange reaction.")] = 25.0

    d_percentage: Annotated[float, Field(ge=0., le=100., title="Deuterium Percentage", description="Percentage of D in the HD exchange reaction.")] = 90.


class POIMetadata(BaseModel):

    concentration: Annotated[Optional[float], Field(ge=0., title="Concentration", description="Concentration of the POI in the HD exchange reaction.")] = None

    oligomeric_state: Annotated[int, Field(ge=0., description="Oligomeric state of the POI.")] = 1

    pdb_id: Annotated[Optional[str], Field(min_length=4, max_length=4, description="PDB identifier of the POI.", title="PDB identifier")] = None