
from emitter import emitter, EventType
from loguru import logger

from datetime import datetime
from telegram import bot, i18n

from db import Db
from dtypes.db import method as dmth
from dtypes.lead import Lead, LeadGroup

from config import get_config


db = Db()


@emitter.on(EventType.public_log_message)
async def public_log_message():
    pass
