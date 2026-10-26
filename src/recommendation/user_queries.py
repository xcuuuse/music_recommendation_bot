_REPLACE_GENRES = """
WITH u
OPTIONAL MATCH (u)-[old:LIKES_GENRE]->()
DELETE old
WITH DISTINCT u
UNWIND $genres AS genre_name
MATCH (g:Genre {name: genre_name})
MERGE (u)-[:LIKES_GENRE]->(g)
"""

UPSERT_USER = (
    """
MERGE (u:User {id: $user_id})
ON CREATE SET u.created_at = datetime()
SET u.username = $username, u.taste = $taste
"""
    + _REPLACE_GENRES
)

SET_GENRES = "MATCH (u:User {id: $user_id})" + _REPLACE_GENRES

GET_USER = """
MATCH (u:User {id: $user_id})
RETURN u.id AS id,
       u.username AS username,
       u.taste AS taste,
       COLLECT { MATCH (u)-[:LIKES_GENRE]->(g:Genre) RETURN g.name } AS liked_genres
"""

RATE = """
MATCH (u:User {id: $user_id}), (a:Album {id: $album_id})
OPTIONAL MATCH (u)-[s:SKIPPED]->(a)
DELETE s
MERGE (u)-[r:RATED]->(a)
ON CREATE SET r.created_at = datetime()
SET r.score = $score, r.updated_at = datetime()
RETURN count(r) AS n
"""

SKIP = """
MATCH (u:User {id: $user_id}), (a:Album {id: $album_id})
MERGE (u)-[s:SKIPPED]->(a)
ON CREATE SET s.created_at = datetime()
"""

HISTORY = """
MATCH (:User {id: $user_id})-[r:RATED]->(a:Album)
RETURN a.id AS id, a.title AS title, a.year AS year, r.score AS score,
       COLLECT { MATCH (a)-[:PERFORMED_BY]->(ar:Artist) RETURN ar.name } AS artists
ORDER BY r.updated_at DESC
LIMIT $limit
"""

MARK_RECOMMENDED = """
MATCH (u:User {id: $user_id}), (a:Album {id: $album_id})
MERGE (u)-[r:RECOMMENDED]->(a)
ON CREATE SET r.first_at = datetime(), r.times = 0
SET r.last_at = datetime(), r.times = r.times + 1, r.score = $score
"""

DELETE_USER = "MATCH (u:User {id: $user_id}) DETACH DELETE u"