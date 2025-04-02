
import os


# telegram
COMMANDS = ["/start"]


LANGUAGES = ["ru", "uk"]
DEFAULT_LANGUAGE = LANGUAGES[0]
BOT_TOKEN = os.getenv("telegram_token")


# main db
MONGODB_URI = os.getenv("mongo_uri")
MONGODB_NAME = os.getenv("mongo_name", default="CrmiusBot")


# crm db
CRM_HOST = os.getenv("crm_db_host", default="127.0.0.1")
CRM_PORT = int(os.getenv("crm_db_port", default=3306))
CRM_USER = os.getenv("crm_db_user", default="crm")
CRM_PASS = os.getenv("crm_db_pass")
CRM_NAME = os.getenv("crm_db_name", default="crm")


# crm chat db
CHAT_CRM_HOST = os.getenv("chat_db_host", default="127.0.0.1")
CHAT_CRM_PORT = int(os.getenv("chat_db_port", default=3306))
CHAT_CRM_USER = os.getenv("chat_db_user", default="chat")
CHAT_CRM_PASS = os.getenv("chat_db_pass")
CHAT_CRM_NAME = os.getenv("chat_db_name", default="chat")


# hosts
crm_host = os.getenv("crm_host")
dev_crm_host = os.getenv("dev_crm_host")


# grupochat api
GRUPO_TOKEN = os.getenv("chat_token")
GRUPO_ENDPOINT = f"https://{crm_host}/chat/api_request/"
GRUPO_BOT = os.getenv("chat_robot", default="robot@crmius.com")


# crm links
ROOT_PORTAL = f"https://{crm_host}/admin/authentication?l={{login}}&p={{password}}"
ROOT_PORTAL_REDIRECT = f"https://{crm_host}/admin/authentication?l={{login}}&p={{password}}$r={{redirect}}"
DEV_PORTAL = f"https://{dev_crm_host}/admin/authentication?l={{login}}&p={{password}}"


# logs
LOGS_LEVEL = "DEBUG"


# resources
RESOURCES_DIR = "resources"
LOGS_DIR = os.path.join(RESOURCES_DIR, "logs")
LOCALES_DIR = os.path.join(RESOURCES_DIR, "locales")
AUDIOS_DIR = os.path.join(RESOURCES_DIR, "audios")
