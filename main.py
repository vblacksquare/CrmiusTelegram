
import asyncio

from telegram import run_telegram
from scheduler import run_cheduler

from db import Db
from dtypes.db import method as dmth
from dtypes.settings import Settings
from dtypes.email import Email

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

    email: Email = await db.ex(dmth.GetOne(Email))
    if not email:
        example = Email(
            id="example",
            login="example@gmail.com",
            password="1234 jasdk qwpo fkeo",
            imap_host="imap.gmail.com",
            imap_port=993,
            smpt_host="smtp.gmail.com",
            smpt_port=587,
            domain="example.com"
        )
        await db.ex(dmth.AddOne(Email, example))

    await run_cheduler()
    await run_telegram()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
