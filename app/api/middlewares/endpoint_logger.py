"""Middleware for logging endpoint data"""

from datetime import datetime
import json
from typing import Optional
from fastapi import Request, Response
from fastapi.datastructures import QueryParams
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Scope

from app.db.history.repo import HistoryRepo
from app.db.sqlalchemy import AsyncSessionFactory
from app.logger import logger
from app.settings import settings


class EndpointLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = datetime.now()
        response: Response = await call_next(request)
        end = datetime.now()
        try:
            if (
                f"{request.scope['method']}:{request.scope['path']}"
                in settings.REQUEST_LOGGING_MIDDLEWARE_ENDPOINTS
            ):

                async def log_endpoint_info_task(
                    db_session_factory: AsyncSessionFactory,
                    scope: Scope,
                    status_code: int,
                    response_body: bytes,
                    query_params: Optional[QueryParams] = None,
                ):
                    db_session = db_session_factory()
                    try:
                        # Логирование данных запроса
                        filtered_scope = {}
                        for field in settings.REQUEST_LOGGING_ALLOWED_FILEDS:
                            if field in scope:
                                filtered_scope[field] = scope[field]
                        body = json.loads(response_body.decode("utf-8"))
                        inn = query_params.get("inn", None)
                        if inn is not None and body is not None:
                            history_repo = HistoryRepo(db_session)
                            await history_repo.create_history(
                                inn,
                                filtered_scope,
                                status_code,
                                body,
                                start,
                                end,
                                (
                                    dict(query_params)
                                    if query_params is not None
                                    else None
                                ),
                            )
                            await db_session.commit()
                    except Exception as ex:
                        logger.error(f"Не удалось сохрнаить лог запроса. ({ex})")
                        if db_session:
                            await db_session.rollback()
                    finally:
                        if db_session:
                            await db_session.close()

                # Тело ответа для логирования
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Создание фоновой задачи
                response.background = BackgroundTask(
                    log_endpoint_info_task,
                    request.app.state.db_session_factory,
                    request.scope,
                    response.status_code,
                    response_body,
                    request.query_params,
                )
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                    background=response.background,
                )

        except Exception as ex:
            logger.error(
                f"Не удалось создать задачу для сохранения лога эндпоинта. ({ex})"
            )
        return response
