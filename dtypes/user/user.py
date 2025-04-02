
from dtypes.db import DatabaseItem


class User(DatabaseItem):
    def __init__(
        self,
        id: int,
        first_name: str,
        second_name: str,
        username: str,
        language: str,
        role: str = "user",
        crm_id: int = None,
        is_verified: bool = False,
        time: list[int, int] = None,
    ):

        self.id = id
        self.first_name = first_name
        self.second_name = second_name
        self.username = username
        self.language = language
        self.role = role
        self.crm_id = crm_id
        self.is_verified = is_verified
        self.time = time if time else [0, 24]

        self.fields = [
            "id", "first_name", "second_name", "username", "language",
            "role", "crm_id", "is_verified", "time"
        ]


class CrmUser(DatabaseItem):
    def __init__(
        self,
        id: int,
        login: str,
        password: str,
        first_name: str,
        last_name: str,
        image: str = "https://innova.crmius.com/assets/images/groups/5.png",
        user_id: int = None,
        not_hashed_password: str = None,
        chat_id: int = None,
    ):

        self.id = id
        self.login = login
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.image = image
        self.user_id = user_id
        self.not_hashed_password = not_hashed_password
        self.chat_id = chat_id

        self.fields = ["id", "login", "password", "first_name", "last_name", "image", "user_id", "not_hashed_password", "chat_id"]

    @property
    def username(self):
        return self.login.split("@")[0]

    @property
    def fullname(self):
        return " ".join((self.first_name, self.last_name))

    @property
    def short_image(self):
        return self.image.split("{size}_")[-1]
