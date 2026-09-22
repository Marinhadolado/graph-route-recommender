import pandas as pd
from graph.GraphRepository import GraphRepository
from evaluation.Evaluator import Evaluator

graph = GraphRepository("Tokyo").get_graph()

resultados = []

context_configs = ["time_segment_conditions", "time_segment", "conditions", "none"]

for suffix in context_configs:
    ev = Evaluator("Tokyo", "markov", suffix)
    r = ev.evaluate(graph=graph)
    r["autonomy_level"] = suffix
    r["autonomy_type"] = "context"
    resultados.append(r)

location_configs = [
    "time_segment_conditions_hops2",
    "time_segment_conditions_hops3",
]

for suffix in location_configs:
    ev = Evaluator("Tokyo", "markov", suffix)
    r = ev.evaluate(graph=graph)
    r["autonomy_level"] = suffix
    r["autonomy_type"] = "location_hops"
    resultados.append(r)

df = pd.DataFrame(resultados)
df.to_csv("coverage_diversity_summary.csv", index=False)
print(df)
