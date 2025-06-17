
from aiogram.types import Message
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
        topic = await bot.create_forum_topic(
            chat_id=get_config().telegram.public_messages_group_id,
            name=i18n.gettext("public_messages_group_topic_name", locale="ru").format(
                left=left_name,
                right=right_name
            ),
            icon_custom_emoji_id=icon
        )

        messages_group = PublicMessagesGroup(
            id="-".join(map(str, dialog_ids)),
            participant_ids=dialog_ids,
            thread_id=topic.message_thread_id
        )
        await db.ex(dmth.AddOne(PublicMessagesGroup, messages_group))

    for message in messages:
        await message.copy_to(chat_id=get_config().telegram.public_messages_group_id, message_thread_id=messages_group.thread_id)

        if is_cork:
            await message.delete()
