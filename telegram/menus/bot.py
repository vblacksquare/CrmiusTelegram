
from loguru import logger

from aiogram import Router
from aiogram.types import Message

from grupo import Grupo

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.user import User, CrmUser

from config import get_config


bot_router = Router()
db = Db()
gr = Grupo()


@bot_router.message()
async def reply(message: Message):
    print(message.from_user)

    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))

    try:
        if not user.is_verified:
            raise ValueError

        if not message.text:
            raise ValueError

        sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=user.crm_id))
        reciever: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=get_config().grupo.chat_robot))

        await gr.send_chat_message(
            sender=sender,
            reciever=reciever,
            message_text=message.text
        )

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "👍"}]
        )

    except Exception as err:
        logger.exception(err)

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "👎"}]
        )