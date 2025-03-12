
from aiogram import BaseMiddleware, Dispatcher, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db import Db

from config import COMMANDS


class ClearFsmMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot, dispatcher: Dispatcher):
        super().__init__()
        self.bot = bot
        self.dp = dispatcher
        self.db = Db()

    async def __call__(self, handler, event: Message, data: dict):
        state: FSMContext = data.get("state")

        if event.text and event.text.lower() in COMMANDS and await state.get_state():
            await state.clear()
            return await self.dp._process_update(bot=self.bot, update=data['event_update'])

        return await handler(event, data)
