from contextlib import asynccontextmanager
from typing import AsyncIterator
import asyncio_redis
from alembic import command
from alembic.config import Config
from fastapi import FastAPI, HTTPException

from app.api.exception_handlers.bfo_api_exception_handler import (
    bfo_api_exception_handler,
)
from app.api.exception_handlers.bfo_too_many_requests_exception_handler import (
    bfo_too_many_requests_exception_handler,
)
from app.api.exception_handlers.value_error_handler import value_error_handler
from app.api.middlewares.db_session import DbSessionMiddleware
from app.api.middlewares.error_handler import ErrorHandlerMiddleware
from app.api.routers import router
from app.db.sqlalchemy import (
    build_db_session_factory,
    close_db_connections,
)
from app.exceptions import BfoApiException, BfoTooManyRequestsException
from app.logger import logger
from app.settings import settings

# 6612042431


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    # Startup logic
    logger.info("Запуск приложения")

    # -- Redis --

    redis_pool = await asyncio_redis.Pool.create(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, poolsize=1
    )
    fastapi_app.state.redis = redis_pool

    # -- Database --
    try:
        run_migrations()
    except Exception as ex:
        logger.error(f"Migration error: {ex}")

    fastapi_app.state.db_session_factory = await build_db_session_factory()

    yield

    # Shutdown logic
    logger.info("Отключение приложения")

    # -- Database --
    try:
        await close_db_connections()
    except Exception as ex:
        logger.error(f"Database disconnection error: {ex}")

    # -- Redis --
    try:
        async with redis_pool:
            await redis_pool.wait_closed()
    except Exception as ex:
        logger.error(f"Redis disconnection error: {ex}")


def create_application() -> FastAPI:
    """Create configured server application instance."""
    fastapi_app = FastAPI(title="bfo parser", lifespan=lifespan)

    # MIDDLEWARES
    fastapi_app.add_middleware(DbSessionMiddleware)
    fastapi_app.add_middleware(ErrorHandlerMiddleware)

    # EXCEPTION HANDLERS
    fastapi_app.add_exception_handler(ValueError, value_error_handler)
    fastapi_app.add_exception_handler(BfoApiException, bfo_api_exception_handler)
    fastapi_app.add_exception_handler(
        BfoTooManyRequestsException, bfo_too_many_requests_exception_handler
    )

    # API router
    fastapi_app.include_router(router)

    return fastapi_app


app = create_application()
