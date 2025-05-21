
import asyncio
import time
import json

from db import Db
from dtypes.db import method as dmth
from dtypes.user import CrmUser
from dtypes.message import ChatMessage

from grupo import Grupo

from config import GRUPO_WRITER_BOT, GRUPO_TRANSLATOR_BOT

from AgentService.connector import AgentConnector


async def translate(data: str, chat_id: str):
    db = Db()
    gr = Grupo()

    data = json.loads(data)
    text = data["text"]
    target_language = data["target_language"]

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=GRUPO_WRITER_BOT))
    receiver: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=GRUPO_TRANSLATOR_BOT))

    last_message: ChatMessage = max(
        await db.ex(dmth.GetMany(ChatMessage, sender_id=receiver.chat_id, reciever_id=sender.chat_id)),
        key=lambda x: x.time_sent
    )

    await gr.send_chat_message(sender=sender, reciever=receiver, message_text=f"{text}\n\nTranslate to {target_language}")

    t1 = time.time()
    t2 = t1 + 1
    message = None

    while t2 - t1 < 30 and message is None:
        message: ChatMessage = await db.ex(dmth.GetOne(
            ChatMessage,
            sender_id=receiver.chat_id,
            reciever_id=sender.chat_id,
            time_sent={"$gt": last_message.time_sent}
        ))

        await asyncio.sleep(1)
        t2 = time.time()

    if message is None:
        return f"No response from translator Danila"

    return message.text


vasiliy_agent = AgentConnector(endpoint="https://bots.innova.ua/agents/writer/")
vasiliy_agent.bind_tool_output("translate", translate)
