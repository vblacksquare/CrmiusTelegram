
from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Telegram(BaseModel):
    bot_token: str
    lead_group_id: int
    languages: list[str] = ["ru", "uk"]
    commands: list[str] = ["/start"]


class Database(BaseModel):
    uri: str
    name: str


class CrmDatabase(BaseModel):
    hostname: str = "127.0.0.1"
    username: str = ""
    password: str = ""
    port: int = 5432
    db: str = "db"


class ChatDatabase(BaseModel):
    hostname: str = "127.0.0.1"
    username: str = ""
    password: str = ""
    port: int = 5432
    db: str = "db"


class Crm(BaseModel):
    hostname: str
    dev_hostname: str

    @property
    def url(self) -> str:
        return f"https://{self.hostname}/admin/authentication?l={{login}}&p={{password}}"

    @property
    def redirect_url(self) -> str:
        return f"https://{self.hostname}/redirect_v1.html?l={{login}}&p={{password}}&r={{redirect}}"

    @property
    def private_chat_url(self) -> str:
        return f"https://{self.hostname}/chat/{{username}}/chat/"

    @property
    def group_chat_url(self) -> str:
        return f"https://{self.hostname}/chat/{{name}}/"

    @property
    def task_url(self) -> str:
        return f"https://{self.hostname}/admin/tasks/view/{{task_id}}"

    @property
    def dev_url(self) -> str:
        return f"https://{self.dev_hostname}/admin/authentication?l={{login}}&p={{password}}"


class Grupo(BaseModel):
    token: str
    chat_robot: str
    translator_robot: str
    writer_robot: str
    endpoint: str


class Logger(BaseModel):
    path: str = "resources/logs"
    level: str = "DEBUG"


class Resources(BaseModel):
    locales_path: str = "resources/locales"
    audios_path: str = "resources/audios"


class Settings(BaseSettings):
    telegram: Telegram
    database: Database
    crmdatabase: CrmDatabase
    chatdatabase: ChatDatabase
    crm: Crm
    grupo: Grupo
    logger: Logger
    resources: Resources

    model_config = SettingsConfigDict(
        env_file=f".env",
        case_sensitive=False,
        env_nested_delimiter="__",
    )


@lru_cache(maxsize=1)
def get_config() -> Settings:
    return Settings()
