from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.logger import logger


def value_error_handler(request: Request, exc: ValueError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request.__dict__}: {exc_str}")
    content = {"message": exc_str}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
