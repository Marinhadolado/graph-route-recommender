from grafo.GraphGenerator import GraphGenerator
from servicios.agoritmos.RandomAlgorithm import RandomAlgorithm
from servicios.agoritmos.PopularityAlgorithm import PopularityAlgorithm
from servicios.RecommendationAlgorithm import RecommendationAlgorithm 

class RecommendationService:

    def __init__(self, generator):
        if not isinstance(generator, GraphGenerator):
            raise TypeError("[RECOMMENDATION SERVICE] Generator debe de ser de tipo GraphGenerator")

        self.generator= generator

        self.algorithms= {
            'random': RandomAlgorithm(),
            'popularity': PopularityAlgorithm()            
        }

    def getCandidates(self, current_poi_id, context, steps, algorithm_name, pois_evitar):
        """
        Crea una lista de diccionarios con los candidatos pois inmediatos para que el predictor los evalue
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param context: Descripción
        :param steps: Descripción
        :param algorithm_name: Descripción
        :param pois_evitar: Conjunto de POIs a evitar
        """

        #buscamos el algoritmo entre los disponibles del sistema
        algorithm = self.algorithms.get(algorithm_name.lower())
        if not algorithm:
            print(f"[SERVICE] Error: Estrategia '{algorithm_name}' no encontrada.")
            return []
        
        if not isinstance(algorithm, RecommendationAlgorithm):
            print(f"[SERVICE] Error: El algoritmo '{algorithm_name}' no es una instancia válida.")
            return []
        
        graph = self.generator.getGraph()

        candidates = algorithm.rankCandidates(current_poi_id, graph, pois_evitar, context)
            
        return candidates