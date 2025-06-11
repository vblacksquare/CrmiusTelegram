
import asyncio
import html
import os.path

import pydub

import aiohttp
import uuid

import bs4
import functools

from loguru import logger

from dtypes.lead import Lead
from grupo import Grupo
from agent import taras_agent, danila_agent, vasiliy_agent

from db import Db, CrmDb
from dtypes import Notification
from dtypes.db import method as dmth
from dtypes.settings import Settings
from dtypes.user import User, CrmUser
from dtypes.group import Group
from dtypes.message import ChatMessage, GroupMessage
from dtypes.task import Task

from utils.singleton import SingletonMeta

from config import get_config


AGENTS = {
    get_config().grupo.chat_robot: taras_agent,
    get_config().grupo.translator_robot: danila_agent,
    get_config().grupo.writer_robot: vasiliy_agent
}

semaphore = asyncio.Semaphore(8)


async def _cork(*args, **kwargs):
    pass


class Updater(metaclass=SingletonMeta):
    def __init__(self, loop: asyncio.BaseEventLoop):
        self.loop = loop

        self.db = Db()
        self.crm = CrmDb()
        self.gr = Grupo()

        self.log = logger.bind(classname=self.__class__.__name__)

        self.tasks = [
            self.new_chat_messages, self.new_group_messages,
            self.new_task_notifications
        ]
        self.long_tasks = [
            self.new_users, self.new_groups, self.new_tasks
        ]
        self.__tasks = []

        self.short_task_func = None
        self.long_task_func = None

        self.delay = 1
        self.long_delay = 60

        self.plan_sent_time = 0

        self.callback_chat_message = _cork
        self.callback_chat_audio_message = _cork
        self.callback_chat_photo_message = _cork
        self.callback_chat_document_message = _cork

        self.callback_group_message = _cork
        self.callback_group_audio_message = _cork
        self.callback_group_photo_message = _cork
        self.callback_group_document_message = _cork

        self.callback_task_notification = _cork

        self.callback_lead = _cork

    def get_text_type(self, message: ChatMessage | GroupMessage) -> str:
        if not message.attachments or not len(message.attachments):
            return "text"

        if "screenshot" in message.attachments:
            return "screenshot"

        try:
            first_attachment = message.attachments[0]

            if first_attachment["file_type"] == "image\\/png":
                return "photo"

            elif first_attachment["file_type"] == "text\\/plain":
                return "document"

            else:
                self.log.warning(f"Unknown attachment type -> {message.attachments}")
                return "text"

        except Exception as err:
            self.log.exception(err)

            return "text"

    def prepare_text(self, message: ChatMessage | GroupMessage | str) -> ChatMessage | GroupMessage:
        soup = bs4.BeautifulSoup(message if isinstance(message, str) else message.text, "html.parser")

        for comment in soup.find_all(string=lambda text: isinstance(text, bs4.element.Comment)):
            comment.extract()

        is_p_like = False

        p_tag = soup.find("p")
        if p_tag:
            is_p_like = True

        for tag in soup.find_all():
            if isinstance(tag, bs4.element.Tag):
                if tag.name == "p":
                    tag.insert_before("\n")
                    tag.unwrap()

                elif tag.name == "br":
                    if not is_p_like:
                        tag.insert_before("\n")
                    tag.unwrap()

                elif tag.name not in ["b", "strong", "i", "em", "u", "s", "strike", "del", "tg-spoiler", "a", "code", "pre"]:
                    tag.unwrap()

                else:
                    tag.attrs = {key: value for key, value in tag.attrs.items() if key == "href"}

        decoded_text = soup.decode()

        cleared_text = ""
        for i, char in enumerate(decoded_text):
            if char != "\n":
                cleared_text = decoded_text[i:]
                break

        text = cleared_text

        if len(text) > 1000:
            text = text[:1000] + f"... (+{len(text)-1000})"

        if isinstance(message, str):
            return text

        else:
            message.text = text
            return message

    def prepare_audio_text(self, message: ChatMessage | GroupMessage) -> str:
        audio_file = message.attachments["audio_message"].replace("\\", "")

        return f"https://innova.crmius.com/chat/{audio_file}"

    def prepare_photo_text(self, message: ChatMessage | GroupMessage) -> list[str]:
        backslashes = "\\"

        return [
            f"https://innova.crmius.com/chat/{image['file'].replace(backslashes, '')}"
            for image in message.attachments
        ]

    def prepare_screenshot_text(self, message: ChatMessage | GroupMessage) -> str:
        backslashes = "\\"

        return [message.attachments["screenshot"].replace(backslashes, '')]

    def prepare_document_text(self, message: ChatMessage | GroupMessage) -> list[list[str, str]]:
        return [
            [
                f"https://innova.crmius.com/chat/download/attachment/group_id/{message.group_id}/message_id/{message.id}/attachment_index/{i}",
                document['name']
            ]
            for i, document in enumerate(message.attachments)
        ]

    async def prepare_audio(self, url) -> str:
        def func():
            audio = pydub.AudioSegment.from_ogg(audio_raw_path)
            audio.export(audio_encoded_path, format="ogg", codec="libopus")

        audio_id = uuid.uuid4().hex
        audio_raw_path = os.path.join(get_config().resources.audios_path, f"{audio_id}.webm")
        audio_encoded_path = os.path.join(get_config().resources.audios_path, f"{audio_id}_opus.ogg")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.read()
                with open(audio_raw_path, "wb") as f:
                    f.write(data)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, func)

        return audio_encoded_path

    async def prepare_photos(self, urls) -> list[str]:
        return urls

    async def prepare_documents(self, urls) -> list[str]:
        return urls

    async def find_task(self, task_id: int) -> Task:
        user: CrmUser = await self.db.ex(dmth.GetOne(Task, id=task_id))

        if not user:
            user = await self.crm.get_task_by_id(task_id=task_id)

        return user

    async def find_user(self, user_id: int, by_crm: bool = False) -> CrmUser:
        if by_crm:
            user: CrmUser = await self.db.ex(dmth.GetOne(CrmUser, id=user_id))

        else:
            user: CrmUser = await self.db.ex(dmth.GetOne(CrmUser, chat_id=user_id))

        return user

    async def find_users(self, user_ids: list[int], by_crm: bool = False) -> list[CrmUser]:
        if by_crm:
            users: list[CrmUser] = await self.db.ex(dmth.GetMany(CrmUser, id={"$in": user_ids}))

        else:
            users: list[CrmUser] = await self.db.ex(dmth.GetMany(CrmUser, chat_id={"$in": user_ids}))

        return users

    async def find_group(self, group_id: str) -> Group:
        group: Group = await self.db.ex(dmth.GetOne(Group, id=group_id))

        if not group:
            group = await self.crm.get_group_by_id(group_id)

        return group

    async def to_agent(self, agent_receiver, sender_user, reciever_user, message):
        resp = await agent_receiver.send(str(sender_user.id), message.text, context=sender_user.to_dict())
        resp = self.prepare_text(resp.content)
        await self.gr.send_chat_message(sender=reciever_user, reciever=sender_user, message_text=resp)

    async def notificate_chat_message(self, message: ChatMessage, forward_to: CrmUser = None) -> None:
        try:
            sender_user = await self.find_user(message.sender_id)
            reciever_user = await self.find_user(message.reciever_id)

            text_type = self.get_text_type(message)

            self.log.info(f"New chat message: {sender_user.login} -> {reciever_user.login} {message.id}@{text_type}")

            if text_type == "text":
                self.prepare_text(message)
                await self.callback_chat_message(sender=sender_user, reciever=reciever_user, text=message.text, forward_to=forward_to, crm_msg_id=message.id)

            elif text_type == "audio":
                audio = self.prepare_audio_text(message)
                audio_path = await self.prepare_audio(audio)
                self.prepare_text(message)
                await self.callback_chat_audio_message(sender=sender_user, reciever=reciever_user, caption=message.text, audio=audio_path, forward_to=forward_to, crm_msg_id=message.id)

            elif text_type == "photo":
                photos = self.prepare_photo_text(message)
                photos_paths = await self.prepare_photos(photos)
                self.prepare_text(message)
                await self.callback_chat_photo_message(sender=sender_user, reciever=reciever_user, caption=message.text, photos=photos_paths, forward_to=forward_to, crm_msg_id=message.id)

            elif text_type == "screenshot":
                photos = self.prepare_screenshot_text(message)
                photos_paths = await self.prepare_photos(photos)
                self.prepare_text(message)
                await self.callback_chat_photo_message(sender=sender_user, reciever=reciever_user, caption=message.text, photos=photos_paths, forward_to=forward_to, crm_msg_id=message.id)

            elif text_type == "document":
                documents = self.prepare_document_text(message)
                documents_paths = await self.prepare_documents(documents)
                self.prepare_text(message)
                await self.callback_chat_document_message(sender=sender_user, reciever=reciever_user, caption=message.text, documents=documents_paths, forward_to=forward_to, crm_msg_id=message.id)

            else:
                self.log.warning(f"No such text type supported: {text_type} -> {message.id}")
                return

            agent_receiver = AGENTS.get(reciever_user.login)

            if not agent_receiver or forward_to:
                return

            elif reciever_user.login in [
                get_config().grupo.chat_robot, get_config().grupo.writer_robot
            ] and sender_user.login == get_config().grupo.translator_robot:
                return

            asyncio.create_task(self.to_agent(agent_receiver, sender_user, reciever_user, message))

        except Exception as err:
            self.log.exception(err)

    async def new_chat_messages(self):
        settings: Settings = await self.db.ex(dmth.GetOne(Settings, id="main"))
        old_last_message_id = settings.last_chat_message_id
        new_last_message_id = 0

        chat_messages = await self.crm.get_chat_messages(from_id=old_last_message_id)

        admins: list[User] = await self.db.ex(dmth.GetMany(User, role="top_admin"))
        admins_crm: list[CrmUser] = await self.find_users([admin.crm_id for admin in admins if admin.crm_id], by_crm=True)

        for chat_message in chat_messages:
            self.log.debug(f"Got new message {chat_message.sender_id} -> {chat_message.reciever_id}: {chat_message.text}")

            message_id = chat_message.id
            if message_id > new_last_message_id:
                new_last_message_id = message_id

            await self.notificate_chat_message(chat_message)

            for admin_crm in admins_crm:
                if admin_crm.chat_id not in [chat_message.sender_id, chat_message.reciever_id]:
                    await self.notificate_chat_message(chat_message, forward_to=admin_crm)

        if new_last_message_id > old_last_message_id:
            settings.last_chat_message_id = new_last_message_id
            await self.db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_chat_message_id"]))

    async def notificate_group_message(self, message: GroupMessage):
        try:
            group = await self.find_group(message.group_id)

            sender_user = await self.find_user(message.sender_id)
            reciever_users = await self.find_users(group.participants)

            text_type = self.get_text_type(message)

            self.log.info(f"New group message: {sender_user.login} -> {group.slug} {message.id}@{text_type}")

            if text_type == "text":
                self.prepare_text(message)
                callback = functools.partial(self.callback_group_message, text=message.text, crm_msg_id=message.id)

            elif text_type == "audio":
                audio = self.prepare_audio_text(message)
                audio_path = await self.prepare_audio(audio)
                self.prepare_text(message)
                callback = functools.partial(self.callback_group_audio_message, caption=message.text, audio=audio_path, crm_msg_id=message.id)

            elif text_type == "photo":
                photos = self.prepare_photo_text(message)
                photos_paths = await self.prepare_photos(photos)
                self.prepare_text(message)
                callback = functools.partial(self.callback_group_photo_message, caption=message.text, photos=photos_paths, crm_msg_id=message.id)

            elif text_type == "screenshot":
                photos = self.prepare_screenshot_text(message)
                photos_paths = await self.prepare_photos(photos)
                self.prepare_text(message)
                callback = functools.partial(self.callback_group_photo_message, caption=message.text, photos=photos_paths, crm_msg_id=message.id)

            elif text_type == "document":
                documents = self.prepare_document_text(message)
                documents_paths = await self.prepare_documents(documents)
                self.prepare_text(message)
                callback = functools.partial(self.callback_group_document_message, caption=message.text, documents=documents_paths, crm_msg_id=message.id)

            else:
                self.log.warning(f"No such text type supported: {text_type} -> {message.id}")
                return

            for reciever_user in reciever_users:
                if reciever_user.id == sender_user.id:
                    continue

                await callback(sender=sender_user, reciever=reciever_user, group=group)

            admins: list[User] = await self.db.ex(dmth.GetMany(User, role="top_admin"))
            admins_crm: list[CrmUser] = await self.find_users([admin.crm_id for admin in admins if admin.crm_id], by_crm=True)
            for admin_crm in admins_crm:
                if admin_crm.chat_id not in group.participants:
                    await callback(sender=sender_user, reciever=admin_crm, group=group, forward_to=admin_crm)

        except Exception as err:
            self.log.exception(err)

    async def new_group_messages(self):
        settings: Settings = await self.db.ex(dmth.GetOne(Settings, id="main"))
        old_last_message_id = settings.last_group_message_id
        new_last_message_id = 0

        chat_messages = await self.crm.get_group_messages(from_id=old_last_message_id)

        for chat_message in chat_messages:
            message_id = chat_message.id
            if message_id > new_last_message_id:
                new_last_message_id = message_id

            await self.notificate_group_message(chat_message)

        if new_last_message_id > old_last_message_id:
            settings.last_group_message_id = new_last_message_id
            await self.db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_group_message_id"]))

    async def notificate_task_action(self, notification: Notification):
        try:
            task = await self.find_task(notification.task_id)
            sender = await self.find_user(notification.sender_id, by_crm=True)
            reciever = await self.find_user(notification.reciever_id, by_crm=True)

            if notification.message_id:
                message = await self.crm.get_task_message_by_id(notification.message_id)
                if message:
                    message.text = html.unescape(html.unescape(message.text))
                    self.prepare_text(message)

            else:
                message = None

            await self.callback_task_notification(sender=sender, reciever=reciever, task=task, notification_type=notification.type, message=message)

        except Exception as err:
            self.log.exception(err)

    async def new_task_notifications(self):
        settings: Settings = await self.db.ex(dmth.GetOne(Settings, id="main"))
        old_last_task_notification_id = settings.last_task_notification_id
        new_last_task_notification_id = 0

        task_notifications = await self.crm.get_task_notifications(from_id=old_last_task_notification_id)

        for task_notification in task_notifications:
            if task_notification.id > new_last_task_notification_id:
                new_last_task_notification_id = task_notification.id

            await self.notificate_task_action(task_notification)

        if new_last_task_notification_id > old_last_task_notification_id:
            settings.last_task_notification_id = new_last_task_notification_id
            await self.db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_task_notification_id"]))

    async def new_tasks(self):
        new_tasks = await self.crm.get_tasks()

        old_tasks: list[Task] = await self.db.ex(dmth.GetMany(Task))
        old_tasks_ids: list[str] = list(map(lambda x: x.id, old_tasks))

        to_add = []

        for new_task in new_tasks:
            if new_task.id in old_tasks_ids:
                await self.db.ex(dmth.UpdateOne(Task, new_task))

            else:
                to_add.append(new_task)

        if len(to_add):
            await self.db.ex(dmth.AddMany(Task, to_add))

    async def new_groups(self):
        new_groups = await self.crm.get_groups()

        old_groups: list[Group] = await self.db.ex(dmth.GetMany(Group))
        old_groups_ids: list[str] = list(map(lambda x: x.id, old_groups))

        to_add = []

        for new_group in new_groups:
            if new_group.id in old_groups_ids:
                await self.db.ex(dmth.UpdateOne(Group, new_group))

            else:
                to_add.append(new_group)

        if len(to_add):
            await self.db.ex(dmth.AddMany(Group, to_add))

    async def new_users(self):
        new_users = await self.crm.get_users()

        if new_users is None:
           return

        new_users_ids = list(map(lambda x: x.id, new_users))

        old_users: list[CrmUser] = await self.db.ex(dmth.GetMany(CrmUser))
        old_users_ids: list[str] = list(map(lambda x: x.id, old_users))

        to_add = []

        for new_user in new_users:
            if new_user.id in old_users_ids:
                await self.db.ex(dmth.UpdateOne(CrmUser, new_user, to_update=["id", "login", "password", "first_name", "last_name", "image", "chat_id"]))

            else:
                to_add.append(new_user)

        if len(to_add):
            await self.db.ex(dmth.AddMany(CrmUser, to_add))

        for old_user in old_users:
            if old_user.id in new_users_ids:
                continue

            await self.db.ex(dmth.RemoveOne(CrmUser, old_user))

            if not old_user.user_id:
                continue

            tuser: User = await self.db.ex(dmth.GetOne(User, id=old_user.user_id))

            if not tuser:
                continue

            tuser.crm_id = None
            tuser.is_verified = False
            await self.db.ex(dmth.UpdateOne(User, tuser, to_update=["crm_id", "is_verified"]))

    async def notificate_new_lead(self, lead: Lead):
        await self.callback_lead(lead)

    async def new_leads(self):
        settings: Settings = await self.db.ex(dmth.GetOne(Settings, id="main"))
        old_lead_id = settings.last_lead_id
        new_lead_id = 0

        leads = await self.crm.get_leads(from_id=settings.last_lead_id)
        await self.db.ex(dmth.AddMany(Lead, leads))

        for lead in leads:
            if lead.crm_id > new_lead_id:
                new_lead_id = lead.crm_id

            await self.notificate_new_lead(lead)

        if new_lead_id > old_lead_id:
            settings.last_lead_id = new_lead_id
            await self.db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_lead_id"]))

    async def task_wrapper(self, func, delay):
        while True:
            try:
                await func()

            except Exception as err:
                self.log.error(f"Occurred error with {func.__name__} -> {err}")
                self.log.exception(err)

            await asyncio.sleep(delay)

    async def run(self):
        try:
            for task in self.tasks:
                self.__tasks.append(asyncio.create_task(self.task_wrapper(task, self.delay)))
                self.log.info(f"Started task -> {task.__name__}")

            for task in self.long_tasks:
                self.__tasks.append(asyncio.create_task(self.task_wrapper(task, self.long_delay)))
                self.log.info(f"Started task -> {task.__name__}")

        except Exception as err:
            self.log.exception(err)
