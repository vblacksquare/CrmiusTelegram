
import bs4
import uuid
import json
from loguru import logger

import aioimaplib
import email
import email.utils
import email.policy
from email.header import Header

from agent import parser_agent

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from emitter import emitter, EventType

from db import Db
from dtypes.db import method as dmth
from dtypes.email import Email
from dtypes.lead import Lead, LeadGroup, LeadMessage

db = Db()
added_email_ids = {}


async def email_job(_email: Email):
    client = added_email_ids[_email.id]

    await client.select('INBOX')
    status, data = await client.search("UNSEEN")

    if status != "OK":
        logger.warning(f"Got search response from imap: {status = }, {data = }")
        data = [b""]

    message_ids = data[0].split()
    for message_id in message_ids:
        message_id = message_id.decode()

        message_bytes = (await client.fetch(message_id, "(RFC822)")).lines[1]
        await process_message(message_bytes)


async def update_email_jobs(scheduler: AsyncIOScheduler):
    emails: list[Email] = await db.ex(dmth.GetMany(Email))
    new_email_ids = list(map(lambda x: x.id, emails))

    for email in emails:
        if email.id in added_email_ids:
            continue

        client = aioimaplib.IMAP4_SSL(host=email.imap_host, port=email.imap_port)
        await client.wait_hello_from_server()
        response = await client.login(email.login, email.password)
        logger.debug(f"Login {email}-> {response}")

        added_email_ids.update({email.id: client})
        scheduler.add_job(
            id=email.id,
            func=email_job,
            trigger=IntervalTrigger(seconds=1),
            kwargs={'_email': email}
        )

    for email_id in list(added_email_ids):
        if email_id in new_email_ids:
            continue

        del added_email_ids[email_id]
        scheduler.remove_job(email_id)


async def process_message(message_bytes):
    try:
        message = email.message_from_bytes(message_bytes)
        message_id, html, files, subject, sender = await get_message_data(message)

        lead_group: LeadGroup = await db.ex(dmth.GetOne(LeadGroup, email=sender))
        if not lead_group:
            logger.warning(f"Message from unknown lead -> {sender}")
            return

        answer = await parser_agent.send(
            chat_id="q",
            context={
                "fields": {
                    "text": "the first message in html from email message"
                },
                "page_link": None
            },
            text=html
        )
        data = json.loads(answer.content)

        lead_message = LeadMessage(
            id=uuid.uuid4().hex,
            email_id=message_id,
            lead_group_id=lead_group.id,
            raw_text=html,
            text=data["text"],
            from_client=True
        )

        emitter.emit(
            EventType.new_lead_message,
            lead_message=lead_message
        )

    except Exception as err:
        logger.exception(err)


async def get_message_data(message):
    text_html = None
    files = []

    message_id = message.get("Message-ID")

    sender = email.utils.parseaddr(message.get('From'))[1]

    subject, encoder = email.header.decode_header(message["Subject"])[0]
    if encoder:
        subject = subject.decode(encoder)

    if isinstance(subject, bytes):
        subject = subject.decode(encoding="utf-8")

    if subject in ["", " "] or not len(subject.replace(" ", "")):
        subject = None

    for part in message.walk():
        if part.get_content_type() == 'text/html' and text_html is None:
            text_html = part.get_payload(decode=True).decode()

        elif part.get_content_disposition() in ["attachment"] or part.get_content_maintype() in ['image']:
            filename = part.get_filename()

            if not filename:
                print(filename)
                continue

            filename = email.header.decode_header(filename)[0][0]
            if isinstance(filename, bytes):
                filename = filename.decode()

            file_id = uuid.uuid4().hex.replace("-", "")
            # file_path = os.path.join(Config().public_path, file_id)
            file_data = part.get_payload(decode=True)

            # async with aiofiles.open(file_path, "wb") as f:
            #    await f.write()

            """file = File(
                id=file_id,
                path=file_path,
                name=filename
            )
            await self.db.ex(dmth.AddOne(File, file))
            files.append(file.id)"""

    return message_id, text_html, files, subject, sender

