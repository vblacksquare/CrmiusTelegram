
from dtypes.db import DatabaseItem


class AgentThread(DatabaseItem):
    def __init__(
        self,
        id: str,
        user_id: int
    ):

        self.id = id
        self.user_id = user_id

        self.fields = ["id", "user_id"]
