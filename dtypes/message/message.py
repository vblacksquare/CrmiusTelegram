
from dtypes.db import DatabaseItem


class GroupMessage(DatabaseItem):
    def __init__(
        self,
        id: str,
        group_id: str,
        text: str,
        sender_id: str,
        time_sent: int,
        attachments: dict = None
    ):

        self.id = id
        self.group_id = group_id
        self.text = text
        self.sender_id = sender_id
        self.time_sent = time_sent
        self.attachments = attachments if attachments else {}

        self.fields = ["id", "group_id", "text", "sender_id", "time_sent", "attachments"]


class ChatMessage(DatabaseItem):
    def __init__(
        self,
        id: str,
        sender_id: str,
        reciever_id: str,
        text: str,
        viewed: bool,
        time_sent: int,
        viewed_at: int,
        chat_id: int = None,
        attachments: dict = None
    ):

        self.id = id
        self.sender_id = sender_id
        self.reciever_id = reciever_id
        self.text = text
        self.viewed = viewed
        self.time_sent = time_sent
        self.viewed_at = viewed_at
        self.chat_id = chat_id
        self.attachments = attachments if attachments else {}

        self.fields = ["id", "sender_id", "reciever_id", "text", "viewed", "time_sent", "viewed_at", "chat_id", "attachments"]


class TaskMessage(DatabaseItem):
    def __init__(
        self,
        id: int,
        text: str,
        task_id: int,
        sender_id: int,
        time_sent: int
    ):

        self.id = id
        self.task_id = task_id
        self.text = text
        self.sender_id = sender_id
        self.time_sent = time_sent

        self.fields = ["id", "task_id", "text", "sender_id", "time_sent"]


class BotMessage(DatabaseItem):
    def __init__(
        self,
        id: int,
        chat_id: int,
        type: str,
        crm_id: str
    ):

        self.id = id
        self.chat_id = chat_id
        self.type = type
        self.crm_id = crm_id

        self.fields = ["id", "chat_id", "type", "crm_id"]
