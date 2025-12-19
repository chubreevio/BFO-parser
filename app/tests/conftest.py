from asyncio import current_task
from typing import (
    AsyncGenerator,
    Callable,
)
from unittest.mock import AsyncMock
from fastapi import FastAPI
import httpx
import pytest
from sqlalchemy.pool.impl import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from app.startup import create_application
from app.settings import settings
from app.db.sqlalchemy import Base


AsyncSessionFactory = Callable[..., AsyncSession]


def make_url_async(url: str) -> str:
    """Add +asyncpg to url scheme."""
    return "postgresql+asyncpg" + url[url.find(":") :]  # noqa: WPS336


async def build_db_session_factory(engine: AsyncEngine) -> AsyncSessionFactory:
    await verify_db_connection(engine)

    return async_scoped_session(
        async_sessionmaker(bind=engine, expire_on_commit=False),
        scopefunc=current_task,
    )


async def verify_db_connection(engine: AsyncEngine) -> None:
    connection = await engine.connect()
    await connection.close()


@pytest.fixture
async def engine():

    _engine = create_async_engine(
        make_url_async(settings.TEST_POSTGRES_DSN), poolclass=AsyncAdaptedQueuePool
    )

    yield _engine

    await _engine.dispose()


@pytest.fixture
async def db_session(
    app: FastAPI, engine: AsyncEngine
) -> AsyncGenerator[AsyncSession, None]:

    # Создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    # Для тестов используем простой async_sessionmaker вместо async_scoped_session
    # чтобы избежать проблем с event loop
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    
    # Создаем фабрику, которая возвращает новую сессию для каждого запроса
    # но в тестах мы будем переопределять её в фикстуре client
    app.state.db_session_factory = await build_db_session_factory(engine)

    async with session_maker() as session:

        yield session

        # await session.rollback()

    # Удаление таблиц
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()


@pytest.fixture(scope="session")
async def app():
    fastapi_app = create_application()

    yield fastapi_app


@pytest.fixture
def mock_redis():
    """Мок для Redis пула."""
    mock_pool = AsyncMock()
    return mock_pool


@pytest.fixture
async def client(app: FastAPI, db_session: AsyncSession, mock_redis):
    """Асинхронный тестовый клиент для FastAPI."""
    # Создаем wrapper для сессии, который не закрывает сессию в тестах
    class TestSessionWrapper:
        def __init__(self, session: AsyncSession):
            self._session = session
            self._closed = False
        
        async def commit(self):
            return await self._session.commit()
        
        async def rollback(self):
            return await self._session.rollback()
        
        async def close(self):
            # Не закрываем сессию в тестах, она управляется фикстурой
            self._closed = True
        
        def __getattr__(self, name):
            return getattr(self._session, name)
    
    # Создаем фабрику, которая всегда возвращает обернутую сессию
    class TestSessionFactory:
        def __init__(self, session: AsyncSession):
            self._session = session
        
        def __call__(self):
            return TestSessionWrapper(self._session)
    
    app.state.db_session_factory = TestSessionFactory(db_session)
    app.state.redis = mock_redis
    
    # Используем ASGITransport для работы с FastAPI приложением
    from httpx import ASGITransport
    transport = ASGITransport(app)
    
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
