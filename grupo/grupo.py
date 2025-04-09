
import aiohttp
from aiogram.types import Message
from loguru import logger

from db import Db
from dtypes.db import method as dmth
from dtypes.group import Group
from dtypes.user import User, CrmUser
from dtypes.task import Task
from dtypes.message import ChatMessage, GroupMessage

from config import GRUPO_ENDPOINT, GRUPO_TOKEN
from utils.singleton import SingletonMeta


db = Db()


class Grupo(metaclass=SingletonMeta):
    def __init__(self):
        self.log = logger.bind(classname=self.__class__.__name__)

    async def send_group_message(self, group: Group, sender: CrmUser, message_text: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=GRUPO_ENDPOINT,
                    data={
                        "api_secret_key": GRUPO_TOKEN,
                        "add": "message",
                        "group": group.id,
                        "sender": sender.login,
                        "message": message_text
                    }
                ) as response:

                    self.log.info(f"Sent message response -> {await response.text()}")

        except Exception as err:
            self.log.exception(err)

    async def send_chat_message(self, sender: CrmUser, reciever: CrmUser, message_text: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=GRUPO_ENDPOINT,
                    data={
                        "api_secret_key": GRUPO_TOKEN,
                        "add": "message",
                        "user": reciever.login,
                        "sender": sender.login,
                        "message": message_text
                    }
                ) as response:

                    self.log.info(f"Sent message response -> {await response.text()}")

        except Exception as err:
            self.log.exception(err)

    async def reply_to_message(self, crm_message: ChatMessage | GroupMessage, message: Message):
        tuser: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))
        sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=tuser.crm_id))

        if isinstance(crm_message, ChatMessage):
            reciever: CrmUser = await db.ex(dmth.GetOne(CrmUser, chat_id=crm_message.sender_id))

            await self.send_chat_message(sender=sender, reciever=reciever, message_text=message.text)

        elif isinstance(crm_message, GroupMessage):
            group: Group = await db.ex(dmth.GetOne(Group, id=crm_message.group_id))

            await self.send_group_message(group=group, sender=sender, message_text=message.text)

    async def send_raw_notification(self, sender: CrmUser, receiver: CrmUser, description: str, task: Task, additional_data) -> None:
        pass

