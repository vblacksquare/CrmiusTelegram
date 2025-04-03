
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User

from telegram.factory import CallbackFactory


write_router = Router()
db = Db()


@write_router.callback_query(CallbackFactory.filter(F.action == "write"))
async def write_menu(callback: CallbackQuery, state: FSMContext):

    if state:
        await state.clear()

    user: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))

    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(
            text=_("to_user_bt"),
            callback_data=CallbackFactory(action="to_user").pack()
        )
    )

    keyboard.row(
        InlineKeyboardButton(
            text=_("to_group_bt"),
            callback_data=CallbackFactory(action="to_group").pack()
        )
    )

    if user.role != "user":
        keyboard.row(
            InlineKeyboardButton(
                text=_("global_bt"),
                callback_data=CallbackFactory(action="global").pack()
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text=_("kick_bt"),
            callback_data=CallbackFactory(action="kick").pack()
        )
    )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="main").pack()
        )
    )

    await callback.message.edit_text(
        text=_("write_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )
