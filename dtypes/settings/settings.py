
from dtypes.db import DatabaseItem


class Settings(DatabaseItem):
    def __init__(
        self,
        id: str = "main",

        last_group_message_id: int = 0,
        last_chat_message_id: int = 0,
        last_task_notification_id: int = 0,

        last_lead_id: int = 0
    ):

        self.id = id
        self.last_group_message_id = last_group_message_id
        self.last_chat_message_id = last_chat_message_id
        self.last_task_notification_id = last_task_notification_id
        self.last_lead_id = last_lead_id

        self.fields = [
            "id",
            "last_group_message_id", "last_chat_message_id", "last_task_notification_id",
            "last_lead_id"
        ]
