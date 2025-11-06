#!/bin/bash

NEO4J_CONTAINER="docker-neo4j-neo4j-1"
CSV="/Q60_NewYorkCity_trails_weather_2_minroutes_4_minPOIs_TestRouteTraining.csv"

echo "Poblando relaciones VISITED desde $CSV..."

docker exec -i $NEO4J_CONTAINER cypher-shell -u neo4j -p password <<CYPHER
CALL {
    LOAD CSV WITH HEADERS FROM 'file://$CSV' AS row
    FIELDTERMINATOR ';'
    WITH row
    WHERE row.user_id IS NOT NULL AND row.trail_id IS NOT NULL
      AND row.venue_id IS NOT NULL AND row.timestamp IS NOT NULL
    WITH row
    ORDER BY row.user_id, row.trail_id, row.timestamp

    WITH row.user_id AS user, row.trail_id AS trail, collect(row) AS visits
    UNWIND range(0, size(visits)-2) AS i
    WITH user, trail, visits[i] AS r1, visits[i+1] AS r2
    WHERE r1.venue_id <> r2.venue_id
      AND size(r1.timestamp) >= 19 AND size(r2.timestamp) >= 19

    WITH user, trail, r1, r2,
         replace(r1.timestamp,' ','T') AS t1s,
         replace(r2.timestamp,' ','T') AS t2s

    WITH user, trail, r1, r2,
         datetime(t1s) AS t1,
         datetime(t2s) AS t2
    WHERE t2 > t1

    MATCH (p1:POI {fsq_id: r1.venue_id})
    MATCH (p2:POI {fsq_id: r2.venue_id})

    CREATE (p1)-[v:VISITED {
        user_id: user,
        trail_id: trail,

        p1_timestamp: r1.timestamp,
        p1_temp: toFloatOrNull(r1.temp),
        p1_precip: toFloatOrNull(r1.precip),
        p1_windspeed: toFloatOrNull(r1.windspeed),
        p1_preciptype: CASE WHEN r1.preciptype IS NULL OR r1.preciptype = '' THEN '' ELSE r1.preciptype END,
        p1_conditions: r1.conditions,

        p2_timestamp: r2.timestamp,
        p2_temp: toFloatOrNull(r2.temp),
        p2_precip: toFloatOrNull(r2.precip),
        p2_windspeed: toFloatOrNull(r2.windspeed),
        p2_preciptype: CASE WHEN r2.preciptype IS NULL OR r2.preciptype = '' THEN '' ELSE r2.preciptype END,
        p2_conditions: r2.conditions
    }]->(p2)
    SET v.time_diff_min = duration.between(t1, t2).minutes
} IN TRANSACTIONS;
CYPHER

echo "Relaciones VISITED creadas correctamente."
