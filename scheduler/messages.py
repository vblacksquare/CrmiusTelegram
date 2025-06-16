
from emitter import emitter, EventType

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.settings import Settings


db = Db()
crm = CrmDb()


async def load_private_messages():
    settings: Settings = await db.ex(dmth.GetOne(Settings, id="main"))
    old_last_message_id = settings.last_chat_message_id
    new_last_message_id = 0

    messages = await crm.get_chat_messages(from_id=old_last_message_id-1)

    for message in messages:
        message_id = message.id
        if message_id > new_last_message_id:
            new_last_message_id = message_id

        emitter.emit(EventType.new_message, message)

    #if new_last_message_id > old_last_message_id:
    #    settings.last_chat_message_id = new_last_message_id
    #    await db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_chat_message_id"]))


async def load_group_messages():
    settings: Settings = await db.ex(dmth.GetOne(Settings, id="main"))
    old_last_message_id = settings.last_group_message_id
    new_last_message_id = 0

    messages = await crm.get_group_messages(from_id=old_last_message_id-1)

    for message in messages:
        message_id = message.id
        if message_id > new_last_message_id:
            new_last_message_id = message_id

        emitter.emit(EventType.new_message, message)

    #if new_last_message_id > old_last_message_id:
    #    settings.last_group_message_id = new_last_message_id
    #    await db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_group_message_id"]))

