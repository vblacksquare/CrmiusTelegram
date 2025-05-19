
import json

from db import Db
from grupo import Grupo

from dtypes.db import method as dmth
from dtypes.user import CrmUser, User
from dtypes.group import Group

from telegram import i18n

from AgentService.connector import AgentConnector


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

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=chat_id))
    tsender: User = await db.ex(dmth.GetOne(User, id=sender.chat_id))

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

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=chat_id))
    tsender: User = await db.ex(dmth.GetOne(User, id=sender.chat_id))

    data = json.loads(data)
    text = data["text"]
    slug = data["target"]

    formatted_text = i18n.gettext("gpt_generated", locale=tsender.language).format(text=text)
    group: Group = await db.ex(dmth.GetOne(Group, slug=slug))

    await gr.send_group_message(sender=sender, group=group, message_text=formatted_text)

    return "ok"


taras_agent = AgentConnector(endpoint="https://bots.innova.ua/agents/taras/")
taras_agent.bind_tool_output("get_chats", get_chats)
taras_agent.bind_tool_output("send_private_message", send_private_message)
taras_agent.bind_tool_output("send_group_message", send_group_message)
