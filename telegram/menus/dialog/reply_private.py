

from loguru import logger

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from grupo import Grupo

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User
from dtypes.message import GroupMessage, ChatMessage, BotMessage


reply_private_router = Router()
db = Db()
gr = Grupo()


@reply_private_router.message(F.reply_to_message & F.chat.type == ChatType.PRIVATE)
async def reply_private(message: Message):
    print(message.reply_to_message, message.chat.type)
    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))

    if not user or not user.crm_id or not user.is_verified:
        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "😡"}]
        )
        return

    bot_message: BotMessage = await db.ex(dmth.GetOne(BotMessage, id=message.reply_to_message.message_id, chat_id=message.chat.id))
    if not bot_message:
        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "😡"}]
        )
        return

    if bot_message.type == "chat":
        crm_message: ChatMessage = await db.ex(dmth.GetOne(ChatMessage, id=bot_message.crm_id))

    elif bot_message.type == "group":
        crm_message: GroupMessage = await db.ex(dmth.GetOne(GroupMessage, id=bot_message.crm_id))

    else:
        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "😡"}]
        )
        return

    if not crm_message:
        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "😡"}]
        )
        return

    try:
        await gr.reply_to_message(crm_message, message)

        if bot_message.type in ["chat", "group"]:
            await message.bot.set_message_reaction(
                message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "👍"}]
            )

        else:
            raise ValueError

    except Exception as err:
        logger.exception(err)

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "😡"}]
        )
