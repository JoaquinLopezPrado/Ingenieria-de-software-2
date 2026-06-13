from pydantic import BaseModel


class CreatePreferenceRequest(BaseModel):
    enrollment_id: int


class PreferenceResponse(BaseModel):
    init_point: str


class MpStatusResponse(BaseModel):
    status_detail: str | None


class CancelDepositResponse(BaseModel):
    refund: bool
    refund_id: str | None = None
