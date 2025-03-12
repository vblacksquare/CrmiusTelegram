
from dtypes.db import DatabaseItem


class Task(DatabaseItem):
    def __init__(
        self,
        id: int,
        title: str
    ):

        self.id = id
        self.title = title

        self.fields = ["id", "title"]
