
from aiogram import Router
from .private import reply_private_router


reply_router = Router()
reply_router.include_routers(
    reply_private_router,
)
