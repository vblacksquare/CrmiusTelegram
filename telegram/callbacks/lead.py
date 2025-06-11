
from telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.lead import Lead

from config import get_config


db = Db()


async def __new_lead(lead):
    topic = await bot.create_forum_topic(
        chat_id=get_config().telegram.lead_group_id,
        name=lead.subject
    )

    lead.thread_id = topic.message_thread_id
    await db.ex(dmth.UpdateOne(Lead, lead, to_update=["thread_id"]))

    nothing = i18n.gettext("nothing", locale=get_config().telegram.languages[0])

    await bot.send_message(
        chat_id=get_config().telegram.lead_group_id,
        message_thread_id=lead.thread_id,
        text=i18n.gettext("lead_msg", locale=get_config().telegram.languages[0]).format(
            subject=lead.subject if lead.subject else nothing,
            full_name=lead.full_name if lead.full_name else nothing,
            phone=lead.phone if lead.phone else nothing,
            email=lead.email if lead.email else nothing
        ),
        parse_mode="HTML"
    )

    if lead.message:
        await bot.send_message(
            chat_id=get_config().telegram.lead_group_id,
            message_thread_id=lead.thread_id,
            text=i18n.gettext("lead_message_msg", locale=get_config().telegram.languages[0]).format(
                message=lead.message
            ),
            parse_mode="HTML"
        )
