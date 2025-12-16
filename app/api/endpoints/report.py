import aiohttp
from fastapi import APIRouter, Request, status, HTTPException, Query

from app.helpers.bfo_api import search_organization_by_inn
from app.logger import logger
from app.schemas.query_params import GetReportParams
from app.schemas.responses import GetReportResponse


router_v1 = APIRouter(prefix="/api/v1/report", tags=["v1"])


@router_v1.get(
    "",
    summary="Запрос на получение БФО отчёта организации",
    status_code=200,
    response_model=GetReportResponse,
)
async def get_report_handler(request: Request, params: GetReportParams = Query()):
    # logger.info(request.__dict__)
    if params.term is not None:
        try:
            params.periods = list(map(int, params.term.split(",")))
        except ValueError as ex:
            error_message = f"Ошибка валидации периодов. '{ex}'"
            logger.error(error_message)
            raise ValueError(error_message)
    logger.info(params)
    async with aiohttp.ClientSession() as session:
        is_success, organization_result = await search_organization_by_inn(
            session, params.inn
        )
        logger.info(is_success)
        logger.info(organization_result)
    return {}
