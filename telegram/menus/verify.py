
import bcrypt

from loguru import logger

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db, CrmDb

from dtypes.user import User, CrmUser
from dtypes.db import method as dmth

from telegram.factory import CallbackFactory
from telegram.state import MainState


verify_router = Router()
db = Db()
crm = CrmDb()


@verify_router.callback_query(CallbackFactory.filter(F.action == "verify"))
async def verify_menu(callback: CallbackQuery = None, state: FSMContext = None, user_message: Message = None):
    await state.clear()

    keyboard = InlineKeyboardBuilder()

    if user_message:
        temp_message = await user_message.answer(
            text=_("verify_msg"),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

    else:
        temp_message = await callback.message.edit_text(
            text=_("verify_msg"),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

    await state.set_state(MainState.verify)
    await state.update_data({"temp_message_id": temp_message.message_id})


@verify_router.message(MainState.verify)
async def verify_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    temp_message_id = data["temp_message_id"]

    try:
        await message.delete()
        login, password = message.text.split(maxsplit=1)

        crm_user = await crm.get_user_by_login(login)
        await db.ex(dmth.AddOne(CrmUser, crm_user))

        if not crm_user:
            raise ValueError

        if not bcrypt.checkpw(password.encode('utf-8'), crm_user.password.encode('utf-8')):
            raise ValueError

        user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))
        user.is_verified = True
        user.crm_id = crm_user.id
        await db.ex(dmth.UpdateOne(User, user, to_update=["is_verified", "crm_id"]))

        crm_user.user_id = user.id
        crm_user.not_hashed_password = password
        await db.ex(dmth.UpdateOne(CrmUser, crm_user, to_update=["user_id", "not_hashed_password"]))

        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(
                text=_("click_me_bt"),
                callback_data=CallbackFactory(action="main").pack()
            )
        )

        await message.bot.edit_message_text(
            text=_("verify_ok_msg").format(
                name=crm_user.first_name
            ),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML",
            message_id=temp_message_id,
            chat_id=user.id
        )
        await state.clear()

    except Exception as err:
        logger.exception(err)

        await message.bot.edit_message_text(
            text=_("verify_err_msg"),
            parse_mode="HTML",
            message_id=temp_message_id,
            chat_id=message.from_user.id
        )

        await state.set_state(MainState.verify)
        await state.update_data({"temp_message_id": temp_message_id})
