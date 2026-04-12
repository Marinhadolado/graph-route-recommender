from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from grafo.GTGraph import GTGraph
#importamos la librería Counter para contar las repeticiones de cada vecino de forma rápida
from collections import Counter
import random

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
        
        porcentaje_vecinos = {}
        for poi_dest_id, num_visitas in neighbors_freq.items():
            porcentaje_vecinos[poi_dest_id] = num_visitas / total_relaciones

        candidates = []


        while len(candidates) < k and len(porcentaje_vecinos) > 0:
            #nmero random para escoger un poi
            random_num = random.random()

            poi_elegido = None
            acumulado = 0.0

            #vamos sumando las probabilidades acumuladas hasta que el número random 
            # sea menor o igual a la acumulada, entonces ese será el poi elegido
            for poi_id, porcentaje in porcentaje_vecinos.items():
                acumulado += porcentaje
                if random_num <= acumulado:
                    poi_elegido = poi_id
                    break

            if poi_elegido is None:
                poi_elegido = random.choice(list(porcentaje_vecinos.keys()))

            prediction_orden = k - len(candidates)
            candidates.append({
                'poi_id': poi_elegido, 
                'prediction': prediction_orden
            })

            #eliminamos el candidato de la lista
            del porcentaje_vecinos[poi_elegido]

            #tenemos que reajustar las probabilidades ahora que hemos perdido un poi
            if len(porcentaje_vecinos) > 0:
                total_porcentaje_restante = sum(porcentaje_vecinos.values())

                for poi_id in porcentaje_vecinos:
                    porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / total_porcentaje_restante

    
        return candidates