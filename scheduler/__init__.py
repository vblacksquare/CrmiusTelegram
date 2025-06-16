
from .cheduler import scheduler
from loguru import logger


async def run_cheduler():
    try:
        scheduler.start()
        logger.info(f"Started scheduler")

    except Exception as err:
        logger.exception(err)
