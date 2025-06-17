
from dtypes.db import DatabaseItem


class PublicMessagesGroup(DatabaseItem):
    def __init__(
        self,
        id: str,
        participant_ids: list[int],
        thread_id: int
    ):

        self.id = id
        self.participant_ids = participant_ids
        self.thread_id = thread_id

        self.fields = ["id", "participant_ids", "thread_id"]


class PrivateMessagesGroup(DatabaseItem):
    def __init__(
        self,
        id: str,
        participant_ids: list[int],
        group_id: int,
        thread_id: int
    ):

        self.id = id
        self.participant_ids = participant_ids
        self.group_id = group_id
        self.thread_id = thread_id

        self.fields = ["id", "participant_ids", "group_id", "thread_id"]
