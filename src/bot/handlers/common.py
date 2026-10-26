from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, Message

from src.bot.cards import history_text
from src.base.exceptions import UserNotFoundError
from src.services.recommender import Recommender

NEED_START = "Нажмите /start"

COMMANDS = [
    BotCommand(command="recommend", description="Получить рекомендацию"),
    BotCommand(command="search", description="Найти альбом по настроению"),
    BotCommand(command="genres", description="Изменить любимые жанры"),
    BotCommand(command="rated", description="Мои оценки"),
    BotCommand(command="help", description="Справка"),
    BotCommand(command="cancel", description="Отмена"),
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
    await msg.answer("Отменено. /help - список команд")


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
    await msg.answer("Попробуйте /recommend или /help")
