
from loguru import logger

from emitter import emitter, EventType

from db import Db, CrmDb
from dtypes.db import method as dmth
from dtypes.user import CrmUser
from dtypes.task import Task
from dtypes.notification import Notification
from dtypes.message import TaskMessage


db = Db()
crm = CrmDb()


@emitter.on(EventType.new_task)
async def new_task(notification: Notification):
    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=notification.sender_id))
    reciever: CrmUser = await db.ex(dmth.GetOne(CrmUser, id=notification.reciever_id))
    task: Task = await db.ex(dmth.GetOne(Task, id=notification.task_id))

    message = None
    if notification.message_id:
        message = await crm.get_task_message_by_id(notification.message_id)

    kwargs = {
        "task_id": task.id,
        "sender": sender,
        "reciever": reciever,
        "text": message.text if message else None,
        "type": notification.type,
        "title": task.title
    }
    data = {key: str(kwargs[key]) for key in kwargs}
    logger.debug(f"Sending message -> {data}")

    emitter.emit(
        EventType.send_task,
        **kwargs
    )
