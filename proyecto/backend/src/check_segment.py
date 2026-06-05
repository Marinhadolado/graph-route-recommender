import itertools
from collections import Counter
from graph.GraphRepository import GraphRepository

g = GraphRepository("Tokyo").get_graph()

print("Aristas totales:", g.g.num_edges())

seg = Counter()
for e in itertools.islice(g.g.edges(), 60000):
    seg[g.ep_p1_time_segment[e]] += 1

print("\n=== p1_time_segment (muestra) ===")
for k, v in seg.most_common():
    print(f"{v:7d}  {repr(k)}")