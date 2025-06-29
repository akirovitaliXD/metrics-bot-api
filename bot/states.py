from aiogram.dispatcher.filters.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_server = State()
    waiting_for_period = State() 