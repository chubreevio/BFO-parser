import time
from typing import Optional
from asyncio_redis import Pool

# from app.logger import logger
from app.settings import settings


async def create_bfo_timeout_flag(redis: Pool) -> None:
    """
    Создание временного флага, обозначающего таймаут запросов к БФО

    :param redis: Подключение к redis
    """
    timestamp = str(int(time.time()))
    await redis.set(settings.REDIS_BFO_TIMEOUT_KEY, timestamp)
    await redis.expire(
        settings.REDIS_BFO_TIMEOUT_KEY, settings.REDIS_BFO_TIMEOUT_SECONDS
    )


async def bfo_timeout_left(redis: Pool) -> Optional[int]:
    """
    Сколько осталось таймаута для запросов к БФО

    :param redis: Подключение к redis

    :return: Оставшеесяя количество секунд или None(таймаута нет)
    """
    value = await redis.get(settings.REDIS_BFO_TIMEOUT_KEY)
    if value is None:
        return None
    return settings.REDIS_BFO_TIMEOUT_SECONDS - (int(time.time()) - int(value))
