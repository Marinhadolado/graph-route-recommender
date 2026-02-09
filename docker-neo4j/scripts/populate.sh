#!/bin/bash

# esto hace que el script falle si cualquier comando falla
set -e

CSV_nodes="/NYC/POIS_INFO_Q60_NewYorkCity_lvl1_categories.csv"

echo "Eliminando nodos y relaciones existentes antes de cargar nuevos datos..."
cypher-shell -u neo4j -p password -a bolt://neo4j:7687 "MATCH (n) DETACH DELETE n;"
echo "Base de datos limpiada."


echo "Poblando nodos POI desde $CSV_nodes..."

cat <<CYPHER | cypher-shell -u neo4j -p password -a bolt://neo4j:7687
CALL {
    LOAD CSV WITH HEADERS FROM 'file://$CSV_nodes' AS row
    WITH row
    WHERE row.fsq_id IS NOT NULL AND toFloat(row.latitude) <> -1.0 AND toFloat(row.longitude) <> -1.0
    MERGE (p:POI {fsq_id: row.fsq_id})
    SET
        p.latitude = CASE WHEN row.latitude <> '' THEN toFloat(row.latitude) END,
        p.longitude = CASE WHEN row.longitude <> '' THEN toFloat(row.longitude) END,
        p.category = row.category,
        p.price = CASE WHEN row.price <> '' THEN toInteger(row.price) END,
        p.rating = CASE WHEN row.rating <> '' THEN toFloat(row.rating) END,
        p.total_ratings = CASE WHEN row.total_ratings <> '' THEN toInteger(row.total_ratings) END,
        p.total_tips = CASE WHEN row.total_tips <> '' THEN toInteger(row.total_tips) END,
        p.Weekday_EarlyMorning = CASE WHEN row.Weekday_EarlyMorning <> '' THEN toInteger(row.Weekday_EarlyMorning) END,
        p.Weekday_Morning = CASE WHEN row.Weekday_Morning <> '' THEN toInteger(row.Weekday_Morning) END,
        p.Weekday_Afternoon = CASE WHEN row.Weekday_Afternoon <> '' THEN toInteger(row.Weekday_Afternoon) END,
        p.Weekday_Night = CASE WHEN row.Weekday_Night <> '' THEN toInteger(row.Weekday_Night) END,
        p.Weekend_EarlyMorning = CASE WHEN row.Weekend_EarlyMorning <> '' THEN toInteger(row.Weekend_EarlyMorning) END,
        p.Weekend_Morning = CASE WHEN row.Weekend_Morning <> '' THEN toInteger(row.Weekend_Morning) END,
        p.Weekend_Afternoon = CASE WHEN row.Weekend_Afternoon <> '' THEN toInteger(row.Weekend_Afternoon) END,
        p.Weekend_Night = CASE WHEN row.Weekend_Night <> '' THEN toInteger(row.Weekend_Night) END,
        p.category_lvlFs = row.category_lvlFs,
        p.city = 'NYC'
} IN TRANSACTIONS;
CYPHER

echo "Nodos POI creados correctamente."

CSV_edges="/NYC/Q60_NewYorkCity_trails_weather_2_minroutes_4_minPOIs_TestRouteTraining.csv"

echo "Poblando relaciones VISITED desde $CSV_edges..."

cat <<CYPHER | cypher-shell -u neo4j -p password -a bolt://neo4j:7687
CALL {
    LOAD CSV WITH HEADERS FROM 'file://$CSV_edges' AS row
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

