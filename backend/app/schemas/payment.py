from pydantic import BaseModel


class CreatePreferenceRequest(BaseModel):
    enrollment_id: int


class PreferenceResponse(BaseModel):
    init_point: str
