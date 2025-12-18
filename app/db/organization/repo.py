from typing import Any, Dict, Optional
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import CRUD
from app.db.organization.models import OrganizationModel
from app.schemas.db.organization import Organization


class OrganizationRepo:
    """Репозиторий для работы с таблицей organizations"""

    def __init__(self, session: AsyncSession):
        self._crud = CRUD(session=session, cls_model=OrganizationModel)

    """CREATE"""

    async def create_organization(
        self, organization_id: int, inn: str, info: Dict[str, Any]
    ) -> Organization:
        """
        Создание записи организации в БД

        :param organization_id: id (из БФО) организации
        :param inn: Строка с ИНН организации

        :return: Модель организации
        """
        query = insert(OrganizationModel).values(id=organization_id, inn=inn, info=info)
        await self._crud._session.execute(query)
        query = select(OrganizationModel).where(OrganizationModel.id == organization_id)
        row = await self._crud._session.execute(query)
        return Organization.from_orm_not_none(row.scalar_one())

    """READ"""

    async def get_organization_by_inn(self, inn: str) -> Optional[Organization]:
        """
        Поиск организации по ИНН

        :param inn: Строка с ИНН организации

        :return: Модель организации или None
        """
        query = select(OrganizationModel).where(OrganizationModel.inn == inn)
        row = await self._crud._session.execute(query)
        return Organization.from_orm(row.scalar_one_or_none())
