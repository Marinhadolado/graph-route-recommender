import sys
import re
from pathlib import Path

import pandas as pd
from graph.GraphRepository import GraphRepository

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[2]
DATA_DIR = HERE / "data"

#esta función se encarga de guardar los datos en un archivo tsv
def save_tsv(rows, name, output_dir):
    pd.DataFrame(rows).to_csv(output_dir / name, sep="\t", header=False, index=False)

# prepara los 4 tsv de elliot a partir del predictions
def prepare(predictions_file, city, hops):

    DATA_DIR.mkdir(exist_ok=True, parents=True)
    filename = Path(predictions_file).stem

    experiment_name = re.sub(
        r"_\d{8}_\d{6}(?:_\d+)?$",
        "",
        filename
    )

    # Carpeta independiente para cada configuración
    experiment_dir = DATA_DIR / experiment_name
    experiment_dir.mkdir(exist_ok=True, parents=True)

    print(f"[ELLIOT] Preparando experimento: {experiment_name}")

    graph = GraphRepository(city).get_graph()

    # Se mapean de todos los POIs del grafo para que puedan ser ints en tsv
    
    # POIs del grafo
    graph_pois = set(graph.id_map.keys())

    # POIs del dataset de test
    test_file = BACKEND / "dataset" / "test.csv"

    test_df = pd.read_csv(
        test_file,
        dtype={"poi_id": str}
    )

    test_pois = set(test_df["poi_id"])

    # Catálogo completo para la evaluación
    all_pois = sorted(graph_pois | test_pois)

    poi_map_file = DATA_DIR / "poi_map.csv"

    if poi_map_file.exists():
        df_map = pd.read_csv(
            poi_map_file,
            dtype={"poi_id": str}
        )

        poi_map = dict(zip(
            df_map["poi_id"],
            df_map["item_id"].astype(int)
        ))

        print("[ELLIOT] Reutilizando poi_map.csv")

    else:
        poi_ids = all_pois

        poi_map = {}
        for idx, poi in enumerate(poi_ids):
            poi_map[poi] = idx + 1

        pd.DataFrame(
            poi_map.items(),
            columns=["poi_id", "item_id"]
        ).to_csv(DATA_DIR / "poi_map.csv", index=False)

        print("[ELLIOT] poi_map.csv generado")

    poi_ids = list(poi_map.keys())

    # Se mapean las categorías se guardan en categories.tsv
    category_map_file = DATA_DIR / "category_map.csv"
    categories_file = DATA_DIR / "categories.tsv"

    if category_map_file.exists() and categories_file.exists():

        df_categories = pd.read_csv(category_map_file)

        category_map = dict(zip(
            df_categories["category"],
            df_categories["category_id"].astype(int)
        ))

        print("[ELLIOT] Reutilizando categorías existentes")

    elif not category_map_file.exists() and not categories_file.exists():
        print("[ELLIOT] Generando nuevas categorías")
        
        poi_categories = {}

        for poi in poi_ids:
            #evitamos buscar nuevas categorias en 
            # pois del test porque estos pueden no estar en el grafo
            if poi not in graph.id_map:
                continue
            vertex = graph.id_map[poi]
            category = str(graph.vp_category_lvlFs[vertex]).strip()

            if category and category.lower() not in {"none", "nan"}:
                poi_categories[poi] = category


        category_map = {}
        for idx, category in enumerate(sorted(set(poi_categories.values()))):
            category_map[category] = idx + 1

        pd.DataFrame(
            category_map.items(),
            columns=["category", "category_id"]
        ).to_csv(DATA_DIR / "category_map.csv", index=False)

        category_rows = []

        for poi, category in poi_categories.items():

            if category not in category_map:
                raise ValueError(
                    f"Categoría '{category}' no encontrada."
                )

            category_rows.append((
                poi_map[poi],
                category_map[category]
            ))

        save_tsv(category_rows, "categories.tsv", DATA_DIR)
    else:
        raise RuntimeError(
            "Solo existe uno de los archivos de categorías. "
            "Comprueba category_map.csv y categories.tsv."
        )

    #se construyen las consultas tipo (query= trail_id, step) a partir de test.csv
    test = pd.read_csv(
        BACKEND / "dataset" / "test.csv",
        dtype=str,
        keep_default_na=False
    )

    # primero se agrupan los POIs por trail_id para formar rutas
    routes ={}
    for trail_id, group in test.groupby("trail_id", sort=False):
        routes[str(trail_id)] = group["poi_id"].tolist()

    queries = []

    #vamos tras cada ruta y generamos las consultas para cada paso, teniendo en cuenta los hops
    for trail_id, route in routes.items():

        for i in range(len(route) - hops):

            origin = route[i]
            target = route[i + hops]
            step = i + 1 + hops

            if origin not in poi_map or target not in poi_map:
                raise ValueError(
                    f"POI fuera del catálogo en ruta {trail_id}, "
                    f"paso {step}: origen={origin}, objetivo={target}"
                )

            queries.append({
                "query_id": len(queries) + 1,
                "trail_id": trail_id,
                "step": step,
                "current_poi": origin,
                "target_poi": target,
                "current_item_id": poi_map[origin],
                "target_item_id": poi_map[target]
            })

    query_df = pd.DataFrame(queries)

    if query_df.empty:
        raise ValueError("No hay consultas para estos hops")

    query_df.to_csv(experiment_dir / "query_map.csv", index=False)

    # construimos un diccionario para mapear (trail_id, step) a query_id
    query_map = {}
    for row in query_df.itertuples(index=False):
        query_map[(str(row.trail_id), int(row.step))] = int(row.query_id)
        

    #generar train.tsv y test.tsv
    # Una interacción conocida por consulta: el POI de origen
    train_rows = []
    for row in query_df.itertuples(index=False):
        train_rows.append((int(row.query_id), int(row.current_item_id), 1))

    # Usuario auxiliar para incluir el catálogo en Elliot
    auxiliary_user = len(query_df) + 1

    for item_id in poi_map.values():
        train_rows.append((auxiliary_user, item_id, 1))

    save_tsv(train_rows, "train.tsv", experiment_dir)

    save_tsv(
        [
            (int(row.query_id), int(row.target_item_id), 1)
            for row in query_df.itertuples(index=False)
        ],
        "test.tsv",
        experiment_dir
    )

    #creamos el ultimo tsv para convertir las recomendaciones del predictor
    recs = pd.read_csv(
        predictions_file,
        dtype={"trail_id": str, "poi_id": str},
        keep_default_na=False
    )

    required = {"trail_id", "step", "poi_id", "prediction"}

    #miramos si falta alguna columna
    if not required.issubset(recs.columns):
        raise ValueError(
            f"Faltan columnas: {required - set(recs.columns)}"
        )

    recs["step"] = recs["step"].astype(int)

    recs["prediction"] = pd.to_numeric(
        recs["prediction"],
        errors="raise"
    )

    recs["query_id"] = [
        query_map.get((trail, step))
        for trail, step in zip(recs["trail_id"], recs["step"])
    ]

    recs["item_id"] = recs["poi_id"].map(poi_map)

    if recs["query_id"].isna().any():
        raise ValueError(
            "Hay (trail_id, step) inexistentes en test.csv"
        )

    if recs["item_id"].isna().any():
        raise ValueError(
            "Hay POIs recomendados que no aparecen en el grafo"
        )

    if recs.duplicated(["query_id", "item_id"]).any():
        raise ValueError(
            "Hay POIs repetidos dentro de una misma consulta"
        )

    recs[
        ["query_id", "item_id", "prediction"]
    ].to_csv(
        experiment_dir / "recommendations.tsv",
        sep="\t",
        header=False,
        index=False
    )

    #por ultimo se crea el archivo para verificar manualmente las consultas
    top5 = (
        recs.sort_values(
            ["query_id", "prediction"],
            ascending=[True, False]
        )
        .groupby("query_id")["poi_id"]
        .apply(lambda pois: " | ".join(pois.head(5)))
        .rename("top5_original")
    )

    verification = query_df.merge(
        top5,
        left_on="query_id",
        right_index=True,
        how="left"
    )

    verification["top5_original"] = (
        verification["top5_original"].fillna("")
    )

    verification["has_recommendations"] = (
        verification["top5_original"].ne("")
    )

    verification["target_in_top5"] = verification.apply(
        lambda row: row["target_poi"]
        in row["top5_original"].split(" | "),
        axis=1
    )

    verification.to_csv(
        experiment_dir / "verification.csv",
        index=False
    )

    print(f"Consultas: {len(query_df)}")
    print(f"Con recomendaciones: {recs['query_id'].nunique()}")
    print(f"POIs en catálogo: {len(poi_map)}")
    print(f"Categorías: {len(category_map)}")
    print(f"Archivos guardados en {experiment_dir}")


if __name__ == "__main__":

    try:
        if len(sys.argv) != 4:
            print("Usage: python PrepareElliot.py <predictions_file> <city_name> <hops>")
            print("  hops: 1 o 2")
            sys.exit(1)

        predictions_file = Path(sys.argv[1])
        city_name = sys.argv[2]
        hops = int(sys.argv[3])

        if hops not in (1, 2):
            print(f"[PREPARE] ERROR: hops must be 1 or 2 (got '{sys.argv[3]}').")
            sys.exit(1)

        prepare(predictions_file, city_name, hops)

    except Exception as e:
        print(f"[PREPARE] ¡ERROR FATAL!: {e}")
        sys.exit(1)
