
from dtypes.db import DatabaseItem


class LeadGroup(DatabaseItem):
    def __init__(
        self,
        id: str,
        email: str,
        phone: str,
        thread_id: int
    ):

        self.id = id
        self.email = email
        self.phone = phone
        self.thread_id = thread_id

        self.fields = ["id", "email", "phone", "thread_id"]
