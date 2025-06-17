
from aiogram.types import Message
from loguru import logger
from emitter import emitter, EventType

from telegram import bot, i18n

from db import Db
from dtypes.user import CrmUser
from dtypes.message import PublicMessagesGroup
from dtypes.db import method as dmth
from dtypes.group import Group

from config import get_config


db = Db()


@emitter.on(EventType.public_log_message)
async def public_log_message(
    sender: CrmUser,
    reciever: CrmUser,
    group: Group,
    messages: list[Message],
    is_cork: bool
):

    chat_id = get_config().telegram.public_messages_group_id

    if group:
        dialog_ids = sorted([group.id])
        left_name = group.title
        right_name = ""
        icon = "5350513667144163474"

    else:
        dialog_ids = sorted([sender.id, reciever.id])
        left_name = sender.fullname
        right_name = reciever.fullname
        icon = "5417915203100613993"

    messages_group: PublicMessagesGroup = await db.ex(dmth.GetOne(PublicMessagesGroup, participant_ids=dialog_ids))
    if not messages_group:
        thread_id = await create_topic(chat_id, left_name, right_name, icon)

        messages_group = PublicMessagesGroup(
            id="-".join(map(str, dialog_ids)),
            participant_ids=dialog_ids,
            thread_id=thread_id
        )
        await db.ex(dmth.AddOne(PublicMessagesGroup, messages_group))

    for i in range(3):
        try:
            for message in messages:
                await message.copy_to(chat_id=get_config().telegram.public_messages_group_id, message_thread_id=messages_group.thread_id)

                if not is_cork:
                    continue

                try:
                    await message.delete()

                except Exception as err:
                    logger.exception(err)

            break

        except Exception as err:
            if "message thread not found" in str(err):
                messages_group.thread_id = await create_topic(chat_id, left_name, right_name, icon)
                await db.ex(dmth.UpdateOne(PublicMessagesGroup, messages_group, to_update=["thread_id"]))
                break

            logger.exception(err)


async def create_topic(
    chat_id: int,
    left_name: str,
    right_name: str,
    icon: str
):

    topic = await bot.create_forum_topic(
        chat_id=chat_id,
        name=i18n.gettext("public_messages_group_topic_name", locale="ru").format(
            left=left_name,
            right=right_name
        ),
        icon_custom_emoji_id=icon
    )

    return topic.message_thread_id
