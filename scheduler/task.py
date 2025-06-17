
from emitter import emitter, EventType

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.settings import Settings


db = Db()
crm = CrmDb()


async def load_tasks():
    settings: Settings = await db.ex(dmth.GetOne(Settings, id="main"))
    old_last_task_notification_id = settings.last_task_notification_id
    new_last_task_notification_id = 0

    task_notifications = await crm.get_task_notifications(from_id=old_last_task_notification_id)

    for task_notification in task_notifications:
        if task_notification.id > new_last_task_notification_id:
            new_last_task_notification_id = task_notification.id

        emitter.emit(EventType.new_task, task_notification)

    if new_last_task_notification_id > old_last_task_notification_id:
        settings.last_task_notification_id = new_last_task_notification_id
        await db.ex(dmth.UpdateOne(Settings, settings, to_update=["last_task_notification_id"]))
