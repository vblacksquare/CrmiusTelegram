
from loguru import logger

from emitter import emitter, EventType

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.settings import Settings
from dtypes.task import Task


db = Db()
crm = CrmDb()


async def load_task_notifications():
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


async def update_tasks():
    new_tasks = await crm.get_tasks()

    old_tasks: list[Task] = await db.ex(dmth.GetMany(Task))
    old_tasks_ids: list[str] = list(map(lambda x: x.id, old_tasks))

    to_add = []

    for new_task in new_tasks:
        if new_task.id in old_tasks_ids:
            await db.ex(dmth.UpdateOne(Task, new_task))

        else:
            to_add.append(new_task)

    if len(to_add):
        await db.ex(dmth.AddMany(Task, to_add))
