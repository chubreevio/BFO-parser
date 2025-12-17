from typing import Any, Dict, List
from pydantic import BaseModel
from datetime import date, datetime


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
    periods: List[ReportForResponse]
