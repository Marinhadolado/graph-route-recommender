from abc import ABC, abstractmethod

class RecommendationAlgorithm(ABC):

    @abstractmethod
    def rankCandidates(self, treeRoute, context=None):
        """
        metodo abstracto que  los algoritmos deberán sobreescribir
        
        :param self: Descripción
        :param treeRoute: Descripción
        :param context: Descripción
        """
        pass
