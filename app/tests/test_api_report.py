"""Тесты для API эндпоинтов отчётов."""

from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch

import pytest
import httpx

from app.logger import logger
from app.schemas.bfo_api import (
    SearchOrganizationResult,
    GetDetailsResult,
    DetailResult,
    CorrectionResult,
)


@pytest.mark.asyncio
async def test_get_report_v1_new_organization_no_periods(
    client: httpx.AsyncClient, db_session, mock_redis
):
    """Тест v1: получение отчёта для новой организации без указания периодов."""
    inn = "1234567894"

    # Мокируем ответы от BFO API
    mock_search_result = SearchOrganizationResult.model_construct(
        id=12345,
        short_name="Test Organization",
        ogrn="1234567894123",
        index="123456",
        region="Test Region",
        city="Test City",
    )

    mock_details_result = GetDetailsResult.model_construct(
        reports=[
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
    )

    with patch(
        "app.api.endpoints.report.search_organization_by_inn",
        return_value=mock_search_result,
    ), patch(
        "app.api.endpoints.report.get_details_by_organization_id",
        return_value=mock_details_result,
    ):
        response = await client.get(f"/api/v1/report?inn={inn}")
    assert response.status_code == 200
    data = response.json()
    assert data["inn"] == inn
    assert data["short_name"] == "Test Organization"
    assert len(data["periods"]) == 1
    assert data["periods"][0]["year"] == 2023
    assert len(data["periods"][0]["reports"]) == 1


@pytest.mark.asyncio
async def test_get_report_v1_existing_organization_with_periods(
    client: httpx.AsyncClient, db_session, mock_redis
):
    """Тест v1: получение отчёта для существующей организации с указанием периодов."""
    from app.db.organization.repo import OrganizationRepo
    from app.db.report.repo import ReportRepo

    # Создаем организацию и отчёты
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345,
        "1234567894",
        {"short_name": "Test Org", "ogrn": "1234567894123", "index": "123123"},
    )

    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2022,
        present_date=date(2022, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 500000},
        finance={"revenue": 200000},
    )
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 1000000},
        finance={"revenue": 500000},
    )

    response = await client.get("/api/v1/report?inn=1234567894&term=2022,2023")

    assert response.status_code == 200
    data = response.json()
    assert data["inn"] == "1234567894"
    assert len(data["periods"]) == 2
    assert {p["year"] for p in data["periods"]} == {2022, 2023}


@pytest.mark.asyncio
async def test_get_report_v1_old_reports_trigger_update(
    client: httpx.AsyncClient, db_session, mock_redis
):
    """Тест v1: обновление старых отчётов (старше 7 дней)."""
    from app.db.organization.repo import OrganizationRepo
    from app.db.report.repo import ReportRepo
    from app.db.report.models import ReportModel
    from sqlalchemy import update

    # Создаем организацию и старый отчёт
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345,
        "1234567894",
        {"short_name": "Test Org", "ogrn": "1234567894123", "index": "123123"},
    )

    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 500000},
        finance={"revenue": 200000},
    )

    # Обновляем updated_at на 8 дней назад
    old_date = datetime.now(timezone.utc) - timedelta(days=8)
    await db_session.execute(
        update(ReportModel)
        .where(ReportModel.organization_id == organization.id)
        .values(updated_at=old_date)
    )
    await db_session.commit()

    # Мокируем ответ от BFO API
    mock_details_result = GetDetailsResult.model_construct(
        reports=[
            DetailResult.model_construct(
                id=1,
                period=2023,
                corrections=[
                    CorrectionResult.model_construct(
                        id=1,
                        date_present=date(2023, 12, 31),
                        requierd_audit=False,
                        organization_info={"name": "Updated Org"},
                        balance={"assets": 2000000},
                        financial={"revenue": 1000000},
                    )
                ],
            )
        ]
    )

    with patch(
        "app.api.endpoints.report.get_details_by_organization_id",
        return_value=mock_details_result,
    ):
        response = await client.get("/api/v1/report?inn=1234567894")

    assert response.status_code == 200
    data = response.json()
    assert len(data["periods"]) == 1
    assert (
        data["periods"][0]["reports"][0]["organization_sheet"]["name"] == "Updated Org"
    )


@pytest.mark.asyncio
async def test_get_report_v2_new_organization_no_periods(
    client: httpx.AsyncClient, db_session, mock_redis
):
    """Тест v2: получение отчёта для новой организации без указания периодов."""
    inn = "1234567894"

    # Мокируем ответы от BFO API
    mock_search_result = SearchOrganizationResult.model_construct(
        id=12345,
        short_name="Test Organization",
        ogrn="1234567894123",
        index="123456",
    )

    mock_details_result = GetDetailsResult.model_construct(
        reports=[
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
    )

    with patch(
        "app.api.endpoints.report.search_organization_by_inn",
        return_value=mock_search_result,
    ), patch(
        "app.api.endpoints.report.get_details_by_organization_id",
        return_value=mock_details_result,
    ):
        response = await client.get(f"/api/v2/report?inn={inn}")

    assert response.status_code == 200
    data = response.json()
    assert data["inn"] == inn
    assert len(data["periods"]) == 1
    assert data["periods"][0]["year"] == 2023


@pytest.mark.asyncio
async def test_get_report_v2_existing_organization_with_periods(
    client: httpx.AsyncClient, db_session, mock_redis
):
    """Тест v2: получение отчёта для существующей организации с указанием периодов."""
    from app.db.organization.repo import OrganizationRepo
    from app.db.report.repo import ReportRepo

    # Создаем организацию и отчёты
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345,
        "1234567894",
        {"short_name": "Test Org", "ogrn": "1234567894123", "index": "123123"},
    )

    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2022,
        present_date=date(2022, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 500000},
        finance={"revenue": 200000},
    )
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 1000000},
        finance={"revenue": 500000},
    )

    response = await client.get("/api/v2/report?inn=1234567894&term=2022,2023")

    assert response.status_code == 200
    data = response.json()
    assert data["inn"] == "1234567894"
    assert len(data["periods"]) == 2
    assert {p["year"] for p in data["periods"]} == {2022, 2023}


