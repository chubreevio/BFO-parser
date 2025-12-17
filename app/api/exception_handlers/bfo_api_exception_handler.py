from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import BfoApiException
from app.logger import logger


def bfo_api_exception_handler(exc: BfoApiException):
    logger.error(exc.detail)
    return JSONResponse(content=exc.detail, status_code=exc.status_code)
