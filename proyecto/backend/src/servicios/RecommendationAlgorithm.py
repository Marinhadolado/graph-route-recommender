from abc import ABC, abstractmethod

class RecommendationAlgorithm(ABC):

    @abstractmethod
    def rankCandidates(self, currentPoiId, userId, graph, pois_evitar, context=None):
        """"
        Método abstracto para recomendaciones
        
        :param currentPoiId: ID del POI actual
        :param userId: ID del usuario
        :param graph: Grafo completo
        :param context: info de los filtros
        :param pois_evitar: Conjunto de POIs a evitar"""
        pass
