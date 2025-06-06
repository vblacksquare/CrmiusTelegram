
from dtypes.db import DatabaseItem


class Lead(DatabaseItem):
    def __init__(
        self,
        id: int,
        crm_id: int,
        raw_subject: str,
        raw_content: str,
        is_processed: bool = False,
        is_valid: bool = False
    ):

        self.id = id
        self.crm_id = crm_id
        self.raw_subject = raw_subject
        self.raw_content = raw_content
        self.is_processed = is_processed
        self.is_valid = is_valid

        self.fields = [
            "id",
            "crm_id", "raw_subject", "raw_content",
            "is_processed", "is_valid"
        ]
