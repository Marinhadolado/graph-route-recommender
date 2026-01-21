#! /bin/bash

#script para ejecutar los tests de la aplicacion backend

#primero comprobamos si se nos ha pasado algun argumento
if [ -z "$1" ]; then
    echo "Error: Debes especificar el nombre de qué test se va a ejecutar."
    echo "Uso: ./run_test.sh <nombre_test>"
    echo "Ejemplo: ./run_test.sh test_generator"
    exit 1
fi

TEST_NAME="$1"
CONTAINER_NAME="docker-neo4j-backend"

run_py_test() {
    echo "Ejecutando test: $TEST_NAME"
    docker exec -it $CONTAINER_NAME env PYTHONPATH=/app/src python3 src/tests/$1
}

if [ "$TEST_NAME" == "test_generator" ]; then
    run_py_test "test_generator.py"

elif [ "$TEST_NAME" == "test_filter" ]; then
    run_py_test "test_filter.py"

elif [ "$TEST_NAME" == "test_recommender" ]; then
    run_py_test "test_recommender.py"

else
    echo "Error: Test desconocido '$TEST_NAME'. Tests disponibles: test_generator, test_filter, test_recommender."
    exit 1
fi