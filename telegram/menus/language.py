
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User

from telegram.factory import CallbackFactory

from config import LANGUAGES


language_router = Router()


@language_router.callback_query(CallbackFactory.filter(F.action == "language"))
async def language_menu(callback: CallbackQuery = None, user_message: Message = None, action: str = "return"):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        *[
            InlineKeyboardButton(
                text=_(language),
                callback_data=CallbackFactory(action="change_language", value=f"{action}|{language}").pack()
            )
            for language in LANGUAGES
        ]
    )
    keyboard.row(
        InlineKeyboardButton(
            text=_("skip_bt") if action == "skip" else _("back_bt"),
            callback_data=CallbackFactory(action="main").pack()
        )
    )

    if user_message:
        await user_message.answer(
            _("language_msg"),
            reply_markup=keyboard.as_markup(),
            parse_mode="html"
        )

    else:
        if callback.message.photo:
            await callback.message.delete()
            await callback.message.answer(
                _("language_msg"),
                reply_markup=keyboard.as_markup(),
                parse_mode="html"
            )

        else:
            await callback.message.edit_text(
                _("language_msg"),
                reply_markup=keyboard.as_markup(),
                parse_mode="html"
            )


@language_router.message(Command("language"))
async def language_menu_command(message: Message):
    action = "return"

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        *[
            InlineKeyboardButton(
                text=_(language),
                callback_data=CallbackFactory(action="change_language", value=f"{action}|{language}").pack()
            )
            for language in LANGUAGES
        ]
    )
    keyboard.row(
        InlineKeyboardButton(
            text=_("skip_bt") if action == "skip" else _("back_bt"),
            callback_data=CallbackFactory(action="main").pack()
        )
    )

    await message.reply(
        _("language_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="html"
    )


@language_router.callback_query(CallbackFactory.filter(F.action == "change_language"))
async def change_language(callback: CallbackQuery, callback_data: CallbackFactory, i18n):
    action, language = callback_data.value.split("|")

    i18n.ctx_locale.set(language)
    user = await Db().ex(dmth.GetOne(User, id=callback.from_user.id))

    if user.language != language:
        user.language = language
        await Db().ex(dmth.UpdateOne(User, user, to_update=["language"]))
        await language_menu(callback, action=action)
