MATCH (s:POI)-[:VISITED]->()
WITH DISTINCT s,
point({ latitude:s.latitude, longitude:s.longitude }) AS ps,
point({ latitude:40.71149, longitude:-74.01321 }) AS q
 ORDER BY point.distance(ps, q) ASC
LIMIT 1
WITH s AS start

// 2. Rutas de hasta N saltos
MATCH p = (start)-[rs:VISITED*1..4]->(end)

// 3. Filtros (mismo user, sin bucles, tiempo ok)
WITH p, rs, rs[0].user_id AS u, start
WHERE all(r IN rs
WHERE r.user_id = u)
 AND all(r IN rs
WHERE r.time_diff_min IS null OR r.time_diff_min >= 0)
 AND size(reduce(acc = [], n IN nodes(p) |


CASE WHEN n IN acc THEN acc ELSE acc + n END)) = size(nodes(p))

// 4. Devolver lo que necesitamos para construir el árbol
RETURN
start AS startPOI,
nodes(p) AS pois, // Lista de TODOS los nodos en la ruta
relationships(p) AS rels // Lista de TODAS las relaciones en la ruta
 ORDER BY size(rs) DESC
LIMIT 50
