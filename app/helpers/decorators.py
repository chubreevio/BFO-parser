from fastapi import HTTPException

from app.helpers.redis import bfo_timeout_left


def check_bfo_timeout(func):
    """Декоратор для проверки таймаута запросов к БФО"""

    async def wrapper(*args, **kwargs):
        timeout = await bfo_timeout_left(args[0])
        if timeout is not None:
            raise HTTPException(
                status_code=429,
                detail={
                    "message": f"Слишком много запросов к БФО (таймаут {timeout} секунд)"
                },
            )
        return await func(*args, **kwargs)

    return wrapper
