
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db import Db
from dtypes.db import method as dmth
from dtypes.user import User

from .language import language_menu
from .main import main_menu

from config import LANGUAGES, DEFAULT_LANGUAGE


auth_router = Router()
db = Db()


@auth_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    user: User = await db.ex(dmth.GetOne(User, id=message.from_user.id))

    if not user:
        user = User(
            id=message.from_user.id,
            first_name=message.from_user.first_name.lower() if message.from_user.first_name else None,
            second_name=message.from_user.last_name.lower() if message.from_user.last_name else None,
            username=message.from_user.username.lower() if message.from_user.username else None,
            language=message.from_user.language_code if message.from_user.language_code in LANGUAGES else DEFAULT_LANGUAGE
        )
        await db.ex(dmth.AddOne(User, user))

        await language_menu(user_message=message, action="skip")

    else:
        await main_menu(user_message=message, state=state)
