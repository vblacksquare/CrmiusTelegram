
import uuid
from datetime import datetime
from loguru import logger

from aiogram import Router, F
from aiogram.types import Message

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

        lead: Lead = await db.ex(dmth.GetOne(Lead, id=lead_group.id))
        messages: list[LeadMessage] = await db.ex(dmth.GetMany(LeadMessage, lead_group_id=lead_group.id))

        new_message = LeadMessage(
            id=uuid.uuid4().hex,
            lead_group_id=lead_group.id,
            text=message.text,
            from_client=False
        )

        await send(
            from_email=email,
            to_email=lead_group.email[-1],
            text=await prepare_message(
                new_message=new_message,
                history=messages,
                manager_email=email,
                lead=lead,
                lead_group=lead_group
            )
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
    subject: str = None,
    files: list[str] = []
):

    message = MIMEText(text, 'html', 'utf-8')
    message['From'] = from_email.login
    message['To'] = to_email

    if subject:
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
    lead_group: LeadGroup
):

    history = history[:]

    parts = [
        f"Вы заполнили форму <b>{lead.source_page_name}</b> на сайте <a href='{lead.source_page}'>{lead.source_page}</a>"
    ]

    if lead.message:
        parts.append(lead.message)

    history.append(LeadMessage(
        id=1,
        lead_group_id=1,
        text="<br><br>".join(parts),
        from_client=True,
        sent_at=lead.added_time
    ))

    last_message = ""
    for message in history[::-1]:
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
            datetime.fromtimestamp(message.sent_at).strftime(f"%y.%m.%d %H:%M"),
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
