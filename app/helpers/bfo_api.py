from typing import Dict, Any, Literal
from aiohttp import ClientSession
from asyncio_redis import Pool
from fastapi import HTTPException

from app.exceptions import BfoTooManyRequestsException
from app.helpers.decorators import check_bfo_timeout
from app.schemas.bfo_api import GetDetailsResult, SearchOrganizationResult
from app.settings import settings


def get_headers_for_bfo_request(headers: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Добавление User-Agent в заголовки для успешного запроса к БФО

    :param headers: Заголовки, которые необходимы для запроса

    :param: Словарь с добаленными заголовками
    """
    headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
    )
    return headers


@check_bfo_timeout
async def search_organization_by_inn(
    redis: Pool, session: ClientSession, inn: str
) -> SearchOrganizationResult:
    """
    Поиск организации по ИНН

    :param redis: Пул подключений к redis
    :param session: Сессия из aiohttp
    :param inn: ИНН организации

    :return: Модель результата поиска
    """
    url = f"{settings.BFO_URL}/advanced-search/organizations/search"
    params = {"query": inn, "page": 0, "size": 20}
    async with session.get(
        url,
        params=params,
        proxy=settings.PROXY_URL,
        headers=get_headers_for_bfo_request(),
    ) as response:
        if response.status == 429:
            raise BfoTooManyRequestsException(
                detail={"message": "Слишком много запросов"}
            )
        if response.status != 200:
            error = await response.text()
            raise HTTPException(status_code=response.status, detail={"message": error})
        result = await response.json()
        return SearchOrganizationResult.model_validate(result)


@check_bfo_timeout
async def get_details_by_organization_id(
    redis: Pool, session: ClientSession, organization_id: int
) -> GetDetailsResult:
    """
    Получение списка доступных отчётов

    :param redis: Пул подключений к redis
    :param session: Сессия из aiohttp
    :param organization_id: id организации

    :return: Модель результата поиска
    """
    url = f"{settings.BFO_URL}/nbo/organizations/{organization_id}/bfo"
    async with session.get(
        url, proxy=settings.PROXY_URL, headers=get_headers_for_bfo_request()
    ) as response:
        if response.status == 429:
            raise BfoTooManyRequestsException(
                detail={"message": "Слишком много запросов"}
            )
        if response.status != 200:
            error = await response.text()
            raise HTTPException(status_code=response.status, detail={"message": error})
        result = await response.json()
        return GetDetailsResult.model_validate(result)


@check_bfo_timeout
async def get_bfo_report(
    redis: Pool,
    session: ClientSession,
    organization_id: int,
    details_id: int,
    period: str,
    report_type: Literal["XLS", "WORD"] = "XLS",
) -> bytes:
    """
    Получение архива с отчётом

    :param redis: Пул подключений к redis
    :param session: Сессия из aiohttp
    :param organization_id: id организации
    :param details_id: id отчёта
    :param period: Год отчёта
    :param report_type: Формат отчета (xlsx или docx)

    :return: Архив с отчётом
    """
    url = f"{settings.BFO_URL}/download/bfo/{organization_id}"
    params = {
        "auditReport": False,
        "balance": True,
        "capitalChange": False,
        "clarification": False,
        "targetedFundsUsing": False,
        "detailsId": details_id,
        "financialResult": True,
        "fundsMovement": False,
        "type": report_type,
        "period": period,
    }
    async with session.get(
        url,
        params=params,
        proxy=settings.PROXY_URL,
        headers=get_headers_for_bfo_request(),
    ) as response:
        if response.status == 429:
            raise BfoTooManyRequestsException(
                detail={"message": "Слишком много запросов"}
            )
        if response.status != 200:
            error = await response.text()
            raise HTTPException(status_code=response.status, detail={"message": error})
        file_content = await response.read()
        return file_content
