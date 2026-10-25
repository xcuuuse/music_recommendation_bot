ALBUM_FIELDS = """
    a.id AS id,
    a.title AS title,
    a.year AS year,
    a.description AS description,
    COLLECT { MATCH (a)-[:PERFORMED_BY]->(ar:Artist) RETURN ar.name } AS artists,
    COLLECT { MATCH (a)-[:HAS_GENRE]->(g:Genre) RETURN g.name } AS genres
"""

# Все неоценённые и непропущенные альбомы + признаки для ранжирования.
# Каждый CALL-подзапрос считает один «сигнал», обходя граф от кандидата.
CANDIDATES_QUERY = f"""
MATCH (u:User {{id: $user_id}})
MATCH (a:Album)
WHERE NOT EXISTS {{ (u)-[:RATED|SKIPPED]->(a) }}

// 1. Как пользователь оценивал другие альбомы этого же исполнителя
CALL (u, a) {{
    OPTIONAL MATCH (a)-[:PERFORMED_BY]->(:Artist)<-[:PERFORMED_BY]-(:Album)<-[r:RATED]-(u)
    RETURN avg(r.score - 3.0) AS artist_delta
}}

// 2. Жанры из онбординга: поджанр альбома -> (0 или 1 шаг вверх по иерархии) -> любимый жанр
CALL (u, a) {{
    OPTIONAL MATCH (a)-[:HAS_GENRE]->(:Genre)-[:SUBGENRE_OF*0..1]->(g:Genre)<-[:LIKES_GENRE]-(u)
    RETURN count(DISTINCT g) AS liked_genre_hits
}}

// 3. Опыт по жанрам: оценки альбомов с общими жанрами
CALL (u, a) {{
    OPTIONAL MATCH (a)-[:HAS_GENRE]->(:Genre)<-[:HAS_GENRE]-(:Album)<-[r:RATED]-(u)
    RETURN avg(r.score - 3.0) AS genre_delta
}}

// 4. Эпоха: понравившиеся альбомы из того же десятилетия
CALL (u, a) {{
    OPTIONAL MATCH (a)-[:RELEASED_IN]->(:Decade)<-[:RELEASED_IN]-(fav:Album)<-[r:RATED]-(u)
    WHERE r.score >= 4
    RETURN count(DISTINCT fav) AS era_hits
}}

// 5. Коллаборативный сигнал: «соседи» — люди, которым понравилось то же, что и мне
CALL (u, a) {{
    OPTIONAL MATCH (u)-[mine:RATED]->(:Album)<-[theirs:RATED]-(peer:User)-[pr:RATED]->(a)
    WHERE mine.score >= 4 AND theirs.score >= 4
    WITH DISTINCT peer, pr
    RETURN avg(pr.score - 3.0) AS peer_delta, count(peer) AS peer_count
}}

RETURN {ALBUM_FIELDS},
    CASE
        WHEN u.taste IS NULL OR a.embedding IS NULL THEN null
        // vector.similarity.cosine возвращает значение в [0; 1], переводим обратно в [-1; 1]
        ELSE 2 * vector.similarity.cosine(u.taste, a.embedding) - 1
    END AS cosine,
    artist_delta, liked_genre_hits, genre_delta, era_hits, peer_delta, peer_count
"""

SEARCH_QUERY = f"""
MATCH (a:Album)
WHERE a.embedding IS NOT NULL
  AND NOT EXISTS {{ (:User {{id: $user_id}})-[:RATED]->(a) }}
WITH a, vector.similarity.cosine($vector, a.embedding) AS sim
ORDER BY sim DESC
LIMIT $limit
RETURN {ALBUM_FIELDS}, 2 * sim - 1 AS cosine
"""

ROOT_GENRES_QUERY = """
MATCH (g:Genre)
WHERE NOT EXISTS { (g)-[:SUBGENRE_OF]->() }
RETURN g.name AS name
ORDER BY g.position
"""

# Эмбеддинги альбомов, попадающих в выбранные макрожанры (через иерархию)
GENRE_EMBEDDINGS_QUERY = """
MATCH (root:Genre) WHERE root.name IN $genres
MATCH (a:Album)-[:HAS_GENRE]->(:Genre)-[:SUBGENRE_OF*0..1]->(root)
WHERE a.embedding IS NOT NULL
RETURN DISTINCT a.id AS id, a.embedding AS embedding
"""