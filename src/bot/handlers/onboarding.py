from contextlib import suppress
from html import escape

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.handlers.common import NEED_START
from src.bot.handlers.recommend import send_recommendation
from src.bot.keyboards import MAX_GENRES, GenresDone, GenreToggle, genres_keyboard
from src.bot.states import EditGenres, Onboarding
from src.base.exceptions import UserNotFoundError
from src.services.recommender import Recommender