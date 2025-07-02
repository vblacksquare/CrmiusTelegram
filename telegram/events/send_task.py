from datetime import datetime
import pytz

from aiogram.types import WebAppInfo, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from telegram import bot, i18n
from loguru import logger
import urllib.parse

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser

from emitter import emitter, EventType

from config import get_config

db = Db()


@emitter.on(EventType.send_task)
async def send_task(
    task_id: int,
    sender: CrmUser,
    reciever: CrmUser,
    text: str,
    type: str,
    title: str
):

    try:
        if not reciever.user_id:
            return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

        reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
        if not reciever_tuser:
            logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")
            return

        message_text = i18n.gettext(
            "new_task_notification",
            locale=reciever_tuser.language
        ).format(
            sender=" ".join((sender.first_name, sender.last_name)),
            notification_type=type,
            task_name=title,
            attachment=text if text else ""
        )

        keyboard = await generate_keyboard(
            task_id=task_id,
            reciever_tuser=reciever_tuser,
            reciever=reciever,
        )

        time_now = datetime.now(pytz.timezone("Europe/Kiev"))
        notificate = True
        if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
            notificate = False

        messages = [await bot.send_message(
            text=message_text,
            parse_mode="html",
            chat_id=reciever_tuser.id,
            link_preview_options=LinkPreviewOptions(is_disabled=False),
            disable_notification=not notificate,
            reply_markup=keyboard.as_markup()
        )]

        logger.debug(f"Sent message -> {messages}")

    except Exception as err:
        logger.exception(err)

        return


async def generate_app_link(
    task_id: int,
    reciever: CrmUser
) -> str:

    resource_link = get_config().crm.task_url.format(task_id=task_id)
    resource_link = urllib.parse.quote_plus(resource_link)
    login = urllib.parse.quote_plus(reciever.login)
    password = urllib.parse.quote_plus(reciever.not_hashed_password)
    return get_config().crm.redirect_url.format(login=login, password=password, redirect=resource_link)


async def generate_keyboard(
    task_id: int,
    reciever_tuser: User,
    reciever: CrmUser
):

    app_redirect_link = await generate_app_link(reciever=reciever, task_id=task_id)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=i18n.gettext("in_app_bt", locale=reciever_tuser.language),
            web_app=WebAppInfo(url=app_redirect_link)
        )
    )

    return keyboard
