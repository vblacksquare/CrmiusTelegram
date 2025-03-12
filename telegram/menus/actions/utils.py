
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from db import Db


utils_router = Router()
db = Db()


@utils_router.callback_query(F.data == "nothing")
async def nothing(callback: CallbackQuery):
    await callback.answer(_("nothing_action"))


@utils_router.callback_query(F.data == "suicide")
async def suicide(callback: CallbackQuery):
    await callback.message.delete()
