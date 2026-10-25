from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.bot.cards import recommendation_card, search_card
from bot.bot.handlers.common import NEED_START
from bot.bot.keyboards import NextAlbum, Noop, Rate, Skip, rated_keyboard, rating_keyboard
from bot.bot.states import Search
from bot.base.exceptions import AlbumNotFoundError, NothingToRecommendError, UserNotFoundError
from bot.services.recommender import Recommender

router = Router(name="recommend")

async def send_recommendation(target: Message, user_id: int, service: Recommender) -> None:
    try:
        album, score = await service.next_album(user_id)
    except UserNotFoundError:
        await target.answer(NEED_START)
        return
    except NothingToRecommendError:
        await target.answer("You have listened to all of the albums. Ratings - /rated")
        return
    await target.answer(
        recommendation_card(album, score), reply_markup=rating_keyboard(album.id)
    )


@router.message(Command("recommend"))
async def recommend_cmd(message: Message, state: FSMContext, service: Recommender) -> None:
    await state.clear()
    await send_recommendation(message, message.from_user.id, service)

@router.callback_query(NextAlbum.filter())
async def next_album(callback: CallbackQuery, callback_data: NextAlbum, service: Recommender) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(
                reply_markup=rated_keyboard(callback_data.score, with_next=False)
            )
        await send_recommendation(callback.message, callback.from_user.id, service)

@router.callback_query(Noop.filter())
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()

@router.callback_query(Rate.filter())
async def rate(cb: CallbackQuery, callback_data: Rate, service: Recommender) -> None:
    try:
        await service.rate(cb.from_user.id, callback_data.album_id, callback_data.score)
    except UserNotFoundError:
        await cb.answer(NEED_START, show_alert=True)
        return
    except AlbumNotFoundError:
        await cb.answer("This album is no longer in base", show_alert=True)
        return

    await cb.answer("Your rating is saved")
    if isinstance(cb.message, Message):
        with suppress(TelegramBadRequest):
            await cb.message.edit_reply_markup(reply_markup=rated_keyboard(callback_data.score))
            
@router.callback_query(Skip.filter())
async def skip(cb: CallbackQuery, callback_data: Skip, service: Recommender) -> None:
    try:
        await service.skip(cb.from_user.id, callback_data.album_id)
    except UserNotFoundError:
        await cb.answer(NEED_START, show_alert=True)
        return

    await cb.answer("Skip this")
    if isinstance(cb.message, Message):
        with suppress(TelegramBadRequest):
            await cb.message.delete()
        await send_recommendation(cb.message, cb.from_user.id, service)

async def _do_search(message: Message, text: str, service: Recommender) -> None:
    wait = await message.answer("🔎 Ищу подходящее…")
    try:
        results = await service.search(message.from_user.id, text)  # type: ignore[union-attr]
    except UserNotFoundError:
        await wait.edit_text(NEED_START)
        return

    with suppress(TelegramBadRequest):
        await wait.delete()

    if not results:
        await message.answer("Nothing found. Try another description")
        return
    best, *rest = [album for album, _ in results]
    await message.answer(search_card(best, rest), reply_markup=rating_keyboard(best.id))
    
@router.message(Command("search"))
async def search_cmd(
    message: Message, command: CommandObject, state: FSMContext, service: Recommender
) -> None:
    if not await service.is_registered(message.from_user.id):  # type: ignore[union-attr]
        await message.answer(NEED_START)
        return

    if command.args:
        await state.clear()
        await _do_search(message, command.args.strip(), service)
        return

    await state.set_state(Search.query)
    await message.answer(
        "Опишите, какое настроение или звучание ищете.\n"
        "<i>Например: «тёплый джаз для дождливого вечера»</i>\n\n/cancel — отмена"
    )


@router.message(Search.query, F.text, ~F.text.startswith("/"))
async def search_query(message: Message, state: FSMContext, service: Recommender) -> None:
    await state.clear()
    await _do_search(message, message.text.strip(), service)

