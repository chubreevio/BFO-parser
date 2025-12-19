import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


from app.logger import logger


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as ex:
            trace = []
            tb = ex.__traceback__
            while tb is not None:
                if tb.tb_frame.f_code.co_filename.startswith("/app/"):
                    trace.append(
                        {
                            "filename": tb.tb_frame.f_code.co_filename,
                            "name": tb.tb_frame.f_code.co_name,
                            "lineno": tb.tb_lineno,
                        }
                    )
                tb = tb.tb_next
            logger.error(
                json.dumps(
                    {"type": type(ex).__name__, "message": str(ex), "trace": trace},
                    sort_keys=True,
                    indent=4,
                )
            )
            raise
