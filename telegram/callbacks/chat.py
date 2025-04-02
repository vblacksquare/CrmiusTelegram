
import pytz
from datetime import datetime

from loguru import logger

from aiogram.types import LinkPreviewOptions, URLInputFile, FSInputFile, InputMediaPhoto, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from ..telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser


db = Db()


async def __new_chat_message(sender: CrmUser, reciever: CrmUser, text: str, forward_to: CrmUser = None):
    forward_tuser: User = (await db.ex(dmth.GetOne(User, id=forward_to.user_id))) if forward_to else None

    if not reciever.user_id and not forward_tuser:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser and not forward_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    task_link = f"https://innova.crmius.com/chat/{sender.username}/chat/"

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=i18n.gettext("go_to_chat", locale=forward_tuser.language),
            web_app=WebAppInfo(url=task_link)
        )
    )

    try:
        if forward_tuser:
            message = await bot.send_message(
                text=i18n.gettext("new_forward_chat_message", locale=forward_tuser.language).format(
                    sender=" ".join((sender.first_name, sender.last_name)),
                    reciever=" ".join((reciever.first_name, reciever.last_name)),
                    text=text
                ),
                parse_mode="html",
                chat_id=forward_tuser.id,
                link_preview_options=LinkPreviewOptions(is_disabled=False),
                disable_notification=True,
                reply_markup=keyboard.as_markup()
            )

        else:

            time_now = datetime.now(pytz.timezone("Europe/Kiev"))
            notificate = True
            if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
                notificate = False

            message = await bot.send_message(
                text=i18n.gettext("new_chat_message", locale=reciever_tuser.language).format(
                    sender=" ".join((sender.first_name, sender.last_name)),
                    text=text
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


async def __new_chat_audio_message(sender: CrmUser, reciever: CrmUser, caption: str, audio: str, forward_to: CrmUser = None):
    forward_tuser: User = (await db.ex(dmth.GetOne(User, id=forward_to.user_id))) if forward_to else None

    if not reciever.user_id and not forward_tuser:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser and not forward_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    try:
        if forward_tuser:
            message = await bot.send_voice(
                voice=FSInputFile(path=audio, filename="audio.ogg"),
                caption=i18n.gettext("new_forward_chat_audio_message", locale=forward_tuser.language).format(
                    sender=" ".join((sender.first_name, sender.last_name)),
                    reciever=" ".join((reciever.first_name, reciever.last_name)),
                    caption=caption
                ),
                parse_mode="html",
                chat_id=forward_tuser.id,
                disable_notification=True
            )

        else:
            time_now = datetime.now(pytz.timezone("Europe/Kiev"))
            notificate = True
            if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
                notificate = False

            message = await bot.send_voice(
                voice=FSInputFile(path=audio, filename="audio.ogg"),
                caption=i18n.gettext("new_chat_audio_message", locale=reciever_tuser.language).format(
                    sender=" ".join((sender.first_name, sender.last_name)),
                    caption=caption
                ),
                parse_mode="html",
                chat_id=reciever_tuser.id,
                disable_notification=not notificate
            )

        return message

    except Exception as err:
        logger.exception(err)


async def __new_chat_photo_message(sender: CrmUser, reciever: CrmUser, caption: str, photos: list[str], forward_to: CrmUser = None):
    forward_tuser: User = (await db.ex(dmth.GetOne(User, id=forward_to.user_id))) if forward_to else None

    if not reciever.user_id and not forward_tuser:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser and not forward_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    try:

        if forward_tuser:
            album = []
            for i, photo in enumerate(photos[:10]):
                caption = i18n.gettext("new_forward_chat_photo_message", locale=forward_tuser.language).format(
                    sender=" ".join((sender.first_name, sender.last_name)),
                    reciever=" ".join((reciever.first_name, reciever.last_name)),
                    caption=caption
                ) if i == 0 else None

                album.append(InputMediaPhoto(
                    media=URLInputFile(url=photo),
                    caption=caption,
                    parse_mode="html"
                ))

            message = await bot.send_media_group(
                media=album,
                chat_id=forward_tuser.id,
                disable_notification=True
            )

        else:
            time_now = datetime.now(pytz.timezone("Europe/Kiev"))
            notificate = True
            if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
                notificate = False

            album = []
            for i, photo in enumerate(photos[:10]):
                caption = i18n.gettext("new_chat_photo_message", locale=reciever_tuser.language).format(
                    sender=" ".join((sender.first_name, sender.last_name)),
                    caption=caption
                ) if i == 0 else None

                album.append(InputMediaPhoto(
                    media=URLInputFile(url=photo),
                    caption=caption,
                    parse_mode="html"
                ))

            message = await bot.send_media_group(
                media=album,
                chat_id=reciever_tuser.id,
                disable_notification=not notificate
            )

        return message

    except Exception as err:
        logger.exception(err)
