
from .task import __new_task_notification
from .lead import __new_lead
from .base import base_callback


async def new_task_notification(*args, **kwargs):
    await base_callback(crm_msg_id=None, message_type="task", callback=__new_task_notification(*args, **kwargs))


async def new_lead(*args, **kwargs):
    await base_callback(crm_msg_id=None, message_type="lead", callback=__new_lead(*args, **kwargs))
