
import os
from loguru import logger

from aiogram import Dispatcher, Bot
from aiogram.utils.i18n import I18n
from aiogram.fsm.storage.mongo import MongoStorage

from .i18n import UserLanguageMiddleware
from .middleware import ClearFsmMiddleware

from config import BOT_TOKEN, LOCALES_DIR, MONGODB_URI


bot = Bot(token=BOT_TOKEN)

os.system(f"pybabel compile -d {LOCALES_DIR} -D messages")
i18n = I18n(path=LOCALES_DIR, default_locale="en", domain="messages")


async def run(updater):
    try:
        from .menus import menus_router

        await bot.delete_webhook(drop_pending_updates=True)

        dp = Dispatcher(storage=MongoStorage.from_url(MONGODB_URI))
        dp.include_router(menus_router)

        dp.message.middleware(ClearFsmMiddleware(bot, dp))

        i18n_middleware = UserLanguageMiddleware(i18n)
        i18n_middleware.setup(dp)

        await updater.run()
        await dp.start_polling(bot, i18n=i18n)

    except Exception as err:
        logger.exception(err)
