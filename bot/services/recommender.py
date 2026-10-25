import asyncio

from pip._internal.resolution.resolvelib import candidates

from bot.base.entities import User
from bot.base.entities import RatedAlbum, Album, AlbumScore
from bot.base.exceptions import UserNotFoundError, NothingToRecommendError
from bot.base.taste import centroid, update_taste
from bot.recommendation.users import UserRepository
from bot.recommendation.albums import AlbumRepository
from bot.recommendation.embedder import Embedder
from bot.base.scoring import Weights, DEFAULT_WEIGHTS, rank


class Recommender:
    def __init__(
            self,
            users: UserRepository,
            albums: AlbumRepository,
            embedder: Embedder,
            weights: Weights = DEFAULT_WEIGHTS
    ):
        self.users = users
        self.albums = albums
        self.embedder = embedder
        self.weights = weights
        self._root_genres: list[str] | None = None

    async def root_genres(self):
        if not self._root_genres:
            self._root_genres = await self.albums.root_genres()
        return self._root_genres

    async def is_registered(self, user_id: int) -> bool:
        return await self.users.exists(user_id)

    async def _require_user(self, user_id: int) -> User:
        user = await self.users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} is not registered")
        return user

    async def register(self, user_id: int, username: str | None, genres: list[str], mood: str | None) -> None:
        if mood:
            taste = await asyncio.to_thread(self.embedder.embed_query, mood)
        else:
            taste = centroid(await self.albums.embedding_for_genres(genres))

        await self.users.save(
            User(id=user_id, username=username, taste_vector=taste, liked_genres=genres)
        )

    async def liked_genres(self, user_id: int) -> list[str]:
        return (await self._require_user(user_id)).liked_genres

    async def set_genres(self, user_id: int, genres: list[str]) -> None:
        await self._require_user(user_id)
        await self.users.set_genres(user_id, genres)

    async def history(self, user_id: int) -> list[RatedAlbum]:
        await self._require_user(user_id)
        return await self.users.history(user_id)

    async def next_album(self, user_id: int) -> tuple[Album, AlbumScore]:
        await self._require_user(user_id)
        user_candidates = await self.albums.candidates(user_id)
        if not candidates:
            raise NothingToRecommendError("All albums are already rated or skipped")
        return rank(user_candidates, self.weights)[0]

    async def search(self, user_id: int, text: str, limit: int = 3) -> list[tuple[Album, float]]:
        await self._require_user(user_id)
        album_vector = await asyncio.to_thread(self.embedder.embed_query, text)
        return await self.albums.search(user_id, album_vector, limit)

    async def rate(self, user_id: int, album_id: int, score: int) -> None:
        user = await self._require_user(user_id)
        album_vector = await self.albums.embedding(album_id)
        await self.users.rate(user_id, album_id, score)
        new_taste = update_taste(user.taste_vector, album_vector, score)
        if new_taste is not user.taste_vector:
            await self.users.set_taste(user_id, new_taste)

    async def skip(self, user_id: int, album_id: int) -> None:
        await self._require_user(user_id)
        await self.users.skip(user_id, album_id)
