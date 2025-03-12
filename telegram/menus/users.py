
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser

from telegram.factory import CallbackFactory


users_router = Router()
db = Db()
crm = CrmDb()


@users_router.callback_query(CallbackFactory.filter(F.action == "users"))
async def users_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()

    tusers: list[User] = await db.ex(dmth.GetMany(User))
    tusers_dict = {tuser.id: tuser  for tuser in tusers}

    users: list[CrmUser] = await db.ex(dmth.GetMany(CrmUser))

    authed_users = []
    not_authed_users = []
    for user in users:
        if user.user_id:
            authed_users.append(user)

        else:
            not_authed_users.append(user)

    authed_users = sorted(authed_users, key=lambda obj: obj.first_name)
    not_authed_users = sorted(not_authed_users, key=lambda obj: obj.first_name)

    for authed_user in authed_users:
        keyboard.row(InlineKeyboardButton(
            text=f"{authed_user.fullname} {_('right')}",
            callback_data="nothing"
        ))

    for not_authed_user in not_authed_users:
        keyboard.row(InlineKeyboardButton(
            text=f"{not_authed_user.fullname} {_('wrong')}",
            callback_data="nothing"
        ))

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="main").pack()
        )
    )

    await callback.message.edit_text(
        text=_("users_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )
