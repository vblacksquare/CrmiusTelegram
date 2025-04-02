
import urllib.parse

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, WebAppInfo
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser

from .verify import verify_menu

from telegram.factory import CallbackFactory

from config import ROOT_PORTAL_URL, DEV_PORTAL_URL


main_router = Router()
db = Db()


@main_router.callback_query(CallbackFactory.filter(F.action == "main"))
async def main_menu(callback: CallbackQuery = None, state: FSMContext = None, user_message: Message = None):
    if state:
        await state.clear()

    user_id = user_message.from_user.id if user_message else callback.from_user.id
    user: User = await db.ex(dmth.GetOne(User, id=user_id))
    if not user.is_verified:
        return await verify_menu(callback=callback, state=state, user_message=user_message)

    crm_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=user.crm_id))

    login = urllib.parse.quote_plus(crm_user.login)
    password = urllib.parse.quote_plus(crm_user.not_hashed_password)

    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(
            text=_("root_portal_bt"),
            web_app=WebAppInfo(url=ROOT_PORTAL_URL.format(login=login, password=password))
        )
    )

    if user.role in ["admin", "top_admin"]:
        keyboard.row(
            InlineKeyboardButton(
                text=_("dev_portal_bt"),
                web_app=WebAppInfo(url=DEV_PORTAL_URL.format(login=login, password=password))
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                text=_("users_bt"),
                callback_data=CallbackFactory(action="users").pack()
            )
        )
        keyboard.row(
            InlineKeyboardButton(
                text=_("write_bt"),
                callback_data=CallbackFactory(action="write").pack()
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text=_("time_bt"),
            callback_data=CallbackFactory(action="time").pack()
        )
    )

    keyboard.row(
        InlineKeyboardButton(
            text=_("language_bt"),
            callback_data=CallbackFactory(action="language").pack()
        )
    )

    if user_message:
        func = user_message.answer

    else:
        func = callback.message.edit_text

    await func(
        text=_("main_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )
