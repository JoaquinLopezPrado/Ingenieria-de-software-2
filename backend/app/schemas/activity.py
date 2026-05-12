from pydantic import BaseModel, ConfigDict, Field


class CreateActivityRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    instructor: str = Field(min_length=1, max_length=200)


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    instructor: str
    is_active: bool
