
import bs4
import asyncio
from loguru import logger

from db import Db
from dtypes.db import method as dmth
from dtypes.group import Group
from dtypes.message import ChatMessage, GroupMessage, MessageType
from dtypes.user import CrmUser

from agent import taras_agent, danila_agent, vasiliy_agent

from emitter import emitter, EventType
from config import get_config


db = Db()

AGENTS = {
    get_config().grupo.chat_robot: taras_agent,
    get_config().grupo.translator_robot: danila_agent,
    get_config().grupo.writer_robot: vasiliy_agent
}


@emitter.on(EventType.new_message)
async def new_message(message: ChatMessage | GroupMessage):
    logger.debug(f"New message -> {message.to_dict()}")

    sender: CrmUser = await db.ex(dmth.GetOne(CrmUser, chat_id=message.sender_id))
    recievers: list[CrmUser] = []

    group = None
    audio = None
    photos = []
    documents = []

    if isinstance(message, GroupMessage):
        group: Group = await db.ex(dmth.GetOne(Group, id=message.group_id))
        recievers += await db.ex(dmth.GetMany(CrmUser, chat_id={"$in": group.participants}))

    elif isinstance(message, ChatMessage):
        user = await db.ex(dmth.GetOne(CrmUser, chat_id=message.reciever_id))
        recievers.append(user)

    else:
        raise TypeError(f"Only accepting {GroupMessage} or {ChatMessage}")

    if message.type == MessageType.audio:
        audio = prepare_audio(message)

    elif message.type == MessageType.photo:
        photos = prepare_photo(message)

    elif message.type == MessageType.screenshot:
        photos = prepare_screenshot(message)

    elif message.type == MessageType.document:
        documents = prepare_document(message)

    prepare_text(message)

    for reciever in recievers:
        if reciever.id == sender.id:
            continue

        kwargs = {
            "sender": sender,
            "reciever": reciever,
            "text": message.text,
            "group": group,
            "audio": audio,
            "photos": photos,
            "documents": documents,
        }
        data = {key: str(kwargs[key]) for key in kwargs}
        logger.debug(f"Sending message -> {data}")

        emitter.emit(
            EventType.send_message,
            **kwargs
        )

        if isinstance(message, ChatMessage):
            agent_receiver = AGENTS.get(reciever.login)
            if not agent_receiver:
                continue

            elif reciever.login in [
                get_config().grupo.chat_robot, get_config().grupo.writer_robot
            ] and sender.login == get_config().grupo.translator_robot:
                return

            asyncio.create_task(to_agent(agent_receiver, sender, reciever, message))


async def to_agent(agent_receiver, sender_user, reciever_user, message):
    resp = await agent_receiver.send(str(sender_user.id), message.text, context=sender_user.to_dict())
    resp = self.prepare_text(resp.content)
    await self.gr.send_chat_message(sender=reciever_user, reciever=sender_user, message_text=resp)


def prepare_text(message: ChatMessage | GroupMessage | str) -> ChatMessage | GroupMessage:
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


def prepare_audio(message: ChatMessage | GroupMessage) -> str:
    audio_file = message.attachments["audio_message"].replace("\\", "")

    return f"https://innova.crmius.com/chat/{audio_file}"


def prepare_photo(message: ChatMessage | GroupMessage) -> list[str]:
    backslashes = "\\"

    return [
        f"https://innova.crmius.com/chat/{image['file'].replace(backslashes, '')}"
        for image in message.attachments
    ]


def prepare_screenshot(message: ChatMessage | GroupMessage) -> str:
    backslashes = "\\"

    return [f"https://innova.crmius.com/chat/{message.attachments['screenshot'].replace(backslashes, '')}"]


def prepare_document(message: ChatMessage | GroupMessage) -> list[list[str, str]]:
    if isinstance(message, GroupMessage):
        return [
            [
                f"https://innova.crmius.com/chat/download/attachment/group_id/{message.group_id}/message_id/{message.id}/attachment_index/{i}",
                document['name']
            ]
            for i, document in enumerate(message.attachments)
        ]

    elif isinstance(message, ChatMessage):
        return [
            [
                f"https://innova.crmius.com/chat/download/attachment/private_conversation_id/{message.chat_id}/message_id/{message.id}/attachment_index/{i}",
                document['name']
            ]
            for i, document in enumerate(message.attachments)
        ]
