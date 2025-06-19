
from emitter import emitter, EventType
from loguru import logger

from datetime import datetime
from telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.lead import Lead, LeadGroup

from config import get_config


db = Db()


@emitter.on(EventType.new_lead)
async def new_lead(lead: Lead):
    if lead.source_domain in [None, "", " "] or lead.email in [None, "", " "]:
        logger.warning(f"Lead skipped -> {lead.to_dict()}")
        return

    logger.debug(f"New lead -> {lead.to_dict()}")

    language = get_config().telegram.languages[0]
    nothing = i18n.gettext("nothing", locale=get_config().telegram.languages[0])

    data = {
        "subject": lead.subject if lead.subject else nothing,
        "full_name": lead.full_name if lead.full_name else nothing,
        "phone": lead.phone if lead.phone else nothing,
        "email": lead.email if lead.email else nothing,
        "date": datetime.fromtimestamp(lead.added_time).strftime("%Y-%m-%d %H:%M") if lead.added_time else nothing,
        "page": lead.source_page,
        "source_domain": lead.source_domain.replace(".", ""),
        "status": "new"
    }

    lead_group: LeadGroup = await db.ex(dmth.GetOne(LeadGroup, {"$or": [{"email": lead.email}], "source_domain": lead.source_domain}))

    if lead_group:
        #if lead.email and lead.email not in lead_group.email:
        #    lead_group.email.append(lead.email)

        #if lead.phone and lead.phone not in lead_group.phone:
        #    lead_group.phone.append(lead.phone)

        #await db.ex(dmth.UpdateOne(LeadGroup, lead_group, to_update=["email", "phone"]))
        pass

    else:
        thread_id = await create_topic(lead.full_name, lead.source_domain, language)

        lead_group = LeadGroup(
            id=lead.id,
            email=[lead.email],
            phone=[lead.phone],
            thread_id=thread_id,
            source_domain=lead.source_domain
        )
        await db.ex(dmth.AddOne(LeadGroup, lead_group))

    message = None
    for i in range(3):
        try:
            message = await bot.send_message(
                chat_id=get_config().telegram.lead_group_id,
                message_thread_id=lead_group.thread_id,
                text=i18n.gettext("lead_msg", locale=language).format(**data),
                parse_mode="HTML"
            )

            break

        except Exception as err:
            if "message thread not found" in str(err):
                lead_group.thread_id = await create_topic(lead.full_name, lead.source_domain, language)
                await db.ex(dmth.UpdateOne(LeadGroup, lead_group, to_update=["thread_id"]))
                continue

            logger.exception(err)

    if not message:
        return

    if lead.message:
        await bot.send_message(
            chat_id=get_config().telegram.lead_group_id,
            message_thread_id=lead_group.thread_id,
            text=i18n.gettext("lead_message_msg", locale=language).format(
                message=lead.message
            ),
            parse_mode="HTML",
            reply_to_message_id=message.message_id
        )


async def create_topic(name: str, domain: str, language: str):
    topic = await bot.create_forum_topic(
        chat_id=get_config().telegram.lead_group_id,
        name=i18n.gettext("lead_topic_name", locale=language).format(
            name=name,
            tags=' '.join([f"#{domain}", "#new"])
        ),
        icon_custom_emoji_id="5417915203100613993"
    )

    return topic.message_thread_id
