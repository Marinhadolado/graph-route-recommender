// POI más cercano a latitude y longitud que tenga al menos una salida VISITED
MATCH (s:POI)-[:VISITED]->()
WITH DISTINCT s,
point({ latitude:s.latitude, longitude:s.longitude }) AS ps,
point({ latitude:40.71149, longitude:-74.01321 }) AS q
 ORDER BY point.distance(ps, q) ASC
LIMIT 1
WITH s AS start

// Rutas de hasta 4 saltos (5 POIs máx)
MATCH p = (start)-[rs:VISITED*1..4]->(end)

// Todas las aristas son del mismo usuario
WITH p, rs, rs[0].user_id AS u, start
WHERE all(r IN rs
WHERE r.user_id = u)

// 4) Garantizar orden temporal coherente
 AND all(r IN rs
WHERE r.time_diff_min IS null OR r.time_diff_min >= 0)

// para evitar los bucles en las rutas
 AND size(
reduce(acc = [], n IN nodes(p) |


CASE WHEN n IN acc THEN acc ELSE acc + n END)
) = size(nodes(p))

RETURN
u AS user_id,
start AS startPOI,
p AS route,
size(rs)+1 AS num_pois,
[n IN nodes(p) | n.fsq_id] AS poi_ids,
[r IN rs | r.trail_id] AS trail_ids,
[r IN rs | r.time_diff_min] AS step_minutes,
reduce(t=0, x IN [r IN rs | coalesce(r.time_diff_min, 0)] | t+x) AS total_minutes
 ORDER BY num_pois DESC, total_minutes ASC;
