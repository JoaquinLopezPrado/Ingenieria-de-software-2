from datetime import date

from pydantic import field_validator, model_validator

from app.schemas.auth import RegisterClientRequest


class CreateClientByStaffRequest(RegisterClientRequest):
    """Alta de cliente hecha por un admin/empleado.

    A diferencia del autoregistro público, permite cargar un cliente menor de
    edad si se marca ``presento_permiso`` (el permiso se presentó en persona).
    """
    presento_permiso: bool = False

    @field_validator("birth_date")
    @classmethod
    def validate_age(cls, v: date) -> date:
        # La validación de edad real se hace en check_age_or_permission (mode="after"),
        # que además tiene en cuenta presento_permiso. Este override anula el chequeo
        # incondicional de RegisterClientRequest.
        return v

    @model_validator(mode="after")
    def check_age_or_permission(self) -> "CreateClientByStaffRequest":
        today = date.today()
        age = today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
        if age < 18 and not self.presento_permiso:
            raise ValueError(
                "El cliente es menor de edad: marcá 'Presento Permiso' para continuar."
            )
        return self
