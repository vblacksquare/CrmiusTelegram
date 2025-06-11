
import asyncio
import json
import time

from db import Db
from grupo import Grupo

from dtypes.db import method as dmth
from dtypes.user import CrmUser, User
from dtypes.group import Group
from dtypes.message import ChatMessage

from telegram import i18n

from AgentService.connector import AgentConnector

from config import get_config


TEMP_DATA = {}


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

    TEMP_DATA.update({chat_id: crm_reciever})

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

    TEMP_DATA.update({chat_id: group})

    return "ok"


async def translate(data: str, chat_id: str):
    db = Db()
    gr = Grupo()

    data = json.loads(data)
    text = data["text"]
    target_language = data["target_language"]

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=get_config().grupo.chat_robot))
    receiver: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=get_config().grupo.translator_robot))

    all_messages: list[ChatMessage] = await db.ex(dmth.GetMany(ChatMessage, sender_id=receiver.chat_id, reciever_id=sender.chat_id))
    if len(all_messages):
        last_message_time = max(all_messages, key=lambda x: x.time_sent).time_sent

    else:
        last_message_time = 0

    await gr.send_chat_message(sender=sender, reciever=receiver, message_text=f"{text}\n\nTranslate to {target_language}")

    t1 = time.time()
    t2 = t1 + 1
    message = None

    while t2 - t1 < 30 and message is None:
        message: ChatMessage = await db.ex(dmth.GetOne(
            ChatMessage,
            sender_id=receiver.chat_id,
            reciever_id=sender.chat_id,
            time_sent={"$gt": last_message_time}
        ))

        await asyncio.sleep(1)
        t2 = time.time()

    if message is None:
        return f"No response from translator Danila"

    return message.text


async def generate(data: str, chat_id: str):
    db = Db()
    gr = Grupo()

    data = json.loads(data)
    query = data["query"]

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=get_config().grupo.chat_robot))
    receiver: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=get_config().grupo.writer_robot))

    all_messages: list[ChatMessage] = await db.ex(dmth.GetMany(ChatMessage, sender_id=receiver.chat_id, reciever_id=sender.chat_id))
    if len(all_messages):
        last_message_time = max(all_messages, key=lambda x: x.time_sent).time_sent

    else:
        last_message_time = 0

    await gr.send_chat_message(sender=sender, reciever=receiver, message_text=query)

    t1 = time.time()
    t2 = t1 + 1
    message = None

    while t2 - t1 < 30 and message is None:
        message: ChatMessage = await db.ex(dmth.GetOne(
            ChatMessage,
            sender_id=receiver.chat_id,
            reciever_id=sender.chat_id,
            time_sent={"$gt": last_message_time}
        ))

        await asyncio.sleep(1)
        t2 = time.time()

    if message is None:
        return f"No response from translator Danila"

    return message.text


async def tech_info(data: str, chat_id: str):
    return """
    Crmius-telegram integration:
    1) You need to build interface to work with exactly crmius and one for crmius chat (Grupo chat).
    2) You need to build telegram bot infrastructure with any library you want. In project was used aiogram.
    3) You need to build callbacks to catch event from crmius and crmius chat and then send it to telegram. 
        a) Text message handling
        b) Photo message handling
        c) Document message handling
        d) Audio message handling
        e) Tasks event handling
    4) For crmius deep linking in telegram mini apps you need to generate auto login links (to create session cookies to avoid relogin every time).
    """


taras_agent = AgentConnector(endpoint="https://bots.innova.ua/agents/taras/")
taras_agent.bind_tool_output("get_chats", get_chats)
taras_agent.bind_tool_output("send_private_message", send_private_message)
taras_agent.bind_tool_output("send_group_message", send_group_message)
taras_agent.bind_tool_output("translate", translate)
taras_agent.bind_tool_output("generate", generate)
taras_agent.bind_tool_output("ask_crm_telegram_info", tech_info)
