from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from networkx.generators import social

MAX_GENRES = 4

class GenreToggle(CallbackData, prefix="g"):
    index: int

class GenresDone(CallbackData, prefix="gd"):
    pass

class Rate(CallbackData, prefix="r"):
    album_id: int
    score: int

class Skip(CallbackData, prefix="s"):
    album_id: int

class NextAlbum(CallbackData, prefix="n"):
    score: int

class Noop(CallbackData, prefix="x"):
    pass

def genres_keyboard(all_genres: list[str], selected: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for index, name in enumerate(all_genres):
        mark = "✅ " if name in selected else ""
        kb.button(text=f"{mark}{name}", callback_data=GenreToggle(index=index))
    kb.adjust(2)
    kb.row(
        InlineKeyboardButton(
            text=f"Готово ({len(selected)}/{MAX_GENRES}) ->",
            callback_data=GenresDone().pack(),
        )
    )
    return kb.as_markup()

def rating_keyboard(album_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for score in range(1, 6):
        kb.button(text=f"{score}", callback_data=Rate(album_id=album_id, score=score))
    kb.button(text="Не сейчас", callback_data=Skip(album_id=album_id))
    kb.adjust(5, 1)
    return kb.as_markup()

def rated_keyboard(score: int, with_next: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"Ваша оценка: {'★' * score}{'☆' * (5 - score)}", callback_data=Noop())
    if with_next:
        kb.button(text="Следующий альбом", callback_data=NextAlbum(score=score))
    kb.adjust(1)
    return kb.as_markup()