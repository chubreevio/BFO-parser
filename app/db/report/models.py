from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.db.sqlalchemy import Base
from app.db.organization.models import OrganizationModel


class ReportModel(Base):
    __tablename__ = "reports"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id")
    )
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    balance_sheet: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)
    financial_sheet: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)

    # relationships
    organization: Mapped["OrganizationModel"] = relationship(
        "OrganizationModel", lazy="select", foreign_keys=[organization_id]
    )
