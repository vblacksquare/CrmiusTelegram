
import urllib.parse

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, LinkPreviewOptions, WebAppInfo
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db, CrmDb
from dtypes import CrmUser
from dtypes.db import method as dmth
from dtypes.group import Group
from dtypes.user import User

from telegram.telegram import bot, i18n
from telegram.factory import CallbackFactory
from telegram.state import MainState

from config import GROUP_CHAT_URL, PORTAL_REDIRECT_URL


to_group_router = Router()
db = Db()
crm = CrmDb()


async def generate_app_link(
    auth: CrmUser,
    group: Group,
) -> str:

    resource_link = GROUP_CHAT_URL.format(name=group.slug)
    resource_link = urllib.parse.quote_plus(resource_link)

    login = urllib.parse.quote_plus(auth.login)
    password = urllib.parse.quote_plus(auth.not_hashed_password)
    return PORTAL_REDIRECT_URL.format(login=login, password=password, redirect=resource_link)


@to_group_router.callback_query(CallbackFactory.filter(F.action == "to_group"))
async def global_menu(callback: CallbackQuery, state: FSMContext):
    tuser: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    crm_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=tuser.crm_id))

    keyboard = InlineKeyboardBuilder()

    groups: list[Group] = await db.ex(dmth.GetMany(Group, participants={"$in": [crm_user.id]}))
    for group in groups:
        app_url = await generate_app_link(crm_user, group)

        keyboard.row(
            InlineKeyboardButton(
                text=group.title,
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
        text=_("to_group_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )
