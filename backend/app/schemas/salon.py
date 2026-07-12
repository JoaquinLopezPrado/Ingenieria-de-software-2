from pydantic import BaseModel, ConfigDict, Field, field_validator


def _capacity_must_be_positive(v: int) -> int:
    if v <= 0:
        raise ValueError("La capacidad debe ser un número entero mayor a 0.")
    return v


class CreateSalonRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    capacity: int

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v: int) -> int:
        return _capacity_must_be_positive(v)


class UpdateSalonRequest(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    capacity: int

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v: int) -> int:
        return _capacity_must_be_positive(v)


class SalonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int
    is_active: bool
