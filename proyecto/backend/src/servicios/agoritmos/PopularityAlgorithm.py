from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from graph.GTGraph import GTGraph

class PopularityAlgorithm(RecommendationAlgorithm):
    
    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_evitar, context, k=50):
        """
        Para escoger al siguiente POI, se tiene en cuenta el campo rating,
        total_ratings y total_tips. Ya que solamente con rating no 
        estaríamos teniendo un razonamiento completo.
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param user_id: ID del usuario
        :param graph: Grafo completo
        :param context: info de los filtros
        """
        neighbors = graph.getFilteredNeighbors(current_poi_id, pois_evitar, context)

        #para que sea más rápido eliminamos neighbors duplicados
        unique_neighbors = set(neighbors)
        candidates = []

        id_map = graph.id_map  # Obtener el mapa de ID del grafo
        
        for n_id in unique_neighbors:
            #obtenemos el nodo contiguo al dado
            v_dest = id_map.get(n_id)
            if v_dest is None:
                continue

            popularidad = v_dest.in_degree()  # Popularidad basada en el grado de entrada
            candidates.append({
                'poi_id': n_id, 
                'prediction': float(popularidad)
            })

        candidates.sort(key=lambda x: x['prediction'], reverse=True)
        return candidates[:k]