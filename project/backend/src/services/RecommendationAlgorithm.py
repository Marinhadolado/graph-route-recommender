from abc import ABC, abstractmethod

class RecommendationAlgorithm(ABC):
    def __init__(self):
        self._candidate_stats = None

    #variable para contar candidatos antes y después del filtrado
    def set_candidate_stats(self, before, after):
        self._candidate_stats = {
        'before': before,
        'after': after
        }

    def get_candidate_stats(self):
        if self._candidate_stats is not None:
            return self._candidate_stats
        return None

    def reset_candidate_stats(self):
        self._candidate_stats = None

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
