"""Тесты для репозиториев."""
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.organization.repo import OrganizationRepo
from app.db.report.repo import ReportRepo
from app.schemas.bfo_api import DetailResult, CorrectionResult


@pytest.mark.asyncio
async def test_organization_repo_create_organization(db_session: AsyncSession):
    """Тест создания организации."""
    repo = OrganizationRepo(db_session)
    
    organization_id = 12345
    inn = "1234567894"
    info = {
        "short_name": "Test Org",
        "ogrn": "1234567894123",
        "index": "123456",
    }
    
    organization = await repo.create_organization(organization_id, inn, info)
    
    assert organization.id == organization_id
    assert organization.inn == inn
    assert organization.info == info
    assert organization.created_at is not None


@pytest.mark.asyncio
async def test_organization_repo_get_organization_by_inn_existing(
    db_session: AsyncSession
):
    """Тест получения организации по ИНН (организация существует)."""
    repo = OrganizationRepo(db_session)
    
    organization_id = 12345
    inn = "1234567894"
    info = {"short_name": "Test Org", "ogrn": "1234567894123"}
    
    # Создаем организацию
    await repo.create_organization(organization_id, inn, info)
    
    # Получаем организацию
    organization = await repo.get_organization_by_inn(inn)
    
    assert organization is not None
    assert organization.id == organization_id
    assert organization.inn == inn


@pytest.mark.asyncio
async def test_organization_repo_get_organization_by_inn_not_existing(
    db_session: AsyncSession
):
    """Тест получения организации по ИНН (организация не существует)."""
    repo = OrganizationRepo(db_session)
    
    organization = await repo.get_organization_by_inn("9999999998")
    
    assert organization is None


@pytest.mark.asyncio
async def test_report_repo_create_report(db_session: AsyncSession):
    """Тест создания отчёта."""
    # Сначала создаем организацию
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345, "1234567894", {"short_name": "Test Org"}
    )
    
    # Создаем отчёт
    report_repo = ReportRepo(db_session)
    report = await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 1000000},
        finance={"revenue": 500000},
    )
    
    assert report.organization_id == organization.id
    assert report.report_year == 2023
    assert report.present_date == date(2023, 12, 31)
    assert report.organization_sheet == {"name": "Test Org"}
    assert report.balance_sheet == {"assets": 1000000}
    assert report.financial_sheet == {"revenue": 500000}


@pytest.mark.asyncio
async def test_report_repo_get_reports_by_organization_id_and_period(
    db_session: AsyncSession
):
    """Тест получения отчётов по организации и периоду."""
    # Создаем организацию
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345, "1234567894", {"short_name": "Test Org"}
    )
    
    # Создаем отчёты
    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={},
        balance={},
        finance={},
    )
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 6, 30),
        organization={},
        balance={},
        finance={},
    )
    await report_repo.create_report(
        organization_id=organization.id,
        year=2022,
        present_date=date(2022, 12, 31),
        organization={},
        balance={},
        finance={},
    )
    
    # Получаем отчёты за 2023 год
    reports = await report_repo.get_reports_by_organization_id_and_period(
        organization.id, 2023
    )
    
    assert len(reports) == 2
    assert all(r.report_year == 2023 for r in reports)
    # Проверяем сортировку по дате
    assert reports[0].present_date <= reports[1].present_date


@pytest.mark.asyncio
async def test_report_repo_get_max_reports_by_organization_id(
    db_session: AsyncSession
):
    """Тест получения отчётов за последний год."""
    # Создаем организацию
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345, "1234567894", {"short_name": "Test Org"}
    )
    
    # Создаем отчёты
    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2022,
        present_date=date(2022, 12, 31),
        organization={},
        balance={},
        finance={},
    )
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 6, 30),
        organization={},
        balance={},
        finance={},
    )
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={},
        balance={},
        finance={},
    )
    
    # Получаем отчёты за последний год
    reports = await report_repo.get_max_reports_by_organization_id(organization.id)
    
    assert len(reports) == 2
    assert all(r.report_year == 2023 for r in reports)


@pytest.mark.asyncio
async def test_report_repo_is_all_periods_available(db_session: AsyncSession):
    """Тест проверки доступности периодов."""
    # Создаем организацию
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345, "1234567894", {"short_name": "Test Org"}
    )
    
    # Создаем отчёт за 2023 год
    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={},
        balance={},
        finance={},
    )
    
    # Проверяем доступность периодов
    non_available = await report_repo.is_all_periods_available(
        organization.id, [2022, 2023, 2024]
    )
    
    # 2023 должен быть доступен, 2022 и 2024 - нет
    assert 2022 in non_available
    assert 2023 not in non_available
    assert 2024 in non_available


@pytest.mark.asyncio
async def test_report_repo_update_or_create_report_from_bfo(
    db_session: AsyncSession
):
    """Тест обновления или создания отчётов из БФО."""
    # Создаем организацию
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345, "1234567894", {"short_name": "Test Org"}
    )
    
    # Создаем данные из БФО
    details = [
        DetailResult.model_construct(
            id=1,
            period=2023,
            corrections=[
                CorrectionResult.model_construct(
                    id=1,
                    date_present=date(2023, 12, 31),
                    requierd_audit=False,
                    organization_info={"name": "Test Org"},
                    balance={"assets": 1000000},
                    financial={"revenue": 500000},
                )
            ],
        )
    ]
    
    report_repo = ReportRepo(db_session)
    await report_repo.update_or_create_report_from_bfo(organization.id, details)
    
    # Проверяем, что отчёт создан
    reports = await report_repo.get_reports_by_organization_id_and_period(
        organization.id, 2023
    )
    
    assert len(reports) == 1
    assert reports[0].report_year == 2023
    assert reports[0].present_date == date(2023, 12, 31)
    assert reports[0].organization_sheet == {"name": "Test Org"}


@pytest.mark.asyncio
async def test_report_repo_update_existing_report_from_bfo(
    db_session: AsyncSession
):
    """Тест обновления существующего отчёта из БФО."""
    # Создаем организацию
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345, "1234567894", {"short_name": "Test Org"}
    )
    
    # Создаем отчёт
    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={"name": "Old Name"},
        balance={"assets": 500000},
        finance={"revenue": 200000},
    )
    
    # Обновляем отчёт из БФО
    details = [
        DetailResult.model_construct(
            id=1,
            period=2023,
            corrections=[
                CorrectionResult.model_construct(
                    id=1,
                    date_present=date(2023, 12, 31),
                    requierd_audit=False,
                    organization_info={"name": "New Name"},
                    balance={"assets": 1000000},
                    financial={"revenue": 500000},
                )
            ],
        )
    ]
    
    await report_repo.update_or_create_report_from_bfo(organization.id, details)
    
    # Проверяем, что отчёт обновлён
    reports = await report_repo.get_reports_by_organization_id_and_period(
        organization.id, 2023
    )
    
    assert len(reports) == 1
    assert reports[0].organization_sheet == {"name": "New Name"}
    assert reports[0].balance_sheet == {"assets": 1000000}

