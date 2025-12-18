from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import insert, null
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import CRUD
from app.db.history.models import HistoryModel


class HistoryRepo:
    def __init__(self, session: AsyncSession):
        self._crud = CRUD(session=session, cls_model=HistoryModel)

    """CREATE"""

    async def create_history(
        self,
        request: Dict[str, Any],
        status_code: int,
        response: Dict[str, Any],
        started_at: datetime,
        finished_at: datetime,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Создание записи в таблице логирования запросов к методу /api/v1/report

        :param request: Данные из request(отфильтрованные)
        :param status_code: Код ответа
        :param response: Тело ответа
        :param started_at: Время до запроса
        :param finished_at: Время после запроса
        :param params: Параметры запроса
        """
        query = insert(HistoryModel).values(
            request=request,
            status_code=status_code,
            response=response,
            started_at=started_at,
            finished_at=finished_at,
            params=params if params is not None else null(),
        )
        await self._crud._session.execute(query)
