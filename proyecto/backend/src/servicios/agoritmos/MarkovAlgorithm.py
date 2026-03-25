from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from grafo.GTGraph import GTGraph
#importamos la librería Counter para contar las repeticiones de cada vecino de forma rápida
from collections import Counter

class MarkovAlgorithm(RecommendationAlgorithm):

    def rankCandidates(self, current_poi_id, graph: GTGraph, pois_evitar, context, k=50):
        """
        Para escoger al siguiente POI, se tiene en cuenta el campo rating,
        total_ratings y total_tips. Ya que solamente con rating no 
        estaríamos teniendo un razonamiento completo.
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param graph: Grafo completo
        :param context: info de los filtros
        """
        #con graphtool tenemos la parte de que si el siguiente poi se visitó más de ua vez, aparece duplicado en los neighbours, por lo que el algoritmo de Markov se implementa contando las repeticiones de cada vecino y no solamente con la puntuación del vecino
        neighbors = graph.getFilteredNeighbors(current_poi_id, pois_evitar, context)
        if not neighbors:
            return []
        
        print(f"[MarkovAlgorithm] Vecinos encontrados para el POI {current_poi_id}: {len(neighbors)}")
        
        #contamos las repeticiones de cada vecino y las transformamos en un diccionario con las frecuencias
        neighbors_freq=Counter(neighbors)

        #guardamos todas las relaciones del current poi con sus duplicaciones tb
        # se hace para calcular la probabilidad que hubo para ir del current poi a cada next poi
        total_relaciones = len(neighbors)

        # del paper: unified model = matrix_factorization + markov_chain(first order)
        
        candidates = []

        for poi_dest_id, num_visitas in neighbors_freq.items():
            # primero obtenemos el markov_chain
            prob_markov= num_visitas / total_relaciones

            # ahora obtenemos el matrix_factorization, que se basa en datos del siguiente poi
            v_dest = graph.id_map[poi_dest_id]
            rating = graph.vp_rating[v_dest]
            total_ratings = graph.vp_total_ratings[v_dest]
            total_tips = graph.vp_total_tips[v_dest]

            if rating:
                rating_rango = rating / 5.0
            else:
                rating_rango = 0.0

            matrix_factorization = (rating_rango * 0.5) + (total_ratings * 0.4) + (total_tips * 0.1)

            # factorized personalized Markov chain
            fpmk = prob_markov * matrix_factorization

            candidates.append({
                'poi_id': poi_dest_id,
                'prediction': fpmk
            })

        
        candidates.sort(key=lambda x: x['prediction'], reverse=True)
        return candidates[:k]