
import urllib.parse

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, WebAppInfo
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db, CrmDb
from dtypes import CrmUser
from dtypes.db import method as dmth
from dtypes.user import User

from telegram.factory import CallbackFactory

from config import get_config


to_user_router = Router()
db = Db()
crm = CrmDb()


async def generate_app_link(
    auth: CrmUser,
    chat: CrmUser
) -> str:

    resource_link = get_config().crm.private_chat_url.format(username=chat.username)
    resource_link = urllib.parse.quote_plus(resource_link)

    login = urllib.parse.quote_plus(auth.login)
    password = urllib.parse.quote_plus(auth.not_hashed_password)
    return get_config().crm.redirect_url.format(login=login, password=password, redirect=resource_link)


@to_user_router.callback_query(CallbackFactory.filter(F.action == "to_user"))
async def user_menu(callback: CallbackQuery):
    tuser: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    self_crm_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=tuser.crm_id))

    keyboard = InlineKeyboardBuilder()

    crm_users: list[CrmUser] = await db.ex(dmth.GetMany(CrmUser, id={"$ne": self_crm_user.id}))
    for crm_user in crm_users:
        app_url = await generate_app_link(self_crm_user, crm_user)

        keyboard.row(
            InlineKeyboardButton(
                text=crm_user.fullname,
                web_app=WebAppInfo(url=app_url)
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="write").pack()
        )
    )

    await callback.message.edit_text(
        text=_("to_user_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )


@to_user_router.message(Command("chat"))
async def user_menu(message: Message):
    tuser: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))
    self_crm_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=tuser.crm_id))

    keyboard = InlineKeyboardBuilder()

    crm_users: list[CrmUser] = await db.ex(dmth.GetMany(CrmUser, id={"$ne": self_crm_user.id}))
    for crm_user in crm_users:
        app_url = await generate_app_link(self_crm_user, crm_user)

        keyboard.row(
            InlineKeyboardButton(
                text=crm_user.fullname,
                web_app=WebAppInfo(url=app_url)
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="write").pack()
        )
    )

    await message.reply(
        text=_("to_user_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )
