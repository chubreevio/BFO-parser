from typing import Dict, Any, Tuple, Union
from aiohttp import ClientSession

from app.schemas.bfo_api import SearchOrganizationResult
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


async def search_organization_by_inn(
    session: ClientSession, inn: str
) -> Tuple[bool, Union[str, SearchOrganizationResult]]:
    """
    Поиск организации по ИНН

    :param session: Сессия из aiohttp
    :param inn: ИНН организации

    :return: Успшно или нет
    :return: Текст ошибки (если не успешно) модель результата поиска
    """
    # TODO добавить проверку из redis
    url = f"{settings.BFO_URL}/advanced-search/organizations/search"
    params = {"query": inn, "page": 0, "size": 20}
    async with session.get(
        url,
        params=params,
        proxy=settings.PROXY_URL,
        headers=get_headers_for_bfo_request(),
    ) as response:
        if response.status != 200:
            error = await response.text()
            return False, error
        result = await response.json()
        return True, SearchOrganizationResult.model_validate(result)
