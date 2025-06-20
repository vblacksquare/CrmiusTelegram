import json

import aiomysql
import asyncio

from loguru import logger
from datetime import datetime

from utils.convert import string_to_uuid
from .db import Db
from dtypes.db import method as dmth
from dtypes.user import CrmUser
from dtypes.lead import Lead
from dtypes.message import GroupMessage, ChatMessage, TaskMessage
from dtypes.notification import Notification
from dtypes.task import Task
from dtypes.group import Group

from utils.singleton import SingletonMeta

from config import get_config


db = Db()


class CrmDb(metaclass=SingletonMeta):
    def __init__(self):
        self.log = logger.bind(classname=self.__class__.__name__)

        self.host = get_config().crmdatabase.hostname
        self.port = get_config().crmdatabase.port
        self.user = get_config().crmdatabase.username
        self.password = get_config().crmdatabase.password
        self.db = get_config().crmdatabase.db

        self.chat_host = get_config().chatdatabase.hostname
        self.chat_port = get_config().chatdatabase.port
        self.chat_user = get_config().chatdatabase.username
        self.chat_password = get_config().chatdatabase.password
        self.chat_db = get_config().chatdatabase.db

        self.updated = 0

    async def connection(self, is_chat: bool = False) -> aiomysql.Connection:
        if is_chat:
            return await aiomysql.connect(
                host=self.chat_host,
                port=self.chat_port,
                user=self.chat_user,
                password=self.chat_password,
                db=self.chat_db,
                loop=asyncio.get_running_loop(),
                charset='utf8mb4'
            )

        else:
            return await aiomysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db,
                loop=asyncio.get_running_loop(),
                charset='utf8mb4'
            )

    async def get_task_message_by_id(self, message_id: int) -> TaskMessage:
        conn = await self.connection()
        cur = await conn.cursor()

        try:

            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT id, content, taskid, staffid, dateadded FROM tbltask_comments WHERE id=%s", (message_id, ))
            raw_message = await cur.fetchone()

            if not raw_message:
                await cur.close()
                conn.close()

                return None

            raw_message = list(raw_message)

            sent_time = raw_message[-1]
            raw_message[-1] = sent_time.timestamp()

            message = TaskMessage(*raw_message)

            await cur.close()
            conn.close()

            return message

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return None

    async def get_tasks(self) -> list[Task]:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT id, name FROM tbltasks")
            raw_tasks = await cur.fetchall()

            tasks = []
            for raw_task in raw_tasks:
                raw_task = list(raw_task)
                tasks.append(Task(*raw_task))

            await cur.close()
            conn.close()

            return tasks

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return []

    async def get_task_by_id(self, task_id: int) -> Task:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT id, name FROM tbltasks WHERE id = %s", (task_id,))
            raw_task = await cur.fetchone()

            if not raw_task:
                await cur.close()
                conn.close()

                return None

            raw_task = list(raw_task)
            return Task(*raw_task)

        except Exception as err:
            self.log.exception(err)
            await cur.close()
            conn.close()

            return None

    async def vire_with_chat(self, users: list[CrmUser]) -> list[CrmUser]:
        conn = await self.connection(is_chat=True)
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT user_id, email_address FROM gr_site_users")
            raw_users = await cur.fetchall()
            dict_raw_users = {}

            for raw_user in raw_users:
                user_id, email_address = raw_user
                dict_raw_users.update({email_address: user_id})

            new_users = []
            for user in users:
                if user.login not in dict_raw_users:
                    continue

                user.chat_id = dict_raw_users[user.login]
                new_users.append(user)

            await cur.close()
            conn.close()

            return new_users

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return users

    async def get_users(self) -> list[CrmUser]:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT staffid, email, password, firstname, lastname, profile_image FROM tblstaff")
            raw_users = await cur.fetchall()

            users = []
            for raw_user in raw_users:
                raw_user = list(raw_user)
                raw_user[-1] = f"https://innova.crmius.com/uploads/staff_profile_images/{raw_user[0]}/" + "{size}_" + f"{raw_user[-1]}"

                users.append(CrmUser(*raw_user))

            await cur.close()
            conn.close()

            return await self.vire_with_chat(users)

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return None

    async def get_user_by_login(self, login: str) -> CrmUser:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT staffid, email, password, firstname, lastname FROM tblstaff WHERE email = %s", (login,))
            raw_user = await cur.fetchone()

            if not raw_user:
                await cur.close()
                conn.close()

                return None

            raw_user = list(raw_user)

            return (await self.vire_with_chat([CrmUser(*raw_user)]))[0]

        except Exception as err:
            self.log.exception(err)
            await cur.close()
            conn.close()

            return None

    async def get_user_by_id(self, user_id: int) -> CrmUser:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT staffid, email, password, firstname, lastname FROM tblstaff WHERE staffid = %s", (int(user_id),))
            raw_user = await cur.fetchone()

            if not raw_user:
                await cur.close()
                conn.close()

                return None

            raw_user = list(raw_user)

            await cur.close()
            conn.close()

            return await self.vire_with_chat([CrmUser(*raw_user)])

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return None

    async def get_groups(self) -> list[Group]:
        conn = await self.connection(is_chat=True)
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")

            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT group_id, name, slug FROM gr_groups")
            raw_groups = await cur.fetchall()

            groups = {}
            for raw_group in raw_groups:
                raw_group = list(raw_group)

                group = Group(*raw_group)

                groups.update({
                    group.id: group
                })

            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT group_id, user_id FROM gr_group_members")
            participants = await cur.fetchall()

            for group_id, member_id in participants:
                groups[group_id].participants.append(member_id)

            await cur.close()
            conn.close()

            return list(groups.values())

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return []

    async def get_group_by_id(self, group_id) -> Group:
        conn = await self.connection(is_chat=True)
        cur = await conn.cursor()

        try:

            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT group_id, name FROM gr_groups WHERE id=%s", (int(group_id),))
            raw_group = await cur.fetchone()

            if not raw_group:
                await cur.close()
                conn.close()

                return None

            raw_group = list(raw_group)
            group = Group(*raw_group)

            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT group_id, user_id FROM gr_groups_members WHERE group_id=%s", (int(group_id),))
            participants = await cur.fetchall()

            for group_id, member_id in participants:
                group.participants.append(member_id)

            await cur.close()
            conn.close()

            return group

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return None

    async def get_group_messages(self, from_id: int = 0) -> list[GroupMessage]:
        conn = await self.connection(is_chat=True)
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT * FROM gr_group_messages WHERE group_message_id > %s", (from_id,))
            raw_messages = await cur.fetchall()

            messages = []
            for raw_message in raw_messages:
                raw_message = list(raw_message)

                sent_time: datetime = raw_message[-2]
                raw_message[-2] = sent_time.timestamp()

                messages.append(GroupMessage(
                    id=raw_message[0],
                    group_id=raw_message[1],
                    text=str(raw_message[3]),
                    sender_id=raw_message[2],
                    time_sent=raw_message[-2],
                    attachments=eval(raw_message[8]) if raw_message[8] else None,
                ))

            await cur.close()
            conn.close()

            if len(messages):
                await db.ex(dmth.AddMany(GroupMessage, messages))
            return messages

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return []

    async def get_chat_messages(self, from_id: int = 0) -> list[ChatMessage]:
        conn = await self.connection(is_chat=True)
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT * FROM gr_private_chat_messages WHERE private_chat_message_id > %s", (from_id,))
            raw_messages = await cur.fetchall()

            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT private_conversation_id, initiator_user_id, recipient_user_id FROM gr_private_conversations")
            raw_chats = await cur.fetchall()
            dict_raw_chats = {raw_chat[0]: raw_chat[1:] for raw_chat in raw_chats}

            messages = []
            for raw_message in raw_messages:
                raw_message = list(raw_message)

                sent_time = raw_message[-2]
                raw_message[-2] = sent_time.timestamp()

                message = ChatMessage(
                    id=raw_message[0],
                    sender_id=raw_message[2],
                    reciever_id=None,
                    text=raw_message[3],
                    viewed=False,
                    time_sent=raw_message[-2],
                    viewed_at=raw_message[-2],
                    chat_id=raw_message[1],
                    attachments=eval(raw_message[8]) if raw_message[8] else None,
                )

                temp_users = dict_raw_chats[message.chat_id]
                for user in temp_users:
                    if user != message.sender_id:
                        message.reciever_id = user
                        break

                messages.append(message)

            await cur.close()
            conn.close()

            if len(messages):
                await db.ex(dmth.AddMany(ChatMessage, messages))
            return messages

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return []

    async def get_task_notifications(self, from_id: int = 0) -> list[Notification]:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT id, description, fromuserid, touserid, link FROM tblnotifications WHERE id > %s", (from_id,))
            raw_notifications = await cur.fetchall()

            notifications = []
            for raw_notification in raw_notifications:
                id, notification_type, sender_id, reciever_id, link = raw_notification

                args = link.split("#")[1:]

                if len(args) == 2:
                    task_arg, message_arg = args

                elif len(args) == 1:
                    task_arg = args[0]
                    message_arg = None

                else:
                    continue

                if not task_arg:
                    continue

                key, task_id = task_arg.split("=")
                if key != "taskid":
                    continue

                task_id = int(task_id)

                message_id = None
                if message_arg:
                    key, message_id = message_arg.split("_")
                    message_id = int(message_id)

                notification = Notification(
                    id=id,
                    sender_id=sender_id,
                    reciever_id=reciever_id,
                    task_id=task_id,
                    type=notification_type,
                    message_id=message_id
                )

                notifications.append(notification)

            return notifications

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return []

    async def get_last_chat_message_id(self) -> str:
        conn = await self.connection(is_chat=True)
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT Max(private_chat_message_id) FROM gr_private_chat_messages")
            raw_message_id = await cur.fetchone()

            await cur.close()
            conn.close()

            return raw_message_id[0]

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return None

    async def get_last_group_message_id(self) -> str:
        conn = await self.connection(is_chat=True)
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT Max(group_message_id) FROM gr_group_messages")
            raw_message_id = await cur.fetchone()

            await cur.close()
            conn.close()

            return raw_message_id[0]

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return None

    async def get_last_task_notification_id(self) -> str:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT Max(id) FROM tblnotifications")
            raw_message_id = await cur.fetchone()

            await cur.close()
            conn.close()

            return raw_message_id[0]

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return None

    async def get_leads(self, from_id: int = 0) -> list[Lead]:
        conn = await self.connection()
        cur = await conn.cursor()

        try:
            await cur.execute("SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'")
            await cur.execute("SELECT id, lead_edata FROM tblleads WHERE id > %s AND lead_edata is not NULL", (from_id,))
            raw_leads = await cur.fetchall()

            leads = []
            for raw_lead in raw_leads:
                crm_id, data = raw_lead

                lead = Lead(**json.loads(data))
                lead.crm_id = crm_id

                leads.append(lead)

            return leads

        except Exception as err:
            self.log.exception(err)

            await cur.close()
            conn.close()

            return []
