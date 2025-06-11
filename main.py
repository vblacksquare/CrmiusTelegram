
import asyncio

from telegram import run
from telegram import callbacks
from updater import Updater

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

    updater = Updater(loop=loop)
    updater.callback_chat_message = callbacks.new_chat_message
    updater.callback_chat_audio_message = callbacks.new_chat_audio_message
    updater.callback_chat_photo_message = callbacks.new_chat_photo_message
    updater.callback_chat_document_message = callbacks.new_chat_document_message

    updater.callback_group_message = callbacks.new_group_message
    updater.callback_group_audio_message = callbacks.new_group_audio_message
    updater.callback_group_photo_message = callbacks.new_group_photo_message
    updater.callback_group_document_message = callbacks.new_group_document_message

    updater.callback_task_notification = callbacks.new_task_notification
    updater.callback_lead = callbacks.new_lead

    await run(updater=updater)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
