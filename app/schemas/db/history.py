from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.db.history.models import HistoryModel


class History(BaseModel):
    """Схема истории запросов из БД"""

    id: int
    request: Dict[str, Any]
    status_code: int
    response: Dict[str, Any]
    started_at: datetime
    finished_at: datetime
    params: Dict[str, Any]

    @classmethod
    def from_orm_not_none(cls, history: HistoryModel) -> "History":
        return cls(
            id=history.id,
            request=history.request,
            status_code=history.status_code,
            response=history.response,
            started_at=history.started_at,
            finished_at=history.finished_at,
            params=history.params,
        )

    @classmethod
    def from_orm(cls, history: Optional[HistoryModel]) -> Optional["History"]:
        if history is None:
            return None
        return cls.from_orm_not_none(history)
