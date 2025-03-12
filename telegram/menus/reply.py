
from loguru import logger

from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from db import Db, CrmDb
from dtypes import CrmUser
from dtypes.db import method as dmth
from dtypes.user import User
from dtypes.group import Group
from dtypes.message import GroupMessage, ChatMessage, BotMessage


reply_router = Router()
db = Db()
crm = CrmDb()


@reply_router.message(F.reply_to_message)
async def reply(message: Message):
    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))

    if user.role not in ["top_admin", "replier"]:
        await message.reply(
            text=_("no_rights_message"),
            parse_mode="html"
        )

        return

    if not user.crm_id or not user.is_verified:
        await message.reply(
            text=_("err_reply_no_user_message"),
            parse_mode="html"
        )

        return

    bot_message: BotMessage = await db.ex(dmth.GetOne(BotMessage, id=message.reply_to_message.message_id, chat_id=message.chat.id))
    if not bot_message:
        await message.reply(
            text=_("err_reply_no_bot_message"),
            parse_mode="html"
        )

        return

    if bot_message.type == "chat":
        crm_message: ChatMessage = await db.ex(dmth.GetOne(ChatMessage, id=bot_message.crm_id))

    elif bot_message.type == "group":
        crm_message: GroupMessage = await db.ex(dmth.GetOne(GroupMessage, id=bot_message.crm_id))

    else:
        await message.reply(
            text=_("err_reply_no_type_message").format(type=bot_message.type),
            parse_mode="html"
        )

        return

    if not crm_message:
        await message.reply(
            text=_("err_reply_no_crm_message"),
            parse_mode="html"
        )

        return

    try:
        await crm.send_message(crm_message, message)

        if bot_message.type == "chat":
            reciever: CrmUser = await db.ex(dmth.GetOne(CrmUser, chat_id=crm_message.sender_id))

            status_message = await message.reply(
                text=_("ok_chat_reply_message").format(name=reciever.fullname),
                parse_mode="html"
            )

        elif bot_message.type == "group":
            group: Group = await db.ex(dmth.GetOne(Group, id=crm_message.group_id))

            status_message = await message.reply(
                text=_("ok_group_reply_message").format(name=group.title),
                parse_mode="html"
            )

        else:
            raise ValueError

        new_bot_message = BotMessage(
            id=status_message.message_id,
            chat_id=status_message.chat.id,
            type=bot_message.type,
            crm_id=crm_message.id
        )
        await db.ex(dmth.AddOne(BotMessage, new_bot_message))

    except Exception as err:
        logger.exception(err)

        await message.reply(
            text=_("err_reply_message"),
            parse_mode="html"
        )
