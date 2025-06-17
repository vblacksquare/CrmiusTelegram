
from loguru import logger

from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from grupo import Grupo

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User
from dtypes.lead import Lead, LeadGroup

from config import get_config


answer_lead_router = Router()
db = Db()
gr = Grupo()


@answer_lead_router.message(F.chat.id == get_config().telegram.lead_group_id)
async def answer_lead(message: Message):
    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))

    try:
        if not user.is_verified:
            raise ValueError

        if not message.text:
            raise ValueError

        lead_group: LeadGroup = await db.ex(dmth.GetOne(LeadGroup, thread_id=message.message_thread_id))
        print(lead_group)

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "👍"}]
        )

    except Exception as err:
        logger.exception(err)

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "🚫"}]
        )
