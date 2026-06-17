from services.RecommendationAlgorithm import RecommendationAlgorithm
from graph.GTGraph import GTGraph
import random

class RandomAlgorithm(RecommendationAlgorithm):
    
    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_to_avoid, context, k=50):
        
        neighbors = graph.getFilteredNeighbors(current_poi_id, pois_to_avoid, context)

        unique_neighbors = set(neighbors)

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