

import urllib.parse
import pytz
from datetime import datetime

from loguru import logger

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import LinkPreviewOptions, WebAppInfo

from ..telegram import bot, i18n
from emitter import emitter, EventType

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser
from dtypes.task import Task
from dtypes.notification import Notification
from dtypes.message import TaskMessage


db = Db()


@emitter.on(EventType.new_task)
async def new_task(notification: Notification):
    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=notification.sender_id))
    reciever: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=notification.reciever_id))
    task: Task = await db.ex(dmth.GetOne(Task, id=notification.task_id))

    message = None
    if notification.message_id:
        message: TaskMessage = await db.ex(dmth.GetOne(TaskMessage, id=notification.message_id))

    kwargs = {
        "task_id": task.id,
        "sender": sender,
        "reciever": reciever,
        "text": message.text if message else None,
        "type": notification.type,
        "title": task.title
    }
    data = {key: str(kwargs[key]) for key in kwargs}
    logger.debug(f"Sending message -> {data}")

    emitter.emit(
        EventType.send_task,
        **kwargs
    )
