from typing import Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel

from app.db.report.models import ReportModel


class Report(BaseModel):
    """Схема отчёта из БД"""

    id: int
    organization_id: int
    report_year: int
    present_date: date
    created_at: datetime
    updated_at: datetime
    organization_sheet: Optional[Dict[str, Any]]
    balance_sheet: Optional[Dict[str, Any]]
    financial_sheet: Optional[Dict[str, Any]]

    @classmethod
    def from_orm_not_none(cls, report: ReportModel) -> "Report":
        return cls(
            id=report.id,
            organization_id=report.organization_id,
            report_year=report.report_year,
            present_date=report.present_date,
            created_at=report.created_at,
            updated_at=report.updated_at,
            organization_sheet=report.organization_sheet,
            balance_sheet=report.balance_sheet,
            financial_sheet=report.financial_sheet,
        )

    @classmethod
    def from_orm(cls, report: Optional[ReportModel]) -> Optional["Report"]:
        if report is None:
            return None
        return cls.from_orm_not_none(report)
