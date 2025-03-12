
from dtypes.db import DatabaseItem


class Plan(DatabaseItem):
    def __init__(
        self,
        id: int,
        to_chat: str
    ):

        self.id = id

        self.fields = ["id"]
