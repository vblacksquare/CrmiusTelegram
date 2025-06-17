
from dtypes.db import DatabaseItem


class Email(DatabaseItem):
    def __init__(
        self,
        id: str,
        login: str,
        password: str,
        imap_port: int,
        imap_host: str,
        smpt_port: int,
        smpt_host: str,
        domain: str,
    ):

        self.id = id
        self.login = login
        self.password = password
        self.imap_port = imap_port
        self.imap_host = imap_host
        self.smpt_port = smpt_port
        self.smpt_host = smpt_host
        self.domain = domain

        self.fields = [
            "id",
            "login", "password",
            "imap_port", "imap_host",
            "smpt_port", "smpt_host",
            "domain"
        ]
