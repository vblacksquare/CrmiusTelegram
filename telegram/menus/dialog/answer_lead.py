
from loguru import logger

from aiogram import Router, F
from aiogram.types import Message

import aiosmtplib
from email.message import EmailMessage

from grupo import Grupo

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User
from dtypes.lead import Lead, LeadGroup
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

        await send(
            from_email=email,
            to_email=lead_group.email[-1],
            text=message.text
        )

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "👍"}]
        )

    except Exception as err:
        logger.exception(err)

        await message.bot.set_message_reaction(
            message.chat.id, message.message_id, reaction=[{"type": "emoji", "emoji": "😡"}]
        )


async def send(from_email: Email, to_email: str, text: str, subject: str = None, files: list[str] = []):
    message = EmailMessage()
    message["From"] = from_email.login
    message["To"] = to_email
    # message["Subject"] = subject
    message.set_content(text)

    client = aiosmtplib.SMTP(hostname=from_email.smpt_host, port=from_email.smpt_port, start_tls=True)
    await client.connect()
    await client.login(from_email.login, from_email.password)

    await client.send_message(
        message=message,
        sender=from_email.login,
        recipients=[to_email],
    )

    client.close()
