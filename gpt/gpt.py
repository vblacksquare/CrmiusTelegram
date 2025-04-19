
import time
import asyncio
import functools
import json
from loguru import logger

from dtypes import CrmUser
from telegram import i18n

from grupo import Grupo

from db import Db
from dtypes.db import method as dmth
from dtypes.agent_thread import AgentThread
from dtypes.user import User
from dtypes.group import Group

from openai import AsyncOpenAI
from openai.types.beta.threads import RequiredActionFunctionToolCall

from config import GPT_KEY, TARAS_ID


db = Db()
gr = Grupo()

GPT = AsyncOpenAI(api_key=GPT_KEY)
gpt_log = logger.bind(classname="GPT")


async def create_gpt_thread():
    try:
        thread = await GPT.beta.threads.create()
        gpt_log.debug(f"Created thread -> {thread}")

        return thread

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't create thread")

        return None


async def create_message(thread_id: str, prompt: str) -> None:
    _prompt = prompt.replace("\n", "\\n")

    try:
        message = await GPT.beta.threads.messages.create(
            thread_id=thread_id,
            content=prompt,
            role="user"
        )
        gpt_log.debug(f"Created message -> {thread_id} -> {_prompt} -> {message}")

        return message

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't create message -> {thread_id} -> {_prompt}")

        return None


async def send_to_assistant(thread_id: str, assistant_id: str, instructions=None) -> str:
    try:
        run = await GPT.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions
        )
        gpt_log.debug(f"Sent to assistant -> {thread_id} -> {run}")

        return run.id

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't send to assistant -> {thread_id}")

        return None


async def submit_tool_outputs(tool_call: RequiredActionFunctionToolCall, dynamic_data: dict):
    data = json.loads(tool_call.function.arguments)

    response = None

    if tool_call.function.name == "chats":
        response = dynamic_data["chats"]

    elif tool_call.function.name == "send_private_message":
        try:
            text = data["text"]
            email = data["target"]

            formatted_text = i18n.gettext("gpt_generated", locale=dynamic_data["sender"].language).format(text=text)
            crm_reciever: CrmUser = await db.ex(dmth.GetOne(CrmUser, login=email))

            await gr.send_chat_message(sender=dynamic_data["crm_sender"], reciever=crm_reciever, message_text=formatted_text)

            response = "ok"

        except Exception as err:
            gpt_log.exception(err)

            response = str(err)

    elif tool_call.function.name == "send_group_message":
        try:
            text = data["text"]
            slug = data["target"]

            formatted_text = i18n.gettext("gpt_generated", locale=dynamic_data["sender"].language).format(text=text)
            group: Group = await db.ex(dmth.GetOne(Group, slug=slug))

            await gr.send_group_message(sender=dynamic_data["crm_sender"], group=group, message_text=formatted_text)

            response = "ok"

        except Exception as err:
            gpt_log.exception(err)

            response = str(err)

    return {
        "tool_call_id": tool_call.id,
        "output": json.dumps(response) if response else "Error"
    }


async def wait_for_response(thread_id: str, run_id: str, dynamic_data: dict) -> str | None:
    try:
        status = None
        time_start = time.time()

        while not status or status != "completed":
            run = await GPT.beta.threads.runs.retrieve(run_id=run_id, thread_id=thread_id)

            if run.required_action:
                tool_calls = run.required_action.submit_tool_outputs.tool_calls

                tool_outputs = []
                for tool_call in tool_calls:
                    output = await submit_tool_outputs(tool_call, dynamic_data)
                    tool_outputs.append(output)

                    gpt_log.debug(f"Answered tool calls -> {tool_call} -> {output}")

                run = await GPT.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs
                )

            status = run.status
            gpt_log.debug(f"Waiting for response -> {thread_id} -> {run_id} -> {status}")
            await asyncio.sleep(3)

            if status == "failed":
                return None

            if time.time() - time_start >= 60:
                raise TimeoutError(f"Didn't get an answer in {60} seconds")

        response = await GPT.beta.threads.messages.list(
            thread_id=thread_id
        )

        gpt_log.debug(f"Got response -> {response}")

        if response.data:
            return response.data[0].content[0].text.value

        return await wait_for_response(thread_id, run_id, dynamic_data)

    except Exception as err:
        gpt_log.exception(err)
        gpt_log.error(f"Coudn't wait for response -> {thread_id} -> {run_id}")

        return None

        # return await wait_for_response(thread_id, run_id, dynamic_data)


async def generate_answer(
    request: str,
    user_id: int
) -> str:

    user: User = await db.ex(dmth.GetOne(User, id=user_id))

    if request is [None, ""]:
        return i18n.gettext("gpt_not_implemented", locale=user.language)

    agent_thread: AgentThread = await db.ex(dmth.GetOne(AgentThread, user_id=user_id))
    if not agent_thread:
        thread_id = (await create_gpt_thread()).id
        agent_thread = AgentThread(thread_id, user_id)
        await db.ex(dmth.AddOne(AgentThread, agent_thread))

    chats: list[CrmUser] = await db.ex(dmth.GetMany(CrmUser))
    groups: list[Group] = await db.ex(dmth.GetMany(Group))

    dynamic_data = {
        "sender": user,
        "crm_sender": await db.ex(dmth.GetOne(CrmUser, user_id=user.id)),
        "chats": [
            *[
                {"first_name": chat.first_name, "last_name": chat.last_name, "email": chat.login, "type": "private"}
                for chat in chats
            ],
            *[
                {"name": group.title, "slug": group.slug, "type": "group"}
                for group in groups
            ]
        ]
    }

    await create_message(agent_thread.id, request)

    run_id = await send_to_assistant(agent_thread.id, TARAS_ID, None)
    resp = await wait_for_response(agent_thread.id, run_id, dynamic_data)

    if resp in [None, ""]:
        resp = i18n.gettext("gpt_unkown_error", locale=user.language)

    return resp

