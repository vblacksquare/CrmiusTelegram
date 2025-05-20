
import asyncio
import json
import pytz
from datetime import datetime

from loguru import logger as log

from db import Db
from grupo import Grupo

from dtypes.db import method as dmth
from dtypes.user import CrmUser, User
from dtypes.group import Group
from dtypes.message import ChatMessage

from telegram import i18n

from AgentService.connector import AgentConnector

from config import GRUPO_BOT, GRUPO_TRANSLATOR_BOT


async def get_chats(data: str, chat_id: str):
    db = Db()

    chats: list[CrmUser] = await db.ex(dmth.GetMany(CrmUser))
    groups: list[Group] = await db.ex(dmth.GetMany(Group))

    return [
        *[
            {"first_name": chat.first_name, "last_name": chat.last_name, "email": chat.login, "type": "private"}
            for chat in chats
        ],
        *[
            {"name": group.title, "slug": group.slug, "type": "group"}
            for group in groups
        ]
    ]


async def send_private_message(data: str, chat_id: str):
    db = Db()
    gr = Grupo()

    chat_id = int(chat_id)

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=chat_id))
    tsender: User = await db.ex(dmth.GetOne(User, id=sender.user_id))

    data = json.loads(data)
    text = data["text"]
    email = data["target"]

    formatted_text = i18n.gettext("gpt_generated", locale=tsender.language).format(text=text)
    crm_reciever: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=email))

    await gr.send_chat_message(sender=sender, reciever=crm_reciever, message_text=formatted_text)

    return "ok"


async def send_group_message(data: str, chat_id: str):
    db = Db()
    gr = Grupo()

    chat_id = int(chat_id)

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=chat_id))
    tsender: User = await db.ex(dmth.GetOne(User, id=sender.user_id))

    data = json.loads(data)
    text = data["text"]
    slug = data["target"]

    formatted_text = i18n.gettext("gpt_generated", locale=tsender.language).format(text=text)
    group: Group = await db.ex(dmth.GetOne(Group, slug=slug))

    await gr.send_group_message(sender=sender, group=group, message_text=formatted_text)

    return "ok"


async def translate(data: str, chat_id: str):
    db = Db()
    gr = Grupo()

    data = json.loads(data)
    text = data["text"]
    target_language = data["target_language"]

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=GRUPO_BOT))
    receiver: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=GRUPO_TRANSLATOR_BOT))

    await gr.send_chat_message(sender=sender, reciever=receiver, message_text=f"{text}\n\nTranslate to {target_language}")

    t1 = datetime.now(pytz.timezone("Europe/Kiev")).timestamp()
    t2 = t1 + 1

    message = None
    while t2 - t1 < 30 and message is None:
        message: ChatMessage = await db.ex(dmth.GetOne(ChatMessage, sender_id=sender.chat_id, reciever_id=receiver.chat_id, time_sent={"gt": t1}))

        t2 = datetime.now(pytz.timezone("Europe/Kiev")).timestamp()
        await asyncio.sleep(3)

    if message is None:
        return f"No response from translator Danila"

    return message.text


taras_agent = AgentConnector(endpoint="https://bots.innova.ua/agents/taras/")
taras_agent.bind_tool_output("get_chats", get_chats)
taras_agent.bind_tool_output("send_private_message", send_private_message)
taras_agent.bind_tool_output("send_group_message", send_group_message)
taras_agent.bind_tool_output("translate", translate)
