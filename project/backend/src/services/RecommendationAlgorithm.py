from abc import ABC, abstractmethod

class RecommendationAlgorithm(ABC):

    @abstractmethod
    def rankCandidates(self, currentPoiId, userId, graph, pois_to_avoid, context=None, hops=1):
        """"
        Método abstracto para recomendaciones
        
        :param currentPoiId: ID del POI actual
        :param userId: ID del usuario
        :param graph: Grafo completo
        :param context: info de los filtros
        :param pois_to_avoid: Conjunto de POIs a evitar"""
        pass
