from pydantic import BaseModel
from typing import List


class OrganizationResult(BaseModel):
    """Информация об организации"""

    id: int


class SearchOrganizationResult(BaseModel):
    """Результат поиска организации по ИНН"""

    content: List[OrganizationResult]
