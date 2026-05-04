Paso 1: Levantar el contenedor
    docker-compose up ó docker compose up

Paso2: activar conda
    conda activate tfg_graph

Paso 3: Acceder a la raiz del proyecto y poblar la base de datos ejecutando lo siguiente:
    python3 -m persistencia.LoadDB  

Paso 4: Crear el Dataset con los filtros de minimo de saltos y minimo de rutas hechas por usuarios(ponemos muchos porque en tokyo hay muchos datos)

    python3 -m persistencia.DatasetGenerator 1 2 Tokyo

Paso 5:Construir el grafo en memoria(.gt), si aún no estan cargados:

    (desde src proyecto/backend/src$) python3 -m grafo.BuildGraph

paso intermedio si markov:

    python3 -m servicios.algoritmos.EntrenamientoFM

Paso 6: Creamos el archivo de predicciones para el algoritmo que se quiera con:

    python3 -m servicios.Predictor 155648 '{"conditions": "Clear"}' 2 markov Tokyo

Paso 7: Evaluamos los ficheros recomendadores:

    python3 -m evaluacion.Evaluator




    

