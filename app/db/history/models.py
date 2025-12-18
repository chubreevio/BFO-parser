from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB

from app.db.sqlalchemy import Base


class HistoryModel(Base):
    __tablename__ = "history"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    request: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer)
    response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
