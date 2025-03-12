
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


db = Db()


async def __new_task_notification(sender: CrmUser, reciever: CrmUser, task: Task, notification_type: str, message: TaskMessage = None):
    if not reciever.user_id:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    receiver_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not receiver_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    time_now = datetime.now(pytz.timezone("Europe/Kiev"))
    notificate = True
    if time_now.hour >= receiver_tuser.time[-1] or time_now.hour < receiver_tuser.time[0]:
        notificate = False

    try:
        attachment = ""
        if message:
            attachment = message.text
            task_link = f"https://innova.crmius.com/admin/tasks/view/{task.id}#comment_{message.id}"

        else:
            task_link = f"https://innova.crmius.com/admin/tasks/view/{task.id}"

        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(
                text=i18n.gettext("in_app_bt", locale=receiver_tuser.language),
                web_app=WebAppInfo(url=task_link)
            )
        )

        message = await bot.send_message(
            text=i18n.gettext("new_task_notification", locale=receiver_tuser.language).format(
                sender=" ".join((sender.first_name, sender.last_name)),
                task_name=task.title,
                task_link=task_link,
                notification_type=i18n.gettext(notification_type, locale=receiver_tuser.language),
                attachment=attachment
            ),
            parse_mode="html",
            chat_id=receiver_tuser.id,
            link_preview_options=LinkPreviewOptions(is_disabled=False),
            disable_notification=not notificate,
            reply_markup=keyboard.as_markup()
        )

        return message

    except Exception as err:
        logger.exception(err)
