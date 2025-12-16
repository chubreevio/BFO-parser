"""Middleware for creating db_session per-request."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logger import logger

SUCCESS_CODES = [200, 201, 204, 307]


class DbSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db_session = None
        try:
            db_session = request.app.state.db_session_factory()
            request.app.state.db_session = db_session
            response: Response = await call_next(request)

            if response.status_code in SUCCESS_CODES:
                await db_session.commit()
            else:
                await db_session.rollback()
            return response
        except Exception as ex:
            logger.error(str(ex))
            if db_session:
                await db_session.rollback()
            raise
        finally:
            # logger.info(f"Pool after: {request.app.state.db_engine.pool.checkedout()}")
            if db_session:
                await db_session.close()
