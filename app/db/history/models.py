from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional, Dict, Any

from app.db.sqlalchemy import Base


class HistoryModel(Base):
    __tablename__ = "history"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    inn: Mapped[str] = mapped_column(String(12), index=True)
    request_ip: Mapped[Optional[str]] = mapped_column(String(45))
    request_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    status_code: Mapped[int] = mapped_column(Integer)
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
