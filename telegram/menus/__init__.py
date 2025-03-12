
from aiogram import Router

from .auth import auth_router
from .actions import actions_router

from .main import main_router
from .language import language_router
from .verify import verify_router
from .reply import reply_router
from .write import write_router
from .users import users_router
from .time import time_router


menus_router = Router()
menus_router.include_routers(
    auth_router,
    main_router,
    actions_router,
    language_router,
    verify_router,
    reply_router,
    write_router,
    users_router,
    time_router
)
