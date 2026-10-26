from html import escape
from contextlib import suppress
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.handlers.common import NEED_START
from src.bot.handlers.recommend import send_recommendation
from src.bot.keyboards import MAX_GENRES, GenresDone, GenreToggle, genres_keyboard
from src.bot.states import EditGenres, OnBoarding
from src.base.exceptions import UserNotFoundError
from src.services.recommender import Recommender

router = Router(name="onboarding")

MOOD_PROMPT = (
    "<b>Шаг 2/2.</b> Опишите своими словами, что хочется послушать.\n"
    "Не хотите — нажмите /skip, тогда начну с ваших жанров."
)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, service: Recommender) -> None:
    await state.clear()
    if await service.is_registered(message.from_user.id):
        await message.answer("Привет! 🎧 /recommend - новая рекомендация, /help - справка")
        return

    await state.set_state(OnBoarding.genres)
    await state.update_data(selected=[])
    await message.answer(
        "Привет! Я могу искать альбомы, основываясь на вашем настроении и вкусе.\n\n"
        f"<b>1/2.</b> Выберите не более {MAX_GENRES} любимых жанров:",
        reply_markup=genres_keyboard(await service.root_genres(), []),
    )
    

@router.callback_query(GenresDone.filter(), EditGenres.genres)
async def edit_genres_done(cb: CallbackQuery, state: FSMContext, service: Recommender) -> None:
    selected: list[str] = (await state.get_data()).get("selected", [])
    await state.clear()
    try:
        await service.set_genres(cb.from_user.id, selected)
    except UserNotFoundError:
        await cb.answer(NEED_START, show_alert=True)
        return

    await cb.answer("Сохранено")
    if isinstance(cb.message, Message):
        chosen = escape(", ".join(selected)) if selected else "ничего не выбрано"
        await cb.message.edit_text(f"✅ Любимые жанры: <i>{chosen}</i>")
        
@router.message(Command("genres"))
async def genres_cmd(message: Message, state: FSMContext, service: Recommender) -> None:
    try:
        current = await service.liked_genres(message.from_user.id)
    except UserNotFoundError:
        await message.answer(NEED_START)
        return

    await state.set_state(EditGenres.genres)
    await state.update_data(selected=current)
    await message.answer(
        "Отметьте ваши любимые жанры:",
        reply_markup=genres_keyboard(await service.root_genres(), current),
    )
    
@router.callback_query(GenresDone.filter(), OnBoarding.genres)
async def onboarding_genres_done(cb: CallbackQuery, state: FSMContext) -> None:
    if not (await state.get_data()).get("selected"):
        await cb.answer("Выберите как минимум один жанр", show_alert=True)
        return
    await state.set_state(OnBoarding.mood)
    await cb.answer()
    if isinstance(cb.message, Message):
        await cb.message.edit_text(MOOD_PROMPT)
        
async def _finish_onboarding(
    message: Message, state: FSMContext, service: Recommender, mood: str | None
) -> None:
    user = message.from_user
    genres = (await state.get_data()).get("selected", [])
    await message.answer("Настраиваем ваш профиль...")
    try:
        await service.register(user.id, user.username, genres, mood)  # type: ignore[union-attr]
    finally:
        await state.clear()
    await message.answer("Ваша первая рекомендация")
    await send_recommendation(message, user.id, service)
    
@router.message(OnBoarding.mood, Command("skip"))
async def mood_skip(message: Message, state: FSMContext, service: Recommender) -> None:
    await _finish_onboarding(message, state, service, mood=None)
    
@router.message(OnBoarding.mood, F.tet, ~F.text.startswith("/"))
async def mood_text(message: Message, state: FSMContext, service: Recommender) -> None:
    await _finish_onboarding(message, state, service, mood=message.text.strip()) 
    
@router.callback_query(
    GenreToggle.filter(), StateFilter(OnBoarding.genres, EditGenres.genres)
)
async def toggle_genre(
    cb: CallbackQuery, callback_data: GenreToggle, state: FSMContext, service: Recommender
) -> None:
    all_genres = await service.root_genres()
    if not 0 <= callback_data.index < len(all_genres):
        await cb.answer()
        return

    name = all_genres[callback_data.index]
    selected: list[str] = (await state.get_data()).get("selected", [])

    if name in selected:
        selected.remove(name)
    elif len(selected) >= MAX_GENRES:
        await cb.answer(f"Нельзя выбрать больше {MAX_GENRES} жанров", show_alert=True)
        return
    else:
        selected.append(name)

    await state.update_data(selected=selected)
    await cb.answer()
    if isinstance(cb.message, Message):
        with suppress(TelegramBadRequest):
            await cb.message.edit_reply_markup(
                reply_markup=genres_keyboard(all_genres, selected)
            )
