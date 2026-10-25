//1

CALL db.schema.visualization();

//2 all artist albums

MATCH (album:Album)-[PERFORMED_BY]->(artist:Artist {name: "Linkin Park"})
RETURN artist, album

//3 metal subgenres

MATCH (sub:Genre)-[:SUBGENRE_OF]->(:Genre {name: "Метал"})
OPTIONAL MATCH (a:Album)-[:HAS_GENRE]->(sub)
RETURN sub.name AS `поджанр`, count(a) AS `альбомов`
ORDER BY `альбомов` DESC, `поджанр`;

MATCH p = (a:Album)-[:HAS_GENRE]->(:Genre)-[:SUBGENRE_OF*0..1]->(:Genre {name: "Электроника"})
RETURN p;

MATCH (c:Country {name: "Россия"})<-[:FROM]-(ar:Artist)<-[:PERFORMED_BY]-(a:Album)-[:RELEASED_IN]->(d:Decade {value: 2020})
RETURN c, ar, a, d;

MATCH (ar:Artist)<-[:PERFORMED_BY]-(a:Album)
WITH ar, count(a) AS n, collect(a.title + " (" + toString(a.year) + ")" AS albums)
WHERE n > 1
RETURN ar.name AS  `исполнитель`, n AS `альбомов`, albums AS `список`
ORDER BY n DESC, `исполнитель`;

MATCH (src:Album {title: "Hybrid Theory"})-[:HAS_GENRE]->(g:Genre)<-[:HAS_GENRE]-(other:Album)
RETURN other.title AS `альбом`, collect(g.name) AS `общие жанры`, count(g) AS `совпадений`
ORDER BY `совпадений` DESC, `альбом`
LIMIT 10

MATCH (g:Genre)-[:SUBGENRE_OF]->(p:Genre)
WITH g, collect(p.name) AS parents
WHERE size(parents) > 1
RETURN g.name AS `жанр`, parents AS `направления`
ORDER BY `жанр`;


MATCH (d:Decade)<-[:RELEASED_IN]-(a:Album)
RETURN d.name AS `десятилетие`, count(a) AS `альбомов`
ORDER BY d.value;

MATCH (a:Album {title: "Master of Puppets"}), (b:Album {title: "Eve"}),
      p = shortestPath((a)-[:HAS_GENRE|SUBGENRE_OF|PERFORMED_BY|RELEASED_IN*..8]-(b))
RETURN p;

MATCH (c:Country)<-[:FROM]-(ar:Artist)<-[:PERFORMED_BY]-(a:Album)
RETURN c.name AS `страна`,
       count(DISTINCT ar) AS `исполнителей`,
       count(DISTINCT a) AS `альбомов`
ORDER BY `альбомов` DESC
LIMIT 10;


MATCH (u:User)-[r:RATED]->(a:Album)
RETURN u.username AS `пользователь`, a.title AS `альбом`, r.score AS `оценка`
ORDER BY `пользователь`, `оценка` DESC;


MATCH (me:User {username: "your_username"})-[r1:RATED]->(:Album)<-[r2:RATED]-(peer:User)
      -[r3:RATED]->(rec:Album)
WHERE r1.score >= 4 AND r2.score >= 4 AND r3.score >= 4
  AND NOT EXISTS { (me)-[:RATED]->(rec) }
RETURN rec.title AS `рекомендация`, count(DISTINCT peer) AS `соседей`
ORDER BY `соседей` DESC;