
from emitter import emitter, EventType

from telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.lead import LeadGroup, LeadMessage

from config import get_config


db = Db()


@emitter.on(EventType.new_lead_message)
async def new_lead_message(lead_message: LeadMessage):
    language = "ru"

    lead_group: LeadGroup = await db.ex(dmth.GetOne(LeadGroup, id=lead_message.lead_group_id))
    await bot.send_message(
        chat_id=get_config().telegram.lead_group_id,
        message_thread_id=lead_group.thread_id,
        text=i18n.gettext("lead_message_msg", locale=language).format(
            message=lead_message.text
        ),
        parse_mode="HTML"
    )

    await db.ex(dmth.AddOne(LeadMessage, lead_message))
