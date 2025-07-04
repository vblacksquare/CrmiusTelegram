
from loguru import logger
import bs4

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
        "text": prepare_text(message.text) if message else None,
        "type": notification.type,
        "title": task.title
    }
    data = {key: str(kwargs[key]) for key in kwargs}
    logger.debug(f"Sending message -> {data}")

    emitter.emit(
        EventType.send_task,
        **kwargs
    )


def prepare_text(message: str) -> str:
    soup = bs4.BeautifulSoup(message if isinstance(message, str) else message.text, "html.parser")

    for comment in soup.find_all(string=lambda text: isinstance(text, bs4.element.Comment)):
        comment.extract()

    is_p_like = False

    p_tag = soup.find("p")
    if p_tag:
        is_p_like = True

    for tag in soup.find_all():
        if isinstance(tag, bs4.element.Tag):
            if tag.name == "p":
                tag.insert_before("\n")
                tag.unwrap()

            elif tag.name == "br":
                if not is_p_like:
                    tag.insert_before("\n")
                tag.unwrap()

            elif tag.name not in ["b", "strong", "i", "em", "u", "s", "strike", "del", "tg-spoiler", "a", "code", "pre"]:
                tag.unwrap()

            else:
                tag.attrs = {key: value for key, value in tag.attrs.items() if key == "href"}

    decoded_text = soup.decode()

    cleared_text = ""
    for i, char in enumerate(decoded_text):
        if char != "\n":
            cleared_text = decoded_text[i:]
            break

    text = cleared_text

    if len(text) > 1000:
        text = text[:1000] + f"... (+{len(text) - 1000})"

    if isinstance(message, str):
        return text

    else:
        message.text = text
        return message
