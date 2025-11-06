#!/bin/bash

NEO4J_CONTAINER="docker-neo4j-neo4j-1"
CSV="/POIS_INFO_Q60_NewYorkCity_lvl1_categories.csv"

echo "Eliminando nodos y relaciones existentes antes de cargar nuevos datos..."
docker exec -i "$NEO4J_CONTAINER" cypher-shell -u neo4j -p password "MATCH (n) DETACH DELETE n;"
echo "Base de datos limpiada."

echo "Poblando nodos POI desde $CSV..."

docker exec -i $NEO4J_CONTAINER cypher-shell -u neo4j -p password <<CYPHER
CALL {
    LOAD CSV WITH HEADERS FROM 'file://$CSV' AS row
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
