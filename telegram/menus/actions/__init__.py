
from aiogram import Router

from .utils import utils_router


actions_router = Router()
actions_router.include_routers(
    utils_router
)
