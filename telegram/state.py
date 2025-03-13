
from aiogram.fsm.state import State, StatesGroup


class MainState(StatesGroup):
    verify = State()
    globale = State()
    plan = State()
