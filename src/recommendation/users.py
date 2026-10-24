from typing import Any
from neo4j import AsyncDriver, RoutingControl


from src.recommendation.user_queries import GET_USER, UPSERT_USER, RATE, SET_GENRES, SKIP, HISTORY

from src.base.entities import RatedAlbum, User

class UserRepository:
    def __init__(self, driver: AsyncDriver):
        self._driver = driver

    async def _run(self, query: str, write: bool = False, **params: Any) -> list[dict]:
        records, _, _ = await self._driver.execute_query(
            query,
            parameters_=params,
            routing_=RoutingControl.WRITE if write else RoutingControl.READ,
        )
        return [r.data() for r in records]

    async def get(self, user_id: int) -> User | None:
        rows = await self._run(GET_USER, user_id=user_id)
        if not rows:
            return None
        r = rows[0]
        return User(
            id=r["id"],
            username=r["username"],
            taste_vector=r["taste"],
            liked_genres=list(r["liked_genres"])
        )

    async def exists(self, user_id: int) -> bool:
        rows = await self._run(
            "MATCH (u: User {id: $user_id})"
            " RETURN count (u) > 0 AS ok",
            user_id=user_id
        )
        return bool(rows and rows[0]["ok"])

    async def save(self, user: User) -> None:
        await self._run(
            UPSERT_USER,
            write=True,
            user_id=user.id,
            username=user.username,
            taste=user.taste_vector,
            genres=user.liked_genres
        )

    async def set_genres(self, user_id: int, genres: list[str]) -> None:
        await self._run(SET_GENRES, write=True, user_id=user_id, genres=genres)

    async def rate(self, user_id: int, album_id: int, score: int) -> bool:
        rows = await self._run(
            RATE, write=True, user_id=user_id, album_id=album_id, score=score
        )
        return bool(rows and rows[0]["n"])

    async def skip(self, user_id: int, album_id: int):
        await self._run(
            query=SKIP,
            write=True,
            user_id=user_id,
            album_id=album_id
        )

    async def history(self, user_id: int, limit: int = 20) -> list[RatedAlbum]:
        rows = await self._run(
            query=HISTORY,
            user_id=user_id,
            limit=limit
        )
        return [
            RatedAlbum(
                album_id=row["id"],
                title=row["title"],
                artists=row["artists"],
                year=row["year"],
                score=row["score"]
            )
            for row in rows
        ]