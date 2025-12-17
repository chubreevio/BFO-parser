from datetime import date
from typing import List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class OrganizationResult(BaseModel):
    """Информация об организации"""

    id: int


class SearchOrganizationResult(BaseModel):
    """Результат поиска организации по ИНН"""

    # content: List[OrganizationResult]
    id: int

    @model_validator(mode="before")
    @classmethod
    def get_last_correction(cls, data: Dict[str, Any]):
        try:
            data["id"] = data["content"][0]["id"]
        except:
            pass
        return data


class CorrectionResult(BaseModel):
    """Данные из отчёта"""

    id: int
    date_present: date = Field(alias="datePresent")
    requierd_audit: bool = Field(alias="requiredAudit")
    organization_info: Dict[str, Any] = Field(alias="bfoOrganizationInfo")
    balance: Dict[str, Any]
    financial: Dict[str, Any] = Field(alias="financialResult")

    @model_validator(mode="before")
    @classmethod
    def get_last_correction(cls, data: Dict[str, Any]):
        return data["correction"]


class DetailResult(BaseModel):
    """Информация об отчёте"""

    id: int
    period: int
    corrections: List[CorrectionResult] = Field(alias="typeCorrections")


class GetDetailsResult(BaseModel):
    """Результат поиска отчётов орагнизации"""

    reports: List[DetailResult]

    @model_validator(mode="before")
    @classmethod
    def wrap_list_to_dict(cls, data: List[Dict[str, Any]]) -> any:
        return {"reports": data}
