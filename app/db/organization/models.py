from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import String, DateTime, Integer

from app.db.sqlalchemy import Base


class OrganizationModel(Base):
    __tablename__ = "organizations"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, unique=True, autoincrement=False
    )
    inn: Mapped[str] = mapped_column(String(12), nullable=False, index=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
