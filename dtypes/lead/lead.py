
from dtypes.db import DatabaseItem


class Lead(DatabaseItem):
    def __init__(
        self,
        id: int,
        crm_id: int,

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
        source_domain: str = None,
        source: str = None,
        ip: str = None,

        additional_info: dict = None,
        sender: str = None,
        added_time: int = None,

        language: str = None,

        **kwargs
    ):

        self.id = id
        self.crm_id = crm_id

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
        self.source_domain = source_domain
        self.source = source
        self.ip = ip
        self.additional_info = additional_info
        self.sender = sender
        self.added_time = added_time
        self.language = language

        self.fields = [
            "id", "crm_id",
            "subject", "first_name", "last_name",
            "sur_name", "phone", "email",
            "message", "service_name", "source_page_name",
            "source_page", "source_domain", "source", "ip",
            "additional_info", "sender", "added_time", "language"
        ]

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.sur_name]
        name = " ".join([
            part
            for part in parts if part not in ["", " ", None]
        ])

        return name
