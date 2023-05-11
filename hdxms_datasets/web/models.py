
from typing import Annotated

from pydantic import BaseModel, Field


class ExperimentMetadata(BaseModel):

    pH: Annotated[float, Field(le=14, ge=2., description="Uncorrected pH as read with a pH meter")] = 7.0

    # pint temperature ?
    temperature: Annotated[float, Field(ge=0., le=100,  title="Temperature (C)", description="Temperature of the HD exchange reaction.")] = 25.0

    d_percentage: Annotated[float, Field(ge=0., le=100., title="Deuterium Percentage", description="Percentage of D in the HD exchange reaction.")] = 90.