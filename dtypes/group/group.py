
from dtypes.db import DatabaseItem


class Group(DatabaseItem):
    def __init__(
        self,
        id: str,
        title: str,
        slug: str,
        participants: list[str] = None
    ):

        self.id = id
        self.title = title
        self.slug = slug
        self.participants = participants if participants else []

        self.fields = ["id", "title", "slug", "participants"]

    @property
    def presence(self):
        return f"presence-{self.title}"
