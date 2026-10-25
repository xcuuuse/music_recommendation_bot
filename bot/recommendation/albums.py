from typing import Any
from neo4j import AsyncDriver, RoutingControl
from sympy.printing import aesaracode

from bot.recommendation.album_queries import CANDIDATES_QUERY, SEARCH_QUERY, ROOT_GENRES_QUERY, GENRE_EMBEDDINGS_QUERY

from bot.base.entities import Album, Signals
from bot.base.exceptions import RecordNotFoundError

def _album(row: dict[str, Any]) -> Album:
    return Album(
        id=row["id"],
        title=row["title"],
        genres=row["genres"],
        year=row["year"],
        description=row["description"] or ""
    )

class AlbumRepository:
    def __init__(self, driver: AsyncDriver):
        self._driver = driver

    async def _read(self, query: str, **params: Any) -> list[dict[str, Any]]:
        album_records, _, _ = await self._driver.execute_query(
            query, parameters_=params, routing_=RoutingControl.READ
        )
        return [record.data() for record in album_records]

    async def candidates(self, user_id: int) -> list[tuple[Album, Signals]]:
        rows = await self._read(
            CANDIDATES_QUERY,
            user_id=user_id
        )
        return [
            (
                _album(row),
                Signals(
                    cosine=row["cosine"],
                    artist_delta=row["artist_delta"],
                    liked_genre_hits=row["liked_genre_hits"],
                    genre_delta=row["genre_delta"],
                    era_hits=row["era_hits"],
                    peer_delta=row["peer_delta"],
                    peer_count=row["peer_count"]
                )
            )
            for row in rows
        ]

    async def search(self, user_id: int, vector: list[float], limit: int) -> list[tuple[Album, float]]:
        rows = await self._read(SEARCH_QUERY, user_id=user_id, vector=vector, limit=limit)
        return [(_album(row), row["cosine"]) for row in rows]

    async def embedding(self, album_id: int) -> list[float] | None:
        rows = await self._read(
            "MATCH (a:Album {id: $id}) RETURN a.embedding AS embedding", id=album_id
        )
        if not rows:
            raise RecordNotFoundError(f"Album {album_id} not found")
        return rows[0]["embedding"]

    async def root_genres(self) -> list[str]:
        return [r["name"] for r in await self._read(ROOT_GENRES_QUERY)]

    async def embedding_for_genres(self, genres: list[str]) -> list[list[float]]:
        rows = await self._read(GENRE_EMBEDDINGS_QUERY, genres=genres)
        return [row["embedding"] for row in rows]