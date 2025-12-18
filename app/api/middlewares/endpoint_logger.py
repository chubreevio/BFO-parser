"""Middleware for logging endpoint data"""

from datetime import datetime
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.history.repo import HistoryRepo
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
                # Тело ответа для логирования
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Логирование данных запроса
                filtered_scope = {}
                scope = request.scope
                for field in settings.REQUEST_LOGGING_ALLOWED_FILEDS:
                    if field in scope:
                        filtered_scope[field] = scope[field]

                # Логирование тела ответа
                try:
                    body = json.loads(response_body.decode("utf-8"))
                except:
                    body = None
                inn = request.query_params.get("inn", None)
                if inn is not None and body is not None:
                    history_repo = HistoryRepo(request.app.state.db_session)
                    await history_repo.create_history(
                        inn,
                        filtered_scope,
                        response.status_code,
                        body,
                        start,
                        end,
                        (
                            dict(request.query_params)
                            if request.query_params is not None
                            else None
                        ),
                    )

                # Ответ с новым итератором
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
        except Exception as ex:
            logger.error(f"Не удалось записать лог эндпоинта. ({ex})")
        return response
