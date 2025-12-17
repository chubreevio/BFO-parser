import aiohttp
from datetime import datetime, timezone
from fastapi import APIRouter, Request, status, HTTPException, Query
from fastapi.responses import JSONResponse

from app.db.organization.repo import OrganizationRepo
from app.db.report.repo import ReportRepo
from app.helpers.bfo_api import (
    get_bfo_report,
    search_organization_by_inn,
    get_details_by_organization_id,
)
from app.logger import logger
from app.schemas.query_params import GetReportParams
from app.schemas.responses import GetReportResponse
from app.settings import settings


router_v1 = APIRouter(prefix="/api/v1/report", tags=["v1"])


@router_v1.get(
    "",
    summary="Запрос на получение БФО отчёта организации",
    status_code=200,
    response_model=GetReportResponse,
)
async def get_report_handler(request: Request, params: GetReportParams = Query()):
    logger.info(params)
    organization_repo = OrganizationRepo(request.app.state.db_session)
    report_repo = ReportRepo(request.app.state.db_session)
    # поиск организации в БД
    organization = await organization_repo.get_organization_by_inn(params.inn)
    logger.info(organization)
    result = {"inn": params.inn, "periods": []}
    async with aiohttp.ClientSession() as session:
        if organization is None:
            # создать запись об организации
            organization_result = await search_organization_by_inn(session, params.inn)
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
                session, organization.id
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
