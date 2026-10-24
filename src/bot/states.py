from aiogram.fsm.state import State, StatesGroup

class OnBoarding(StatesGroup):
    genres = State()
    mood = State()

class EditGenres(StatesGroup):
    genres = State()

class Search(StatesGroup):
    query = State()

