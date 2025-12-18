from typing import List, Optional, Dict, Any
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.crud import CRUD
from app.db.report.models import ReportModel
from app.schemas.bfo_api import DetailResult
from app.schemas.db.report import Report


class ReportRepo:
    def __init__(self, session: AsyncSession):
        self._crud = CRUD(session=session, cls_model=ReportModel)

    """CREATE"""

    async def create_report(
        self,
        organization_id: int,
        year: int,
        present_date: str,
        organization: Dict[str, Any],
        balance: Dict[str, Any],
        finance: Dict[str, Any],
    ) -> Report:
        """
        Создание записи организации в БД

        :param organization_id: id (из БФО) организации
        :param year: Год отчёта
        :param present_date: Дата предоставления отчёта
        :param organization: Данные об организации
        :param balance: Данные из бухгалтерского баланса
        :param finance: Данные из финансового отчёта

        :return: Модель отчёта
        """
        query = insert(ReportModel).values(
            organization_id=organization_id,
            report_year=year,
            present_date=present_date,
            organization_sheet=organization,
            balance_sheet=balance,
            financial_sheet=finance,
        )
        result = await self._crud._session.execute(query)
        query = select(ReportModel).where(id=result.inserted_primary_key)
        row = await self._crud._session.execute(query)
        return Report.from_orm_not_none(row.scalar_one())

    """READ"""

    async def get_reports_by_organization_id_and_period(
        self, organization_id: int, year: int
    ) -> List[Report]:
        """
        Поиск отчёта в БД

        :param organization_id: id организации
        :param year: За какой год отчётность

        :param: Список отчётов за указанный год
        """
        query = (
            select(ReportModel)
            .where(
                ReportModel.organization_id == organization_id,
                ReportModel.report_year == year,
            )
            .order_by(ReportModel.present_date)
        )
        rows = await self._crud._session.execute(query)
        return [Report.from_orm_not_none(row) for row in rows.scalars().all()]

    async def get_last_report_by_organization_id(
        self, organization_id: int
    ) -> Optional[Report]:
        """
        Получить последний отчёт организации (для проверки когда была последняя запись в БД)

        :param organization_id: id организации

        :return: Модель отчёта или None
        """
        query = (
            select(ReportModel)
            .where(ReportModel.organization_id == organization_id)
            .order_by(ReportModel.updated_at.desc())
            .limit(1)
        )
        row = await self._crud._session.execute(query)
        return Report.from_orm(row.scalar_one_or_none())

    async def get_max_reports_by_organization_id_and_period(
        self, organization_id: int
    ) -> List[Report]:
        """
        Найти последний отчёт организации (может быть несколько за один год)

        :param organization_id: id организации

        :param: Список отчётов за последний год
        """
        # подзапрос для поиска максимального года
        subquery = (
            select(func.max(ReportModel.report_year))
            .where(ReportModel.organization_id == organization_id)
            .scalar_subquery()
        )
        query = (
            select(ReportModel)
            .where(
                ReportModel.organization_id == organization_id,
                ReportModel.report_year == subquery,
            )
            .order_by(ReportModel.present_date)
        )
        rows = await self._crud._session.execute(query)
        return [Report.from_orm_not_none(row) for row in rows.scalars().all()]

    """UPDATE"""

    async def update_or_create_report_from_bfo(
        self, organization_id: int, details: List[DetailResult]
    ):
        """
        Обновить или создать отчёты в БД из результата запроса к БФО

        :param organization_id: id организации
        :param details: Список отчётов из БФО
        """
        for detail in details:
            for correction in detail.corrections:
                query = (
                    select(ReportModel)
                    .where(
                        ReportModel.organization_id == organization_id,
                        ReportModel.report_year == detail.period,
                        ReportModel.present_date == correction.date_present,
                    )
                    .limit(1)
                )
                row = await self._crud._session.execute(query)
                row = row.scalar_one_or_none()
                if row is None:
                    # отчёт не найден
                    query = insert(ReportModel).values(
                        organization_id=organization_id,
                        report_year=detail.period,
                        present_date=correction.date_present,
                        organization_sheet=correction.organization_info,
                        balance_sheet=correction.balance,
                        financial_sheet=correction.financial,
                    )
                    await self._crud._session.execute(query)
                else:
                    # обновляем данные у отчёта
                    row.organization_sheet = correction.organization_info
                    row.balance_sheet = correction.balance
                    row.financial_sheet = correction.financial
