
import urllib.parse
import pytz
from datetime import datetime

from loguru import logger

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import LinkPreviewOptions, WebAppInfo
from aiogram.utils.i18n import gettext as _

from ..telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser
from dtypes.message import TaskMessage
from dtypes.task import Task

from config import TASK_URL, PORTAL_REDIRECT_URL


db = Db()


async def generate_app_link(
    reciever: CrmUser,
    task: Task
) -> str:

    resource_link = TASK_URL.format(task_id=task.id)
    resource_link = urllib.parse.quote_plus(resource_link)
    reciever_user = reciever
    login = urllib.parse.quote_plus(reciever_user.login)
    password = urllib.parse.quote_plus(reciever_user.not_hashed_password)
    return PORTAL_REDIRECT_URL.format(login=login, password=password, redirect=resource_link)


async def generate_keyboard(
    reciever_tuser: User,
    reciever: CrmUser,
    task: Task
):

    app_redirect_link = await generate_app_link(reciever, task)

    tuser = reciever_tuser

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=i18n.gettext("in_app_bt", locale=tuser),
            web_app=WebAppInfo(url=app_redirect_link)
        )
    )

    return keyboard


async def __new_task_notification(sender: CrmUser, reciever: CrmUser, task: Task, notification_type: str, message: TaskMessage = None):
    if not reciever.user_id:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    time_now = datetime.now(pytz.timezone("Europe/Kiev"))
    notificate = True
    if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
        notificate = False

    keyboard = await generate_keyboard(reciever_tuser, reciever, task)

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
