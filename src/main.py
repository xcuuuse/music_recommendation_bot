import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from neo4j import AsyncGraphDatabase

from src.bot.handlers import build_router
from src.bot.handlers.common import COMMANDS
from src.config import Settings
from src.recommendation.albums import AlbumRepository
from src.recommendation.embedder import Embedder
from src.recommendation.users import UserRepository
from src.services.recommender import Recommender


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    if settings.bot_token is None:
        raise SystemExit("BOT_TOKEN не задан — добавьте его в .env")

    driver = AsyncGraphDatabase.driver(settings.neo4j_uri, auth=settings.neo4j_auth)
    await driver.verify_connectivity()

    logging.info("Загружаю модель эмбеддингов %s…", settings.embedding_model)
    embedder = Embedder(settings.embedding_model)

    service = Recommender(UserRepository(driver), AlbumRepository(driver), embedder)
    if not await service.root_genres():
        raise SystemExit("В базе нет жанров. Сначала запустите: python -m scripts.load_data")

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["service"] = service  # попадёт в хендлеры как аргумент service
    dp.include_router(build_router())

    await bot.set_my_commands(COMMANDS)
    try:
        logging.info("Бот запущен")
        await dp.start_polling(bot)
    finally:
        await driver.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())