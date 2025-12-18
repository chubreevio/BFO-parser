from typing import Any, Dict, List, Optional
from datetime import date, datetime
from pydantic import BaseModel


class CorrectionForResponse(BaseModel):
    """Информация из отчёта БФО"""

    present_date: date
    updated_at: datetime
    organization_sheet: Dict[str, Any]
    balance_sheet: Dict[str, Any]
    financial_sheet: Dict[str, Any]


class ReportForResponse(BaseModel):
    """Список отчётов для указанного года"""

    year: int
    reports: List[CorrectionForResponse]


class GetReportResponse(BaseModel):
    """Успешный результат запроса на получение отчёта БФО"""

    inn: str
    short_name: str
    ogrn: str
    index: str
    region: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    settlement: Optional[str] = None
    street: Optional[str] = None
    house: Optional[str] = None
    building: Optional[str] = None
    office: Optional[str] = None
    periods: List[ReportForResponse]
