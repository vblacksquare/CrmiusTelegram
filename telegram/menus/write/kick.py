
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser

from telegram.factory import CallbackFactory


kick_router = Router()
db = Db()
crm = CrmDb()


@kick_router.callback_query(CallbackFactory.filter(F.action == "kick"))
async def global_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()

    trigger_tuser: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    trigger_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=trigger_tuser.crm_id))
    if trigger_tuser.role not in ["admin", "top_admin"]:
        return

    users: list[CrmUser] = await db.ex(dmth.GetMany(CrmUser))
    users = sorted(users, key=lambda obj: obj.first_name)

    for user in users:
        keyboard.row(InlineKeyboardButton(
            text=user.fullname,
            callback_data=CallbackFactory(action="kicked", value=str(user.id)).pack()
        ))

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="write").pack()
        )
    )

    await callback.message.edit_text(
        text=_("kick_msg").format(name=trigger_user.fullname),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )


@kick_router.callback_query(CallbackFactory.filter(F.action == "kicked"))
async def kicked(callback: CallbackQuery, callback_data: CallbackFactory):
    user: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    if user.role not in ["admin", "top_admin"]:
        return

    user_id = int(callback_data.value)
    user: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=user_id))

    bot_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, login="robot@crmius.com"))

    trigger_tuser: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    trigger_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=trigger_tuser.crm_id))

    text = _("kick_text").format(name=trigger_user.fullname)
    await crm.send_chat_message(sender=bot_user, reciever=user, message_text=text)

    for row in callback.message.reply_markup:
        k, row = row
        for bt in row:
            bt = bt[0]

            if bt.text == user.fullname:
                bt.text = f"🦵 {user.fullname}"

    await callback.message.edit_text(
        text=callback.message.text,
        reply_markup=callback.message.reply_markup,
        parse_mode="HTML",
    )
