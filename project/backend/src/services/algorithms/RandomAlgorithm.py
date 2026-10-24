from services.RecommendationAlgorithm import RecommendationAlgorithm
from graph.GTGraph import GTGraph
import random

class RandomAlgorithm(RecommendationAlgorithm):

    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_to_avoid, context_chain, hops=1, k=50):
        
        if context_chain:
            neighbors_before = graph.getFilteredNeighbors(
                current_poi_id,
                pois_to_avoid,
                None,
                hops=hops
            )
        else:
            neighbors_before = None

        neighbors = graph.getFilteredNeighbors(
            current_poi_id,
            pois_to_avoid,
            context_chain,
            hops=hops
        )

        unique_neighbors = set(neighbors)

        # conteo de candidatos antes y después del filtrado
        if neighbors_before is not None:
            n_before = len(set(neighbors_before))
        else:
            n_before = len(unique_neighbors)

        n_after = len(unique_neighbors)

        self.set_candidate_stats(n_before, n_after)

        candidates = []

        if len(unique_neighbors) == 0:
            return []
        
        puntuaciones_azar = list(range(len(unique_neighbors)))
        random.shuffle(puntuaciones_azar)
        
        candidates = []
        for i, n_id in enumerate(unique_neighbors):
            candidates.append({
                'poi_id': n_id,
                'prediction': float(puntuaciones_azar[i])
            })

        candidates.sort(key=lambda x: x['prediction'], reverse=True)

        return candidates[:k]