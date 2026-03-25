Paso 1: Levantar el contenedor
    docker-compose up ó docker compose up

Paso2: activar conda
    conda activate tfg_graph

Paso 3: Acceder a la raiz del proyecto y poblar la base de datos ejecutando lo siguiente:
    python3 backend/src/LoadData.py

Paso 4:Construir el grafo en memoria(.gt), si aún no estan cargados:
    (desde src proyecto/backend/src$) python3 -m grafo.BuildGraph

Paso 5: Crear el Dataset con los filtros de minimo de saltos y minimo de rutas hechas por usuarios(ponemos muchos porque en tokyo hay muchos datos)

    python3 -m persistencia.DatasetGenerator 10 5 Tokyo

Paso 4: Creamos el archivo de predicciones para el algoritmo que se quiera con :


    

