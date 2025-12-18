from datetime import datetime, timezone
import aiohttp
from fastapi import APIRouter, Request, Query

from app.db.organization.repo import OrganizationRepo
from app.db.report.repo import ReportRepo
from app.helpers.bfo_api import (
    search_organization_by_inn,
    get_details_by_organization_id,
)
from app.logger import logger
from app.schemas.query_params import GetReportParams
from app.schemas.responses import GetReportResponse
from app.settings import settings


router_v1 = APIRouter(prefix="/api/v1/report", tags=["v1"])
router_v2 = APIRouter(prefix="/api/v2/report", tags=["v2"])


@router_v1.get(
    "",
    summary="Запрос на получение БФО отчёта организации",
    description="Если есть год, у которого нет отчёта в БД, но есть другие отчёты (не старше 7 дней), то запрос к БФО не делается",
    status_code=200,
    response_model=GetReportResponse,
)
async def get_report_handler(request: Request, params: GetReportParams = Query()):
    organization_repo = OrganizationRepo(request.app.state.db_session)
    report_repo = ReportRepo(request.app.state.db_session)
    # поиск организации в БД
    organization = await organization_repo.get_organization_by_inn(params.inn)
    result = {"inn": params.inn, "periods": []}
    async with aiohttp.ClientSession() as session:
        if organization is None:
            # создать запись об организации
            organization_result = await search_organization_by_inn(
                request.app.state.redis, session, params.inn
            )
            organization = await organization_repo.create_organization(
                organization_result.id, params.inn
            )
        # найти дату последнего отчёта для этой организации
        last_report = await report_repo.get_last_report_by_organization_id(
            organization.id
        )
        if (
            last_report is None
            or (datetime.now(timezone.utc) - last_report.updated_at).days
            > settings.REPORT_AVAILABLE_DAYS
        ):
            # отчётов по организации еще не было или они старые
            organization_details = await get_details_by_organization_id(
                request.app.state.redis, session, organization.id
            )
            await report_repo.update_or_create_report_from_bfo(
                organization.id, organization_details.reports
            )
        if params.periods is None:
            # Нужен отчёт за последний год
            reports = await report_repo.get_max_reports_by_organization_id(
                organization.id
            )
            if len(reports) > 0:
                result["periods"].append(
                    {"year": reports[0].report_year, "reports": reports}
                )
        else:
            for period in params.periods:
                # для каждого указанного года найдем отчёты за год
                reports = await report_repo.get_reports_by_organization_id_and_period(
                    organization.id, period
                )
                result["periods"].append({"year": period, "reports": reports})
    return result


@router_v2.get(
    "",
    summary="Запрос на получение БФО отчёта организации",
    description="Если есть год, у которого нет отчёта в БД -> делается запрос к БФО для обновления отчётов",
    status_code=200,
    response_model=GetReportResponse,
)
async def get_report_v2_handler(request: Request, params: GetReportParams = Query()):
    organization_repo = OrganizationRepo(request.app.state.db_session)
    report_repo = ReportRepo(request.app.state.db_session)
    # поиск организации в БД
    organization = await organization_repo.get_organization_by_inn(params.inn)
    result = {"inn": params.inn, "periods": []}
    async with aiohttp.ClientSession() as session:
        if organization is None:
            # создать запись об организации
            organization_result = await search_organization_by_inn(
                request.app.state.redis, session, params.inn
            )
            organization = await organization_repo.create_organization(
                organization_result.id, params.inn
            )
        if params.periods is None:
            # Отправить последний отчёт
            reports = await report_repo.get_max_reports_by_organization_id(
                organization.id
            )
            if (
                len(reports) == 0
                or (datetime.now(timezone.utc) - reports[0].updated_at).days
                > settings.REPORT_AVAILABLE_DAYS
            ):
                # необходимо обновить отчёт
                organization_details = await get_details_by_organization_id(
                    request.app.state.redis, session, organization.id
                )
                await report_repo.update_or_create_report_from_bfo(
                    organization.id, organization_details.reports
                )
                reports = await report_repo.get_max_reports_by_organization_id(
                    organization.id
                )
            result["periods"].append(
                {"year": reports[0].report_year, "reports": reports}
            )
        else:
            # указаны конкретные периоды
            non_available_periods = await report_repo.is_all_periods_available(
                organization.id, params.periods
            )
            logger.info(non_available_periods)
            if len(non_available_periods) > 0:
                # есть отчёты, которые нужно обновить
                organization_details = await get_details_by_organization_id(
                    request.app.state.redis, session, organization.id
                )
                await report_repo.update_or_create_report_from_bfo(
                    organization.id, organization_details.reports
                )
            for period in params.periods:
                # для каждого указанного года найдем отчёты за год
                reports = await report_repo.get_reports_by_organization_id_and_period(
                    organization.id, period
                )
                result["periods"].append({"year": period, "reports": reports})

    return result
