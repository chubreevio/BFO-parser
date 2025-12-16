from fastapi import Request, status
from fastapi.responses import JSONResponse
from asyncio import TimeoutError

from app.logger import logger


async def timeoutr_handler(request: Request, exc: TimeoutError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request.__dict__}: {exc_str}")
    content = {"message": exc_str}
    # TODO добавить запись в redis
    # logger.info(request.app.state.redis)
    return JSONResponse(content=content, status_code=status.HTTP_429_TOO_MANY_REQUESTS)
