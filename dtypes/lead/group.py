
from dtypes.db import DatabaseItem


class LeadGroup(DatabaseItem):
    def __init__(
        self,
        id: str,
        email: list[str],
        phone: list[str],
        source_domain: str,
        thread_id: int
    ):

        self.id = id
        self.email = email
        self.phone = phone
        self.source_domain = source_domain
        self.thread_id = thread_id

        self.fields = ["id", "email", "phone", "source_domain", "thread_id"]
