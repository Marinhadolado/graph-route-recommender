from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from grafo.GTGraph import GTGraph
from modelos.POI import POI

class MarkovAlgorithm(RecommendationAlgorithm):

    def rankCandidates(self, current_poi_id, graph: GTGraph, pois_evitar, context=None):
        """
        Para escoger al siguiente POI, se tiene en cuenta el campo rating,
        total_ratings y total_tips. Ya que solamente con rating no 
        estaríamos teniendo un razonamiento completo.
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param graph: Grafo completo
        :param context: info de los filtros
        """
        neighbors = graph.getNeighbors(current_poi_id)
        candidates = []
        
        candidates.sort(key=lambda x: x['prediction'], reverse=True)
        return candidates