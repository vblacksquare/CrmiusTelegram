
import uuid
from datetime import datetime, timezone, timedelta
from loguru import logger

from aiogram import Router, F
from aiogram.types import Message

from telegram import i18n

import aiosmtplib
from email.mime.text import MIMEText
from email.header import Header

from grupo import Grupo

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User
from dtypes.lead import Lead, LeadGroup, LeadMessage
from dtypes.email import Email

from config import get_config


answer_lead_router = Router()
db = Db()
gr = Grupo()

GMT3 = timezone(timedelta(hours=3))
SUPPORTED_LANGUAGES = ["en", "ru", "uk"]


@answer_lead_router.message(F.chat.id == get_config().telegram.lead_group_id)
async def answer_lead(message: Message):
    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))

    try:
        if not user.is_verified:
            raise ValueError("User is not verified")

        if not message.text:
            raise ValueError("Missing text")

        lead_group: LeadGroup = await db.ex(dmth.GetOne(LeadGroup, thread_id=message.message_thread_id))

        email: Email = await db.ex(dmth.GetOne(Email, domain=lead_group.source_domain))
        if not email:
            raise Exception(f"No email for domain -> {lead_group.source_domain}")

        raw_lead = await db.db[Lead.__name__].find_one(
            {"group_id": lead_group.id},
            {"_id": 0},
            sort=[("added_time", -1)]
        )
        lead = Lead(**raw_lead)

        raw_messages = db.db[LeadMessage.__name__].find(
            {"lead_group_id": lead_group.id},
            {"_id": 0},
            sort=[("sent_at", 1)]
        )
        messages = []

        async for raw_message in raw_messages:
            messages.append(LeadMessage(**raw_message))

        language = lead.language if lead.language in SUPPORTED_LANGUAGES else SUPPORTED_LANGUAGES[0]

        new_message = LeadMessage(
            id=uuid.uuid4().hex,
            lead_group_id=lead_group.id,
            text=message.text,
            from_client=False
        )

        subject = lead.subject
        if not subject:
            subject = i18n.gettext("lead_default_subject", locale=language)

        await send(
            from_email=email,
            to_email=lead_group.email[-1],
            text=await prepare_message(
                new_message=new_message,
                history=messages,
                manager_email=email,
                lead=lead,
                lead_group=lead_group,
                language=language
            ),
            subject=subject
        )

        await db.ex(dmth.AddOne(LeadMessage, new_message))

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "👍"}]
        )

    except Exception as err:
        logger.exception(err)

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "😡"}]
        )


async def send(
    from_email: Email,
    to_email: str,
    text: str,
    subject: str = None
):

    message = MIMEText(text, 'html', 'utf-8')
    message['From'] = from_email.login
    message['To'] = to_email
    message['Subject'] = Header(subject, 'utf-8')

    client = aiosmtplib.SMTP(hostname=from_email.smpt_host, port=from_email.smpt_port, use_tls=True)
    await client.connect()
    await client.login(from_email.login, from_email.password)

    await client.sendmail(
        from_email.login,
        [to_email],
        message.as_string()
    )

    client.close()


async def prepare_message(
    new_message: LeadMessage,
    history: list[LeadMessage],
    manager_email: Email,
    lead: Lead,
    lead_group: LeadGroup,
    language: str
):

    history = history[:]

    parts = []

    if lead.source_page_name and lead.source_page:
        parts.append(i18n.gettext("lead_form_sent_full", locale=language).format(
            name=lead.source_page_name,
            source=lead.source_page
        ))

    elif lead.source_page_name:
        parts.append(i18n.gettext("lead_form_sent_name", locale=language).format(
            name=lead.source_page_name
        ))

    elif lead.source_page:
        parts.append(i18n.gettext("lead_form_sent_source", locale=language).format(
            source=lead.source_page
        ))

    if lead.message:
        parts.append(lead.message)

    if len(parts):
        history = [
            LeadMessage(
                id=1,
                lead_group_id=1,
                text=''.join(["<br><br>".join(parts), "<br>"]),
                from_client=True,
                sent_at=lead.added_time
            )
        ] + history

    last_message = ""
    for message in history:
        if message.from_client or not manager_email.sign:
            sender = lead_group.email[0]

            content = "<br><br>".join(
                filter(
                    lambda x: x,
                    [
                        message.text,
                        last_message
                    ]
                )
            )

        else:
            sender = manager_email.login

            content = "<br><br>".join(
                filter(
                    lambda x: x,
                    [
                        message.text,
                        manager_email.sign,
                        last_message
                    ]
                )
            )

        content_meta = ', '.join([
            ''.join([datetime.fromtimestamp(message.sent_at, tz=GMT3).strftime(f"%y.%m.%d %H:%M"), "(gmt+3)"]),
            f"<<a href='mailto:{sender}'>{sender}</a>>:"
        ])

        last_message = "\n".join([
            content_meta,
            '<blockquote style="margin:0px 0px 0px 0.8ex;border-left-width:1px;border-left-style:solid;border-left-color:rgb(204,204,204);padding-left:1ex">',
            content,
            "</blockquote>"
        ])

    if manager_email.sign:
        message = "<br><br>".join([
            new_message.text,
            manager_email.sign,
            last_message
        ])

    else:
        message = "<br><br>".join([
            new_message.text,
            last_message
        ])

    return message
