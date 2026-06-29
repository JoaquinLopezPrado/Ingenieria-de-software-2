from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CreateActivityRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)


class UpdateActivityRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    is_active: bool


class ClaseDiaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    turno_id: int
    date: date
    capacity: int
    is_active: bool
