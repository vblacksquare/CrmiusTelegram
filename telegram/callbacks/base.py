
from loguru import logger

from aiogram.types import Message

from db import Db
from dtypes.db import method as dmth
from dtypes.message import BotMessage


db = Db()


async def base_callback(crm_msg_id: int, message_type: str, callback):
    messages = []

    try:
        messages: list[Message] = await callback

    except Exception as err:
        logger.exception(err)

    if not crm_msg_id:
        return

    if not messages:
        logger.warning(f"No message sent so skip -> {crm_msg_id}:{message_type}")
        return

    if not isinstance(messages, list):
        messages = [messages]

    to_add = []
    for message in messages:
        to_add.append(
            BotMessage(
                id=message.message_id,
                chat_id=message.chat.id,
                type=message_type,
                crm_id=crm_msg_id
            )
        )

    await db.ex(dmth.AddMany(BotMessage, to_add))