@pytest.mark.asyncio
async def test_get_report_v2_missing_periods_trigger_update(
    client: httpx.AsyncClient, db_session, mock_redis
):
    """Тест v2: обновление при отсутствии отчётов за указанные периоды."""
    from app.db.organization.repo import OrganizationRepo
    from app.db.report.repo import ReportRepo

    # Создаем организацию с отчётом только за 2022 год
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345,
        "1234567894",
        {"short_name": "Test Org", "ogrn": "1234567894123", "index": "123123"},
    )

    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2022,
        present_date=date(2022, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 500000},
        finance={"revenue": 200000},
    )

    # Мокируем ответ от BFO API с отчётами за 2022 и 2023
    mock_details_result = GetDetailsResult.model_construct(
        reports=[
            DetailResult.model_construct(
                id=1,
                period=2022,
                corrections=[
                    CorrectionResult.model_construct(
                        id=1,
                        date_present=date(2022, 12, 31),
                        requierd_audit=False,
                        organization_info={"name": "Test Org"},
                        balance={"assets": 500000},
                        financial={"revenue": 200000},
                    )
                ],
            ),
            DetailResult.model_construct(
                id=2,
                period=2023,
                corrections=[
                    CorrectionResult.model_construct(
                        id=2,
                        date_present=date(2023, 12, 31),
                        requierd_audit=False,
                        organization_info={"name": "Test Org"},
                        balance={"assets": 1000000},
                        financial={"revenue": 500000},
                    )
                ],
            ),
        ]
    )

    with patch(
        "app.api.endpoints.report.get_details_by_organization_id",
        return_value=mock_details_result,
    ):
        response = await client.get("/api/v2/report?inn=1234567894&term=2022,2023")

    assert response.status_code == 200
    data = response.json()
    assert len(data["periods"]) == 2
    # Проверяем, что отчёт за 2023 год был добавлен
    periods = {p["year"] for p in data["periods"]}
    assert 2022 in periods
    assert 2023 in periods


@pytest.mark.asyncio
async def test_get_report_v2_old_reports_trigger_update(
    client: httpx.AsyncClient, db_session, mock_redis
):
    """Тест v2: обновление старых отчётов (старше 7 дней)."""
    from app.db.organization.repo import OrganizationRepo
    from app.db.report.repo import ReportRepo
    from app.db.report.models import ReportModel
    from sqlalchemy import update

    # Создаем организацию и старый отчёт
    org_repo = OrganizationRepo(db_session)
    organization = await org_repo.create_organization(
        12345,
        "1234567894",
        {"short_name": "Test Org", "ogrn": "1234567894123", "index": "123123"},
    )

    report_repo = ReportRepo(db_session)
    await report_repo.create_report(
        organization_id=organization.id,
        year=2023,
        present_date=date(2023, 12, 31),
        organization={"name": "Test Org"},
        balance={"assets": 500000},
        finance={"revenue": 200000},
    )

    # Обновляем updated_at на 8 дней назад
    old_date = datetime.now(timezone.utc) - timedelta(days=8)
    await db_session.execute(
        update(ReportModel)
        .where(ReportModel.organization_id == organization.id)
        .values(updated_at=old_date)
    )
    await db_session.commit()

    # Мокируем ответ от BFO API
    mock_details_result = GetDetailsResult.model_construct(
        reports=[
            DetailResult.model_construct(
                id=1,
                period=2023,
                corrections=[
                    CorrectionResult.model_construct(
                        id=1,
                        date_present=date(2023, 12, 31),
                        requierd_audit=False,
                        organization_info={"name": "Updated Org"},
                        balance={"assets": 2000000},
                        financial={"revenue": 1000000},
                    )
                ],
            )
        ]
    )

    with patch(
        "app.api.endpoints.report.get_details_by_organization_id",
        return_value=mock_details_result,
    ):
        response = await client.get("/api/v2/report?inn=1234567894")

    assert response.status_code == 200
    data = response.json()
    assert len(data["periods"]) == 1
    assert (
        data["periods"][0]["reports"][0]["organization_sheet"]["name"] == "Updated Org"
    )


@pytest.mark.asyncio
async def test_get_report_invalid_inn(client: httpx.AsyncClient):
    """Тест валидации ИНН."""
    response = await client.get("/api/v1/report?inn=123")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_report_invalid_period(client: httpx.AsyncClient):
    """Тест валидации периода."""
    response = await client.get("/api/v1/report?inn=1234567894&term=1800")

    assert response.status_code == 422  # Validation error
