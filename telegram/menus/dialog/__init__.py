
from aiogram import Router
from .reply_private import reply_private_router
from .answer_private import answer_private_router


dialog_router = Router()
dialog_router.include_routers(
    reply_private_router,
    answer_private_router
)
