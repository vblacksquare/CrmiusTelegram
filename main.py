
import asyncio

from telegram import run_telegram
from scheduler import run_cheduler

from db import Db
from dtypes.db import method as dmth
from dtypes.settings import Settings

from utils.logger import setup_logger

from config import get_config


async def main():
    config = get_config()

    setup_logger(config.logger.path, config.logger.level)

    db = Db()
    db.connect(config.database.name, config.database.uri)

    settings: Settings = await db.ex(dmth.GetOne(Settings))
    if not settings:
        settings = Settings()
        await db.ex(dmth.AddOne(Settings, settings))

    await run_cheduler()

    while True:
        await asyncio.sleep(1)

    #await run_telegram()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
