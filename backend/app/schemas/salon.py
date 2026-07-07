from pydantic import BaseModel, ConfigDict, Field


class CreateSalonRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    capacity: int = Field(gt=0)


class UpdateSalonRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    capacity: int = Field(gt=0)


class SalonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int
    is_active: bool
