"""Загрузка жанров и альбомов из CSV в Neo4j.

    python -m scripts.load_data                 # обычная загрузка (идемпотентна, через MERGE)
    python -m scripts.load_data --wipe          # предварительно очистить ВСЮ базу
    python -m scripts.load_data --no-embeddings # без модели: граф для лабы, но без /search
"""

import argparse
from pathlib import Path

import pandas as pd
from neo4j import GraphDatabase

from src.config import Settings

CONSTRAINTS = [
    "CREATE CONSTRAINT album_id IF NOT EXISTS FOR (a:Album) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT artist_name IF NOT EXISTS FOR (a:Artist) REQUIRE a.name IS UNIQUE",
    "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
    "CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT decade_value IF NOT EXISTS FOR (d:Decade) REQUIRE d.value IS UNIQUE",
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
]

LOAD_GENRES = """
UNWIND $rows AS row
MERGE (g:Genre {name: row.name})
SET g.position = row.position
"""

LINK_GENRES = """
UNWIND $rows AS row
UNWIND row.parents AS parent_name
MATCH (child:Genre {name: row.name}), (parent:Genre {name: parent_name})
MERGE (child)-[:SUBGENRE_OF]->(parent)
"""

LOAD_ALBUMS = """
UNWIND $rows AS row
MERGE (a:Album {id: row.id})
SET a.title = row.title,
    a.year = row.year,
    a.description = row.description,
    a.embedding = row.embedding

// год может быть неизвестен — тогда узел десятилетия не создаём
FOREACH (_ IN CASE WHEN row.decade IS NULL THEN [] ELSE [1] END |
    MERGE (d:Decade {value: row.decade})
    ON CREATE SET d.name = toString(row.decade) + '-е'
    MERGE (a)-[:RELEASED_IN]->(d)
)

WITH a, row
UNWIND row.artists AS artist
MERGE (ar:Artist {name: artist.name})
MERGE (a)-[:PERFORMED_BY]->(ar)
FOREACH (_ IN CASE WHEN artist.country IS NULL THEN [] ELSE [1] END |
    MERGE (c:Country {name: artist.country})
    MERGE (ar)-[:FROM]->(c)
)

WITH DISTINCT a, row
UNWIND row.genres AS genre_name
MATCH (g:Genre {name: genre_name})
MERGE (a)-[:HAS_GENRE]->(g)
"""


def split(value) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def read_genres(path: Path) -> list[dict]:
    df = pd.read_csv(path)
    return [
        {"name": row["name"].strip(), "parents": split(row["parents"]), "position": i}
        for i, row in df.iterrows()
    ]


def read_albums(path: Path, known_genres: set[str]) -> list[dict]:
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        artists = split(r["artists"])
        countries = split(r["countries"])
        # Страны идут в том же порядке, что и исполнители; одна страна — на всех,
        # пустая ячейка — страна неизвестна (узел Country не создаётся).
        if not countries:
            countries = [None] * len(artists)
        elif len(countries) == 1:
            countries *= len(artists)
        if len(countries) != len(artists):
            raise ValueError(f"Альбом {r['id']}: исполнителей и стран разное количество")

        genres = split(r["genres"])
        unknown = set(genres) - known_genres
        if unknown:
            print(f"⚠️  Альбом {r['id']} «{r['title']}»: неизвестные жанры {unknown}")

        year = int(r["year"]) if pd.notna(r["year"]) else None
        rows.append(
            {
                "id": int(r["id"]),
                "title": str(r["title"]).strip(),
                "year": year,
                "decade": year // 10 * 10 if year else None,
                "description": str(r["description"]).strip(),
                "artists": [{"name": a, "country": c} for a, c in zip(artists, countries, strict=True)],
                "genres": genres,
                "embedding": None,
            }
        )
    return rows


def embedding_text(album: dict) -> str:
    """Текст для эмбеддинга: не только описание, но и жанры с исполнителем —
    так поиск «что-то вроде трип-хопа» тоже работает."""
    artists = ", ".join(a["name"] for a in album["artists"])
    return (
        f"{album['title']} — {artists}. Жанры: {', '.join(album['genres'])}. "
        f"{album['description']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--wipe", action="store_true", help="удалить всё из базы перед загрузкой")
    parser.add_argument("--no-embeddings", action="store_true")
    args = parser.parse_args()

    settings = Settings()
    genres = read_genres(args.data_dir / "genres.csv")
    albums = read_albums(args.data_dir / "albums.csv", {g["name"] for g in genres})
    print(f"Прочитано: {len(genres)} жанров, {len(albums)} альбомов")

    if not args.no_embeddings:
        from src.recommendation.embedder import Embedder

        print(f"Считаю эмбеддинги моделью {settings.embedding_model}…")
        vectors = Embedder(settings.embedding_model).embed_passages(
            [embedding_text(a) for a in albums]
        )
        for album, vec in zip(albums, vectors, strict=True):
            album["embedding"] = vec

    with GraphDatabase.driver(settings.neo4j_uri, auth=settings.neo4j_auth) as driver:
        driver.verify_connectivity()
        if args.wipe:
            driver.execute_query("MATCH (n) DETACH DELETE n")
            print("База очищена")
        for stmt in CONSTRAINTS:
            driver.execute_query(stmt)

        driver.execute_query(LOAD_GENRES, rows=genres)
        driver.execute_query(LINK_GENRES, rows=genres)
        driver.execute_query(LOAD_ALBUMS, rows=albums)

        records, _, _ = driver.execute_query(
            "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label"
        )
        print("Готово:", ", ".join(f"{r['label']}={r['n']}" for r in records))


if __name__ == "__main__":
    main()
