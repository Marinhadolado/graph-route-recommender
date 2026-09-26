import pandas as pd
from graph.GraphRepository import GraphRepository
from evaluation.Evaluator import Evaluator

# 1. Cargamos el grafo una sola vez para que sea súper rápido
graph = GraphRepository("Tokyo").get_graph()

resultados = []

# 2. Definimos los algoritmos y los archivos que tienes en tu carpeta
algoritmos = ["markov", "random"]
context_configs = ["time_segment_conditions", "time_segment", "conditions", "none"]
location_configs = ["time_segment_conditions_hops2", "none_hops2"]

# 3. El "Robot" empieza a leer todo
for algo in algoritmos:
    
    # Evaluar las 4 configuraciones de 1 salto
    for suffix in context_configs:
        ev = Evaluator("Tokyo", algo, suffix)
        r = ev.evaluate(graph=graph)
        r["algorithm"] = algo
        r["autonomy_level"] = suffix
        r["autonomy_type"] = "context"
        resultados.append(r)

    # Evaluar las 2 configuraciones de 2 saltos
    for suffix in location_configs:
        ev = Evaluator("Tokyo", algo, suffix)
        r = ev.evaluate(graph=graph)
        r["algorithm"] = algo
        r["autonomy_level"] = suffix
        r["autonomy_type"] = "location_hops"
        resultados.append(r)

# 4. Guardar la tabla maestra final
df = pd.DataFrame(resultados)

# Reordenar las columnas para que las métricas queden bonitas al principio
cols = ['algorithm', 'autonomy_type', 'autonomy_level', 'ndcg@1', 'ndcg@5', 'ndcg@10', 'coverage', 'diversity', 'n_queries_evaluadas']
# Filtramos solo las columnas que existan por si falta alguna
cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
df = df[cols]

df.to_csv("coverage_diversity_summary.csv", index=False)
print("\n¡Evaluación completa! Resultados guardados en coverage_diversity_summary.csv")
print(df)