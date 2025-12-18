from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions import BfoTooManyRequestsException
from app.helpers.redis import create_bfo_timeout_flag
from app.logger import logger


async def bfo_too_many_requests_exception_handler(
    request: Request, exc: BfoTooManyRequestsException
):
    logger.error(exc.detail)
    # добавить запись в redis что сейчас таймаут
    await create_bfo_timeout_flag(request.app.state.redis)
    return JSONResponse(
        content=exc.detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS
    )
