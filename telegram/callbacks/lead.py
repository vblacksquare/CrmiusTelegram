
from datetime import datetime

from telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.lead import Lead, LeadGroup

from config import get_config


db = Db()


async def __new_lead(lead):
    language = get_config().telegram.languages[0]
    nothing = i18n.gettext("nothing", locale=get_config().telegram.languages[0])

    data = {
        "subject": lead.subject.split(":", maxsplit=1)[-1].strip() if lead.subject else nothing,
        "full_name": lead.full_name if lead.full_name else nothing,
        "phone": lead.phone if lead.phone else nothing,
        "email": lead.email if lead.email else nothing,
        "date": datetime.fromtimestamp(lead.added_time).strftime("%Y-%m-%d %H:%M") if lead.added_time else nothing,
        "page": lead.source_page
    }

    lead_group: LeadGroup = await db.db[LeadGroup.__name__].find_one({"$or": [{"email": lead.email}, {"phone": "lead.phone"}]})
    if lead_group:
        if lead.email:
            lead_group.email.append(lead.email)

        if lead.phone:
            lead_group.phone.append(lead.phone)

        await db.ex(dmth.UpdateOne(LeadGroup, lead_group, to_update=["email", "phone"]))

    else:
        topic = await bot.create_forum_topic(
            chat_id=get_config().telegram.lead_group_id,
            name=lead.full_name
        )

        lead_group = LeadGroup(
            id=lead.id,
            email=[lead.email],
            phone=[lead.phone],
            thread_id=topic.message_thread_id
        )
        await db.ex(dmth.AddOne(LeadGroup, lead_group))

    await bot.send_message(
        chat_id=get_config().telegram.lead_group_id,
        message_thread_id=lead_group.thread_id,
        text=i18n.gettext("lead_msg", locale=language).format(**data),
        parse_mode="HTML"
    )

    if lead.message:
        await bot.send_message(
            chat_id=get_config().telegram.lead_group_id,
            message_thread_id=lead_group.thread_id,
            text=i18n.gettext("lead_message_msg", locale=language).format(
                message=lead.message
            ),
            parse_mode="HTML"
        )
