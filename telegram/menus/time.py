
import pytz
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User

from telegram.factory import CallbackFactory


time_router = Router()
db = Db()


times = [
    [0, 24],
]

for left in range(0, 24):
    right = left + 9

    if right > 24:
        right -= 24

    times.append([left, right])


@time_router.callback_query(CallbackFactory.filter(F.action == "time"))
async def time_menu(callback: CallbackQuery):
    user: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))

    keyboard = InlineKeyboardBuilder()

    for time_format in times:
        text = _("time_format_bt").format(left=time_format[0], right=time_format[1])

        if time_format == user.time:
            keyboard.row(
                InlineKeyboardButton(
                    text=" ".join((_("right"), text)),
                    callback_data="nothing"
                )
            )

        else:
            keyboard.row(
                InlineKeyboardButton(
                    text=text,
                    callback_data=CallbackFactory(action="chose_time", value=str(time_format)).pack()
                )
            )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="main").pack()
        )
    )

    time_now = datetime.now(pytz.timezone("Europe/Kiev")).strftime("%H:%M")
    await callback.message.edit_text(
        _("time_msg").format(now=time_now),
        reply_markup=keyboard.as_markup(),
        parse_mode="html"
    )


@time_router.message(Command("time"))
async def time_menu_command(message: Message):
    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))

    keyboard = InlineKeyboardBuilder()

    for time_format in times:
        text = _("time_format_bt").format(left=time_format[0], right=time_format[1])

        if time_format == user.time:
            keyboard.row(
                InlineKeyboardButton(
                    text=" ".join((_("right"), text)),
                    callback_data="nothing"
                )
            )

        else:
            keyboard.row(
                InlineKeyboardButton(
                    text=text,
                    callback_data=CallbackFactory(action="chose_time", value=str(time_format)).pack()
                )
            )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="main").pack()
        )
    )

    time_now = datetime.now(pytz.timezone("Europe/Kiev")).strftime("%H:%M")
    await message.reply(
        _("time_msg").format(now=time_now),
        reply_markup=keyboard.as_markup(),
        parse_mode="html"
    )


@time_router.callback_query(CallbackFactory.filter(F.action == "chose_time"))
async def change_time(callback: CallbackQuery, callback_data: CallbackFactory):
    chose_time = eval(callback_data.value)

    user: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    user.time = chose_time
    await db.ex(dmth.UpdateOne(User, user, to_update=["time"]))

    keyboard = InlineKeyboardBuilder()

    for time_format in times:
        text = _("time_format_bt").format(left=time_format[0], right=time_format[1])

        if time_format == user.time:
            keyboard.row(
                InlineKeyboardButton(
                    text=" ".join((_("right"), text)),
                    callback_data="nothing"
                )
            )

        else:
            keyboard.row(
                InlineKeyboardButton(
                    text=text,
                    callback_data=CallbackFactory(action="chose_time", value=str(time_format)).pack()
                )
            )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="main").pack()
        )
    )

    time_now = datetime.now(pytz.timezone("Europe/Kiev")).strftime("%H:%M")
    await callback.message.edit_text(
        _("time_msg").format(now=time_now),
        reply_markup=keyboard.as_markup(),
        parse_mode="html"
    )
