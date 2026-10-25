from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, Message

from bot.bot.cards import history_text
from bot.base.exceptions import UserNotFoundError
from bot.services.recommender import Recommender

NEED_START = "Press /start"

COMMANDS = [
    BotCommand(command="recommend", description="Get recommendation"),
    BotCommand(command="search", description="Find album based on your mood"),
    BotCommand(command="genres", description="Change fav genres"),
    BotCommand(command="rated", description="My ratings"),
    BotCommand(command="help", description="Help"),
    BotCommand(command="cancel", description="Cancel"),
]

HELP = (
    "Я подбираю музыкальные альбомы по вашему вкусу 🎶\n\n"
    "/recommend — следующая рекомендация\n"
    "/search &lt;описание&gt; — поиск по настроению, например "
    "<i>/search мрачный и холодный, как зима в спальном районе</i>\n"
    "/genres — изменить любимые жанры\n"
    "/rated — история ваших оценок\n"
    "/cancel — отменить текущее действие\n\n"
    "Чем больше альбомов вы оцените, тем точнее рекомендации: "
    "я учитываю исполнителей, жанры, десятилетия и оценки людей с похожим вкусом."
)

router = Router(name="common")
fallback_router = Router(name="fallback")


@router.message(Command("cancel"))
async def cancel(msg: Message, state: FSMContext) -> None:
    await state.clear()
    await msg.answer("Cancelled. /help — список команд")


@router.message(Command("help"))
async def help_cmd(msg: Message) -> None:
    await msg.answer(HELP)


@router.message(Command("rated"))
async def rated(msg: Message, service: Recommender) -> None:
    try:
        items = await service.history(msg.from_user.id)  # type: ignore[union-attr]
    except UserNotFoundError:
        await msg.answer(NEED_START)
        return
    await msg.answer(history_text(items))


@fallback_router.message()
async def fallback(msg: Message) -> None:
    await msg.answer("Try /recommend or /help")
