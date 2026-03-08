from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from grafo.GTGraph import GTGraph
import random

class RandomAlgorithm(RecommendationAlgorithm):
    
    def rankCandidates(self, current_poi_id, graph: GTGraph, pois_evitar, context=None):
        """
        Para escoger el siguiente POI, se asigna un predictions aleatorio 
        y único a cada hijo del nodo del 0-num_opciones
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param graph: Grafo completo
        :param context: info de los filtros
        :param pois_evitar: conjunto de POIs a evitar
        """
        neighbors = graph.getNeighbors(current_poi_id)

        #eliminamos de la lista de candidatos los pois que tengamos que evitar    
        if pois_evitar:
            for n in neighbors:
                if n in pois_evitar:
                    neighbors.remove(n)

        candidates = []

        if len(neighbors) == 0:
            return []
        
        puntuaciones_azar = list(range(len(neighbors)))
        random.shuffle(puntuaciones_azar)
        
        candidates = []
        # vamos elemento a elemento de neighbors y le asignamos un número 
        # aleatorio de los creados
        for i, n_id in enumerate(neighbors):
            candidates.append({
                'poi_id': n_id,
                'score': float(puntuaciones_azar[i])
            })

        candidates.sort(key=lambda x: x['score'], reverse=True)

        return candidates