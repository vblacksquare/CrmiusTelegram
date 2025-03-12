
from loguru import logger

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, LinkPreviewOptions
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User
from dtypes.plan import Plan

from telegram.telegram import bot, i18n
from telegram.factory import CallbackFactory
from telegram.state import MainState


plan_router = Router()
db = Db()


@plan_router.callback_query(CallbackFactory.filter(F.action == "plan"))
async def plan_menu(callback: CallbackQuery, state: FSMContext):

    user: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    if user.role not in ["admin", "top_admin"]:
        return

    plan: Plan = await db.ex(dmth.GetOne(Plan, id=user.id))
    if not plan:
        plan = Plan(id=user.id)
        await db.ex(dmth.AddOne(Plan, plan))

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="write").pack()
        )
    )

    message = await callback.message.edit_text(
        text=_("plan_msg").format(hours=str(plan.hours), message=plan.message),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )

    await state.set_state(MainState.plan)
    await state.update_data({
        "temp_message_id": message.message_id
    })


@plan_router.message(MainState.plan)
async def new_plan_menu(message: Message, state: FSMContext):

    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))
    if user.role not in ["admin", "top_admin"]:
        return

    data = await state.get_data()
    temp_message_id = data["temp_message_id"]

    await state.clear()

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="plan").pack()
        )
    )

    try:
        await message.delete()

        hours, message_text = message.text.split("\n", maxsplit=1)

        hours = int(hours)
        if hours > 24 or hours < 0:
            raise ValueError

        plan: Plan = await db.ex(dmth.GetOne(Plan, id=message.from_user.id))
        plan.hours = hours
        plan.message = message_text
        await db.ex(dmth.UpdateOne(Plan, plan, to_update=["hours", "message"]))

        await message.bot.edit_message_text(
            text=_("ok_plan_msg"),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML",
            message_id=temp_message_id,
            chat_id=message.chat.id
        )

    except Exception as err:
        logger.exception(err)

        await message.bot.edit_message_text(
            text=_("err_plan_msg"),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML",
            message_id=temp_message_id,
            chat_id=message.chat.id
        )
