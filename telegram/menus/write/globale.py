
from loguru import logger

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, LinkPreviewOptions
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


global_router = Router()
db = Db()
crm = CrmDb()


async def send_globally(text, allowed_users: list[str] = None):
    if allowed_users:
        users: list[CrmUser] = await Db().ex(dmth.GetMany(CrmUser, id={"$in": allowed_users}))

    else:
        users: list[CrmUser] = await Db().ex(dmth.GetMany(CrmUser))

    for user in users:
        try:
            bot_user: CrmUser = await db.ex(dmth.GetOne(CrmUser, login="robot@crmius.com"))

            language = "uk"
            if user.user_id:
                tuser: User = await db.ex(dmth.GetOne(User, id=user.user_id))
                language = tuser.language

            message_text = i18n.gettext("global_bot_message", locale=language).format(text=text),
            message_id = await crm.create_chat_message(sender=bot_user, reciever=user, text=message_text)
            await crm.send_chat_message(sender=bot_user, reciever=user, message_id=message_id, message_text=message_text)

        except Exception as err:
            logger.exception(err)


@global_router.callback_query(CallbackFactory.filter(F.action == "global"))
async def global_menu(callback: CallbackQuery, state: FSMContext):
    trigger_tuser: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    if trigger_tuser.role not in ["admin", "top_admin"]:
        return

    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(
            text=' '.join((_("right"), _("all_users_bt"))),
            callback_data="nothing"
        )
    )

    groups: list[Group] = await db.ex(dmth.GetMany(Group))
    for group in groups:
        keyboard.row(
            InlineKeyboardButton(
                text=group.title,
                callback_data=CallbackFactory(action="chose_group", value=str(group.id)).pack()
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="write").pack()
        )
    )

    message = await callback.message.edit_text(
        text=_("global_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )

    await state.set_state(MainState.globale)
    await state.update_data({
        "temp_message_id": message.message_id,
        "allowed_users": -1
    })


@global_router.callback_query(CallbackFactory.filter(F.action == "chose_group"))
async def global_menu(callback: CallbackQuery, callback_data: CallbackFactory, state: FSMContext):
    user: User = await db.ex(dmth.GetOne(User, id=callback.from_user.id))
    if user.role not in ["admin", "top_admin"]:
        return

    group_id = int(callback_data.value)

    keyboard = InlineKeyboardBuilder()

    if group_id == -1:
        keyboard.row(
            InlineKeyboardButton(
                text=' '.join((_("right"), _("all_users_bt"))),
                callback_data="nothing"
            )
        )

    else:
        keyboard.row(
            InlineKeyboardButton(
                text=_("all_users_bt"),
                callback_data=CallbackFactory(action="chose_group", value=str(-1)).pack()
            )
        )

    groups: list[Group] = await db.ex(dmth.GetMany(Group))
    for group in groups:
        if group.id == group_id:
            keyboard.row(
                InlineKeyboardButton(
                    text=' '.join((_("right"), group.title)),
                    callback_data="nothing"
                )
            )

        else:
            keyboard.row(
                InlineKeyboardButton(
                    text=group.title,
                    callback_data=CallbackFactory(action="chose_group", value=str(group.id)).pack()
                )
            )

    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="write").pack()
        )
    )

    message = await callback.message.edit_text(
        text=_("global_msg"),
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )

    await state.set_state(MainState.globale)
    await state.update_data({
        "temp_message_id": message.message_id,
        "allowed_users": group_id
    })


@global_router.message(MainState.globale)
async def global_menu(message: Message, state: FSMContext):

    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))
    if user.role not in ["admin", "top_admin"]:
        return

    data = await state.get_data()
    temp_message_id = data["temp_message_id"]
    allowed_users = data["allowed_users"]

    await state.clear()

    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text=_("back_bt"),
            callback_data=CallbackFactory(action="global").pack()
        )
    )

    try:
        await message.delete()

        if allowed_users == -1:
            allowed_users = None

        else:
            allowed_users_group: Group = (await db.ex(dmth.GetOne(Group, id=allowed_users)))
            allowed_users = allowed_users_group.participants

        await send_globally(message.text, allowed_users=allowed_users)

        await message.bot.edit_message_text(
            text=_("ok_global_msg"),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML",
            message_id=temp_message_id,
            chat_id=message.chat.id
        )

    except Exception as err:
        logger.exception(err)

        await message.bot.edit_message_text(
            text=_("err_global_msg"),
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML",
            message_id=temp_message_id,
            chat_id=message.chat.id
        )
