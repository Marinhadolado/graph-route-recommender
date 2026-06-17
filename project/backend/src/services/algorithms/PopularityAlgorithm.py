from services.RecommendationAlgorithm import RecommendationAlgorithm
from graph.GTGraph import GTGraph

class PopularityAlgorithm(RecommendationAlgorithm):
    
    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_to_avoid, context, k=50):
        
        neighbors = graph.getFilteredNeighbors(current_poi_id, pois_to_avoid, context)

        unique_neighbors = set(neighbors)
        candidates = []

        id_map = graph.id_map
        
        for n_id in unique_neighbors:
            v_dest = id_map.get(n_id)
            if v_dest is None:
                continue

            popularidad = v_dest.in_degree()
            candidates.append({
                'poi_id': n_id, 
                'prediction': float(popularidad)
            })

        candidates.sort(key=lambda x: x['prediction'], reverse=True)
        return candidates[:k]