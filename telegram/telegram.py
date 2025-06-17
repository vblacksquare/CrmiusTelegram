
import os
from loguru import logger

from aiogram import Dispatcher, Bot
from aiogram.utils.i18n import I18n
from aiogram.fsm.storage.mongo import MongoStorage

from .i18n import UserLanguageMiddleware
from .middleware import ClearFsmMiddleware

from config import get_config


bot = Bot(token=get_config().telegram.bot_token)

os.system(f"pybabel compile -d {get_config().resources.locales_path} -D messages")
i18n = I18n(path=get_config().resources.locales_path, default_locale="en", domain="messages")


async def run_telegram():
    try:
        from .menus import menus_router

        # await bot.delete_webhook(drop_pending_updates=True)

        dp = Dispatcher(storage=MongoStorage.from_url(get_config().database.uri))
        dp.include_router(menus_router)

        dp.message.middleware(ClearFsmMiddleware(bot, dp))

        i18n_middleware = UserLanguageMiddleware(i18n)
        i18n_middleware.setup(dp)

        await dp.start_polling(bot, i18n=i18n)

    except Exception as err:
        logger.exception(err)
