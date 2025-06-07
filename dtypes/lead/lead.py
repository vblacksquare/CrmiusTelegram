
from dtypes.db import DatabaseItem


class Lead(DatabaseItem):
    def __init__(
        self,
        id: int,
        crm_id: int,

        raw_subject: str,
        raw_content: str,

        subject: str = None,

        first_name: str = None,
        last_name: str = None,
        sur_name: str = None,

        phone: str = None,
        email: str = None,
        message: str = None,
        service_name: str = None,

        source_page_name: str = None,
        source_page: str = None,
        source: str = None,
        ip: str = None,

        additional_info: dict = None,

        is_processed: bool = False,
        **kwargs
    ):

        self.id = id
        self.crm_id = crm_id

        self.raw_subject = raw_subject
        self.raw_content = raw_content

        self.subject = subject
        self.first_name = first_name
        self.last_name = last_name
        self.sur_name = sur_name
        self.phone = phone
        self.email = email
        self.message = message
        self.service_name = service_name
        self.source_page_name = source_page_name
        self.source_page = source_page
        self.source = source
        self.ip = ip
        self.additional_info = additional_info

        self.is_processed = is_processed

        self.fields = [
            "id", "crm_id",
            "raw_subject", "raw_content",
            "subject", "first_name", "last_name",
            "sur_name", "phone", "email",
            "message", "service_name", "source_page_name",
            "source_page", "source", "ip", "additional_info",
            "is_processed"
        ]
