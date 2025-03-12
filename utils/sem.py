
from asyncio import Semaphore
import functools

from loguru import logger as log

from config import BEHANCE_CONCURRENT


sem = Semaphore(BEHANCE_CONCURRENT)


def to_semaphore():
    def wrapper(func):

        @functools.wraps(func)
        async def wrapped(*args):
            async with sem:
                try:
                    return await func(*args)

                except Exception as err:
                    log.exception(err)
                    return None

        return wrapped

    return wrapper
