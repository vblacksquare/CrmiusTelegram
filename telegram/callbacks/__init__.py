
from .chat import __new_chat_message, __new_chat_audio_message, __new_chat_photo_message
from .group import __new_group_message, __new_group_audio_message, __new_group_photo_message
from .task import __new_task_notification
from .base import base_callback


async def new_chat_message(*args, crm_msg_id, **kwargs):
    await base_callback(crm_msg_id=crm_msg_id, message_type="chat", callback=__new_chat_message(*args, **kwargs))


async def new_chat_audio_message(*args, crm_msg_id, **kwargs):
    await base_callback(crm_msg_id=crm_msg_id, message_type="chat", callback=__new_chat_audio_message(*args, **kwargs))


async def new_chat_photo_message(*args, crm_msg_id, **kwargs):
    await base_callback(crm_msg_id=crm_msg_id, message_type="chat", callback=__new_chat_photo_message(*args, **kwargs))


async def new_group_message(*args, crm_msg_id, **kwargs):
    await base_callback(crm_msg_id=crm_msg_id, message_type="group", callback=__new_group_message(*args, **kwargs))


async def new_group_audio_message(*args, crm_msg_id, **kwargs):
    await base_callback(crm_msg_id=crm_msg_id, message_type="group", callback=__new_group_audio_message(*args, **kwargs))


async def new_group_photo_message(*args, crm_msg_id, **kwargs):
    await base_callback(crm_msg_id=crm_msg_id, message_type="group", callback=__new_group_photo_message(*args, **kwargs))


async def new_task_notification(*args, **kwargs):
    await base_callback(crm_msg_id=None, message_type="task", callback=__new_task_notification(*args, **kwargs))
