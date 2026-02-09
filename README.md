Paso 1: Levantar el contenedor
    docker-compose up ó docker compose up

Paso 2: Acceder a la raiz del proyecto y poblar la base de datos ejecutando lo siguiente:
    python3 backend/src/LoadData.py

Paso 3: Para generar los directorios del Dataset y de Predictions(con datos de ejemplo):
    docker exec -it docker-neo4j-backend python src/DatasetGenerator.py 3 2
    docker exec -it docker-neo4j-backend python src/Predictor.py 11111 None 3 score

