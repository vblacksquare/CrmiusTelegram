

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
from dtypes.message import TaskMessage
from dtypes.task import Task
from dtypes.notification import Notification

from config import get_config


db = Db()


async def generate_app_link(
    reciever: CrmUser,
    task: Task
) -> str:

    resource_link = get_config().crm.task_url.format(task_id=task.id)
    resource_link = urllib.parse.quote_plus(resource_link)
    reciever_user = reciever
    login = urllib.parse.quote_plus(reciever_user.login)
    password = urllib.parse.quote_plus(reciever_user.not_hashed_password)
    return get_config().crm.redirect_url.format(login=login, password=password, redirect=resource_link)


async def generate_keyboard(
    reciever_tuser: User,
    reciever: CrmUser,
    task: Task
):

    app_redirect_link = await generate_app_link(reciever=reciever, task=task)

    tuser = reciever_tuser

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=i18n.gettext("in_app_bt", locale=tuser.language),
            web_app=WebAppInfo(url=app_redirect_link)
        )
    )

    return keyboard


"""
sender: CrmUser,
reciever: CrmUser,
task: Task,
notification_type: str,
message: TaskMessage = None
"""


@emitter.on(EventType.new_task)
async def new_task(notification: Notification):

    if not reciever.user_id:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    time_now = datetime.now(pytz.timezone("Europe/Kiev"))
    notificate = True
    if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
        notificate = False

    keyboard = await generate_keyboard(
        reciever_tuser=reciever_tuser,
        reciever=reciever,
        task=task
    )

    try:
        attachment = ""
        if message:
            attachment = message.text

        message = await bot.send_message(
            text=i18n.gettext("new_task_notification", locale=reciever_tuser.language).format(
                sender=" ".join((sender.first_name, sender.last_name)),
                task_name=task.title,
                notification_type=i18n.gettext(notification_type, locale=reciever_tuser.language),
                attachment=attachment
            ),
            parse_mode="html",
            chat_id=reciever_tuser.id,
            link_preview_options=LinkPreviewOptions(is_disabled=False),
            disable_notification=not notificate,
            reply_markup=keyboard.as_markup()
        )

        return message

    except Exception as err:
        logger.exception(err)
