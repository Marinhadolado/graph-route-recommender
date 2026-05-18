from graph.GraphRepository import GraphRepository
from servicios.agoritmos.RandomAlgorithm import RandomAlgorithm
from servicios.agoritmos.PopularityAlgorithm import PopularityAlgorithm
from servicios.agoritmos.MarkovAlgorithm import MarkovAlgorithm
from servicios.RecommendationAlgorithm import RecommendationAlgorithm 
from servicios.agoritmos.MarkovPreferencesAlgorithm import MarkovPreferencesAlgorithm

class RecommendationService:

    def __init__(self):
        self.algorithms= {
            'random': RandomAlgorithm,
            'popularity': PopularityAlgorithm,
            'markov': MarkovAlgorithm,
            'markov_preferences': MarkovPreferencesAlgorithm
        }

        self.current_peso_markov = 0.5
        self.current_peso_nmf = 0.5
    
    def set_weights(self, peso_markov, peso_nmf):

        self.current_peso_markov = peso_markov
        self.current_peso_nmf = peso_nmf
        print(f"[SERVICE] Pesos actualizados: Markov {peso_markov} - NMF {peso_nmf}")

    def getCandidates(self, current_poi_id, user_id, context, steps, algorithm_name, pois_evitar, graph):
        """
        Crea una lista de diccionarios con los candidatos pois inmediatos para que el predictor los evalue
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param user_id: ID del usuario
        :param context: Descripción
        :param steps: Descripción
        :param algorithm_name: Descripción
        :param pois_evitar: Conjunto de POIs a evitar
        """

        #buscamos el algoritmo entre los disponibles del sistema
        algorithmClass = self.algorithms.get(algorithm_name.lower())
        if not algorithmClass:
            print(f"[SERVICE] Error: Estrategia '{algorithm_name}' no encontrada.")
            return []
        
        ciudad_actual = graph.getCityName()

        if algorithm_name.lower() == 'markov_preferences':
            algorithm_instance = algorithmClass(
                city_name=ciudad_actual, 
                peso_markov=self.current_peso_markov, 
                peso_nmf=self.current_peso_nmf
            )
        else:
            algorithm_instance = algorithmClass()
        
        if not isinstance(algorithm_instance, RecommendationAlgorithm):
            print(f"[SERVICE] Error: El algoritmo '{algorithm_name}' no es una instancia válida.")
            return []
        
        candidates = algorithm_instance.rankCandidates(current_poi_id, user_id, graph, pois_evitar, context)
            
        return candidates