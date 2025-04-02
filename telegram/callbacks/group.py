
import urllib.parse
import pytz
from datetime import datetime

from loguru import logger

from aiogram.types import LinkPreviewOptions, URLInputFile, FSInputFile, InputMediaPhoto, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from ..telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser
from dtypes.group import Group


from config import GROUP_CHAT_URL, PORTAL_REDIRECT_URL


db = Db()


async def generate_app_link(
    reciever: CrmUser,
    forward_to: CrmUser,
    group: Group,
) -> str:

    resource_link = GROUP_CHAT_URL.format(name=group.slug)
    logger.info(resource_link)
    resource_link = urllib.parse.quote_plus(resource_link)
    reciever_user = forward_to if forward_to else reciever
    login = urllib.parse.quote_plus(reciever_user.login)
    password = urllib.parse.quote_plus(reciever_user.not_hashed_password)
    return PORTAL_REDIRECT_URL.format(login=login, password=password, redirect=resource_link)


async def generate_keyboard(
    reciever_tuser: User,
    forward_tuser: User,
    reciever: CrmUser,
    forward_to: CrmUser,
    group: Group
):

    app_redirect_link = await generate_app_link(reciever=reciever, forward_to=forward_to, group=group)
    logger.info(app_redirect_link)

    tuser = forward_tuser if forward_tuser else reciever_tuser

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=i18n.gettext("in_app_bt", locale=tuser.language),
            web_app=WebAppInfo(url=app_redirect_link)
        )
    )

    return keyboard


async def __new_group_message(sender: CrmUser, reciever: CrmUser, group: Group, text: str, forward_to: CrmUser = None):
    forward_tuser: User = (await db.ex(dmth.GetOne(User, id=forward_to.user_id))) if forward_to else None

    if not reciever.user_id and not forward_tuser:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser and not forward_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    keyboard = await generate_keyboard(
        reciever_tuser=reciever_tuser,
        forward_tuser=forward_tuser,
        reciever=reciever,
        forward_to=forward_to,
        group=group
    )

    try:
        if forward_tuser:
            message = await bot.send_message(
                text=i18n.gettext("new_forward_group_message", locale=forward_tuser.language).format(
                    group=group.title,
                    sender=" ".join((sender.first_name, sender.last_name)),
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
                text=i18n.gettext("new_group_message", locale=reciever_tuser.language).format(
                    group=group.title,
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


async def __new_group_audio_message(sender: CrmUser, reciever: CrmUser, group: Group, caption: str, audio: str, forward_to: CrmUser = None):
    forward_tuser: User = (await db.ex(dmth.GetOne(User, id=forward_to.user_id))) if forward_to else None

    if not reciever.user_id and not forward_tuser:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser and not forward_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    keyboard = await generate_keyboard(
        reciever_tuser=reciever_tuser,
        forward_tuser=forward_tuser,
        reciever=reciever,
        forward_to=forward_to,
        group=group
    )

    try:
        if forward_tuser:
            message = await bot.send_voice(
                voice=FSInputFile(path=audio, filename="audio.ogg"),
                caption=i18n.gettext("new_forward_group_audio_message", locale=forward_tuser.language).format(
                    group=group.title,
                    sender=" ".join((sender.first_name, sender.last_name)),
                    caption=caption
                ),
                parse_mode="html",
                chat_id=forward_tuser.id,
                disable_notification=True,
                reply_markup=keyboard.as_markup()
            )

        else:
            time_now = datetime.now(pytz.timezone("Europe/Kiev"))
            notificate = True
            if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
                notificate = False

            message = await bot.send_voice(
                voice=FSInputFile(path=audio, filename="audio.ogg"),
                caption=i18n.gettext("new_group_audio_message", locale=reciever_tuser.language).format(
                    group=group.title,
                    sender=" ".join((sender.first_name, sender.last_name)),
                    caption=caption
                ),
                parse_mode="html",
                chat_id=reciever_tuser.id,
                disable_notification=not notificate,
                reply_markup=keyboard.as_markup()
            )

        return message

    except Exception as err:
        logger.exception(err)


async def __new_group_photo_message(sender: CrmUser, reciever: CrmUser, group: Group, caption: str, photos: list[str], forward_to: CrmUser = None):
    forward_tuser: User = (await db.ex(dmth.GetOne(User, id=forward_to.user_id))) if forward_to else None

    if not reciever.user_id and not forward_tuser:
        return logger.warning(f"No user authed -> {reciever.id}:{reciever.login}")

    reciever_tuser: User = await db.ex(dmth.GetOne(User, id=reciever.user_id))
    if not reciever_tuser and not forward_tuser:
        return logger.warning(f"No such user_id -> {reciever.user_id} -> {reciever.id}:{reciever.login}")

    keyboard = await generate_keyboard(
        reciever_tuser=reciever_tuser,
        forward_tuser=forward_tuser,
        reciever=reciever,
        forward_to=forward_to,
        group=group
    )

    try:
        if forward_tuser:
            album = []
            for i, photo in enumerate(photos[:10]):
                caption = i18n.gettext("new_forward_group_photo_message", locale=forward_tuser.language).format(
                    group=group.title,
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
                chat_id=forward_tuser.id,
                disable_notification=True,
                reply_markup=keyboard.as_markup()
            )

        else:
            time_now = datetime.now(pytz.timezone("Europe/Kiev"))
            notificate = True
            if time_now.hour >= reciever_tuser.time[-1] or time_now.hour < reciever_tuser.time[0]:
                notificate = False

            album = []
            for i, photo in enumerate(photos[:10]):
                caption = i18n.gettext("new_group_photo_message", locale=reciever_tuser.language).format(
                    group=group.title,
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
                disable_notification=not notificate,
                reply_markup=keyboard.as_markup()
            )

        return message

    except Exception as err:
        logger.exception(err)
