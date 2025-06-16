
from datetime import datetime
import pytz

from aiogram.types import WebAppInfo, LinkPreviewOptions, FSInputFile, InputMediaPhoto, URLInputFile, InputMediaDocument
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from agent.taras import TEMP_DATA

from telegram import bot, i18n
from loguru import logger
import urllib.parse

from db import Db
from dtypes.db import method as dmth
from dtypes.group import Group
from dtypes.message import ChatMessage, GroupMessage, MessageType
from dtypes.user import User, CrmUser

from emitter import emitter, EventType

from config import get_config


db = Db()


def generate_group_app_link(
    reciever: CrmUser,
    group: Group,
) -> str:

    resource_link = get_config().crm.group_chat_url.format(name=group.slug)
    resource_link = urllib.parse.quote_plus(resource_link)
    reciever_user = reciever
    login = urllib.parse.quote_plus(reciever_user.login)
    password = urllib.parse.quote_plus(reciever_user.not_hashed_password)
    return get_config().crm.redirect_url.format(login=login, password=password, redirect=resource_link)


def generate_private_app_link(
    sender: CrmUser,
    reciever: CrmUser
) -> str:

    resource_link = get_config().crm.private_chat_url.format(username=sender.username)
    resource_link = urllib.parse.quote_plus(resource_link)
    reciever_user = reciever
    login = urllib.parse.quote_plus(reciever_user.login)
    password = urllib.parse.quote_plus(reciever_user.not_hashed_password)
    return get_config().crm.redirect_url.format(login=login, password=password, redirect=resource_link)


async def generate_keyboard(
    reciever_tuser: User,
    sender: CrmUser,
    reciever: CrmUser,
    group: Group
):

    if group:
        app_redirect_link = generate_group_app_link(reciever=reciever, group=group)

    else:
        app_redirect_link = generate_private_app_link(sender=sender, reciever=reciever)

    tuser = reciever_tuser

    keyboard = InlineKeyboardBuilder()

    if reciever.id in TEMP_DATA:
        entity = TEMP_DATA.pop(reciever.id)

        if isinstance(entity, CrmUser):
            app_redirect_link = generate_private_app_link(sender=entity, reciever=sender)
            keyboard.row(
                InlineKeyboardButton(
                    text=i18n.gettext("in_app_bt", locale=tuser.language),
                    web_app=WebAppInfo(url=app_redirect_link)
                )
            )

        elif isinstance(entity, Group):
            app_redirect_link = generate_group_app_link(group=entity, reciever=sender)
            keyboard.row(
                InlineKeyboardButton(
                    text=i18n.gettext("in_app_bt", locale=tuser.language),
                    web_app=WebAppInfo(url=app_redirect_link)
                )
            )

    else:
        keyboard.row(
            InlineKeyboardButton(
                text=i18n.gettext("in_app_bt", locale=tuser.language),
                web_app=WebAppInfo(url=app_redirect_link)
            )
        )

    return keyboard


@emitter.on(EventType.send_message)
async def send_message(
    sender: CrmUser,
    reciever: CrmUser,
    text: str,
    group: Group = None,
    audio: str = None,
    photos: list[str] = [],
    documents: list[str] = []
):

    try:
        if not reciever.user_id:
            return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

        reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
        if not reciever_tuser:
            return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

        dest = "group" if group else "chat"
        message_type = ""
        if audio:
            message_type = "audio"
        elif photos:
            message_type = "photo"
        elif documents:
            message_type = "document"

        message_text = i18n.gettext(
            '_'.join(filter(
                lambda x: x,
                [
                    "new",
                    dest,
                    message_type,
                    "message"
                ]
            )),
            locale=reciever_tuser.language
        ).format(
            sender=" ".join((sender.first_name, sender.last_name)),
            reciever=" ".join((reciever.first_name, reciever.last_name)),
            text=text,
            caption=text,
            group=group.title if group else None
        )

        keyboard = await generate_keyboard(
            reciever_tuser=reciever_tuser,
            sender=sender,
            reciever=reciever,
            group=group
        )

        time_now = datetime.now(pytz.timezone("Europe/Kiev"))
        notificate = True
        if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
            notificate = False

        if audio:
            message = await bot.send_voice(
                voice=FSInputFile(path=audio, filename="audio.ogg"),
                caption=message_text,
                parse_mode="html",
                chat_id=reciever_tuser.id,
                disable_notification=not notificate,
                reply_markup=keyboard.as_markup()
            )

        elif photos:
            album = []
            for i, document in enumerate(photos):
                album.append(InputMediaPhoto(
                    media=URLInputFile(url=document),
                    caption=message_text if i == 0 else None,
                    parse_mode="html"
                ))

            message = await bot.send_media_group(
                media=album,
                chat_id=reciever_tuser.id,
                disable_notification=not notificate
            )

        elif documents:
            album = []
            for i, document in enumerate(documents):
                album.append(InputMediaDocument(
                    media=URLInputFile(url=document[0], filename=document[1]),
                    caption=message_text if i == 0 else None,
                    parse_mode="html"
                ))

            message = await bot.send_media_group(
                media=album,
                chat_id=reciever_tuser.id,
                disable_notification=not notificate
            )

        else:
            message = await bot.send_message(
                text=message_text,
                parse_mode="html",
                chat_id=reciever_tuser.id,
                link_preview_options=LinkPreviewOptions(is_disabled=False),
                disable_notification=not notificate,
                reply_markup=keyboard.as_markup()
            )

        logger.debug(f"Sent message -> {message}")
        return message

    except Exception as err:
        logger.exception(err)
