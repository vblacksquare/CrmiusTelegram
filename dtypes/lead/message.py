
from dtypes.db import DatabaseItem
from utils import now


class LeadMessage(DatabaseItem):
    def __init__(
        self,
        id: str,
        email_id: str,
        lead_group_id: str,
        text: str,
        from_client: bool,
        sent_at: int = None,
        raw_text: str = None
    ):

        self.id = id
        self.email_id = email_id
        self.lead_group_id = lead_group_id
        self.raw_text = raw_text if raw_text else text
        self.text = text
        self.from_client = from_client
        self.sent_at = sent_at if sent_at else now()

        self.fields = ["id", "email_id", "lead_group_id", "raw_text", "text", "from_client", "sent_at"]
