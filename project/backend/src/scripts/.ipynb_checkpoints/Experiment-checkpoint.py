import pandas as pd
from graph.GraphRepository import GraphRepository
from evaluation.Evaluator import Evaluator

graph = GraphRepository("Tokyo").get_graph()

resultados = []
for suffix in ["time_segment_conditions", "time_segment", "conditions", "none"]:
    ev = Evaluator("Tokyo", "markov", suffix)
    r = ev.evaluate(graph=graph)
    r["autonomy_level"] = suffix
    resultados.append(r)

df = pd.DataFrame(resultados)
df.to_csv("coverage_diversity_summary.csv", index=False)
print(df)