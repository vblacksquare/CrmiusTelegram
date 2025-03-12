
from aiogram.filters.callback_data import CallbackData
from typing import Optional


class CallbackFactory(CallbackData, prefix="fab", sep="~"):
    action: str
    value: Optional[str] = None
