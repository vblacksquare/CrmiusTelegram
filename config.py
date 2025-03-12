
import os

# telegram
COMMANDS = ["/start"]


LANGUAGES = ["ru", "uk"]
DEFAULT_LANGUAGE = LANGUAGES[0]


BOT_TOKEN = "7555915267:AAEwr4VCqpWNeDIJml65xFvx63OODxnVghc"
BOT_USERNAME = "crmius_bot"


TEST_USER = 885554630


ROLE_INDEX = {
    "top_admin": 2,
    "admin": 1,
    "user": 0
}


# db
MONGODB_URI = "mongodb://root:7c8ef10155504bffb8df21044034a79a@46.175.150.63:27017"
MONGODB_NAME = "CrmiusBot"


link = "mongodb://dmarket:q2230f9j230f9j@46.175.150.63:27017"

# crm db
CRM_HOST = "185.253.219.177"
CRM_PORT = 3306
CRM_USER = "innova_crm"
CRM_PASS = "CRM235689"
CRM_NAME = "innova_crm"

CHAT_CRM_HOST = "213.136.88.71"
CHAT_CRM_PORT = 3306
CHAT_CRM_USER = "innova_chat"
CHAT_CRM_PASS = "chat235689"
CHAT_CRM_NAME = "innova_chat"

# grupochat api
GRUPO_TOKEN = "JXeGxvoDc8CVq0"
GRUPO_ENDPOINT = "https://innova.crmius.com/chat/api_request/"
GRUPO_BOT = "robot@crmius.com"
GRUPO_DEV = "minka@mmix.ua"


# crm links
ROOT_PORTAL = "https://innova.crmius.com/admin/authentication?l={login}&p={password}"
DEV_PORTAL = "https://developer.crmius.com/admin/authentication?l={login}&p={password}"


# logs
LOGS_LEVEL = "DEBUG"


# resources
RESOURCES_DIR = "resources"
LOGS_DIR = os.path.join(RESOURCES_DIR, "logs")
LOCALES_DIR = os.path.join(RESOURCES_DIR, "locales")
AUDIOS_DIR = os.path.join(RESOURCES_DIR, "audios")
