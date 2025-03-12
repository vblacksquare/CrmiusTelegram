
from dtypes.db import DatabaseItem


class Notification(DatabaseItem):
    def __init__(
        self,
        id: int,
        sender_id: int,
        reciever_id: int,
        task_id: int,
        type: str,
        message_id: int = None
    ):

        self.id = id
        self.sender_id = sender_id
        self.reciever_id = reciever_id
        self.task_id = task_id
        self.type = type
        self.message_id = message_id

        self.fields = ["id", "sender_id", "reciever_id", "task_id", "type", "message_id"]
