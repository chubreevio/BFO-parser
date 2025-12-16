from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import CRUD
from app.db.organization.models import OrganizationModel


class OrganizationRepo:
    def __init__(self, session: AsyncSession):
        self._crud = CRUD(session=session, cls_model=OrganizationModel)
