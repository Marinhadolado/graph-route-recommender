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

        #obtenemos estos datos fuera para evitar hacerlos cada vez en el bucle
        vp_rating = graph.vp_rating
        vp_total_ratings = graph.vp_total_ratings
        vp_total_tips = graph.vp_total_tips
        id_map = graph.id_map
        
        for n_id in unique_neighbors:
            #obtenemos el nodo contiguo al dado
            v_dest = id_map.get(n_id)
            if v_dest is None:
                continue

            # obtenemos los datos de la relacion nodo contiguo- nodo dado
            rating = vp_rating[v_dest]
            total_ratings = vp_total_ratings[v_dest]
            total_tips = vp_total_tips[v_dest]

            # ponermos el rating en rango [0,1]
            if rating:
                rating_rango = rating / 5.0
            else:
                rating_rango = 0.0 
            
            # calculamos el prediction (50% rating, 40% total_ratings, 10% tips)
            score = (rating_rango * 0.5) + (total_ratings * 0.4) + (total_tips * 0.1)
            final_score = score * 100

            candidates.append({
                'poi_id': n_id,
                'prediction': final_score
            })
            
        candidates.sort(key=lambda x: x['prediction'], reverse=True)
        return candidates[:k]