from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

from app.helpers.functions import validate_inn


class GetReportParams(BaseModel):
    """Параметры для получения отчёта"""

    inn: str = Field(..., description="ИНН организации")
    term: Optional[str] = Field(
        None, description="Периоды для отчётов", example="2019,2020"
    )
    periods: Optional[List[int]] = Field(None, exclude=True)

    @field_validator("inn", mode="before")
    @classmethod
    def inn_field_validator(cls, inn: str) -> str:
        """Проверка валидности ИНН"""
        is_success, result = validate_inn(inn)
        if is_success is False:
            raise ValueError(result)
        return result

    @model_validator(mode="before")
    @classmethod
    def validate_params(cls, data: Dict[str, Any]):
        """Проверка валидности периодов и преобразование строки в список годов"""
        if data.get("term", None) is not None:
            periods = []
            for year_str in data["term"].split(","):
                year = int(year_str)
                if year < 1990 or year > date.today().year:
                    raise ValueError(f"Невалидный год {year}")
                periods.append(year)
            data["periods"] = list(set(periods))
        return data
