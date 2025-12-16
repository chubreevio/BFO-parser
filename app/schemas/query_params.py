from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class GetReportParams(BaseModel):
    """Параметры для получения отчёта"""

    inn: str = Field(..., description="ИНН организации")
    term: Optional[str] = Field(
        None, description="Периоды для отчётов", example="2019,2020"
    )
    periods: Optional[List[int]] = Field(None, exclude=True)

    @field_validator("inn", mode="before")
    @classmethod
    def validate_field_validator(cls, inn: str) -> str:
        """Проверка валидности ИНН"""

        return inn
