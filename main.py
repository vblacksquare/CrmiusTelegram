
import sys
import os
import asyncio
import time

from telegram import run
from telegram import callbacks
from updater import Updater

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.settings import Settings

from config import MONGODB_NAME, MONGODB_URI, LOGS_DIR, LOGS_LEVEL
from config import CRM_NAME, CRM_HOST, CRM_PASS, CRM_PORT, CRM_USER
from utils.logger import setup_logger


async def main():
    """if "s" in sys.argv:
        args = ' '.join([
            arg
            for arg in sys.argv[1:] if arg not in ["main.py", "s"]
        ])

        print("Stopping project")
        c = f"screen -S crm_bot -X quit"
        os.system(c)

        print(f"Starting project")
        c = f'screen -S crm_bot -dm bash -c "venv/bin/python main.py {args}"'
        os.system(c)
        return
    """
    setup_logger(LOGS_DIR, LOGS_LEVEL)

    db = Db()
    db.connect(MONGODB_NAME, MONGODB_URI)

    crm = CrmDb()

    settings: Settings = await db.ex(dmth.GetOne(Settings))
    if not settings:
        settings = Settings()
        await db.ex(dmth.AddOne(Settings, settings))

    if "okup" in sys.argv:
        last_chat_message_id = await crm.get_last_chat_message_id()
        settings.last_chat_message_id = last_chat_message_id

        last_group_message_id = await crm.get_last_group_message_id()
        settings.last_group_message_id = last_group_message_id

        last_task_notification_id = await crm.get_last_task_notification_id()
        settings.last_task_notification_id = last_task_notification_id

        await db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_chat_message_id", "last_group_message_id", "last_task_notification_id"]))

    updater = Updater(loop=loop)
    updater.callback_chat_message = callbacks.new_chat_message
    updater.callback_chat_audio_message = callbacks.new_chat_audio_message
    updater.callback_chat_photo_message = callbacks.new_chat_photo_message

    updater.callback_group_message = callbacks.new_group_message
    updater.callback_group_audio_message = callbacks.new_group_audio_message
    updater.callback_group_photo_message = callbacks.new_group_photo_message

    updater.callback_task_notification = callbacks.new_task_notification

    await run(updater=updater)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
