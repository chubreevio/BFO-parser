from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.organization.models import OrganizationModel


class Organization(BaseModel):
    """Схема организации из БД"""

    id: int
    inn: str
    created_at: datetime

    @classmethod
    def from_orm_not_none(cls, organization: OrganizationModel) -> "Organization":
        return cls(
            id=organization.id, inn=organization.inn, created_at=organization.created_at
        )

    @classmethod
    def from_orm(
        cls, organization: Optional[OrganizationModel]
    ) -> Optional["Organization"]:
        if organization is None:
            return None
        return cls.from_orm_not_none(organization)
