import time
from graph.GraphRepository import GraphRepository
from graph.GTGraph import GTGraph
from servicios.agoritmos.RandomAlgorithm import RandomAlgorithm
from servicios.agoritmos.PopularityAlgorithm import PopularityAlgorithm
from servicios.agoritmos.MarkovAlgorithm import MarkovAlgorithm
from servicios.RecommendationAlgorithm import RecommendationAlgorithm 
from servicios.agoritmos.MarkovPreferencesAlgorithm import MarkovPreferencesAlgorithm
from servicios.agoritmos.PreferencesAlgorithm import PreferencesAlgorithm

class RecommendationService:

    def __init__(self):
        self.algorithms= {
            'random': RandomAlgorithm,
            'popularity': PopularityAlgorithm,
            'markov': MarkovAlgorithm,
            'markov_preferences': MarkovPreferencesAlgorithm,
            'preferences': PreferencesAlgorithm
        }

        self.current_peso_markov = 0.5
        self.current_peso_nmf = 0.5

        self._instances = {}

        self.tiempo_ranking = 0.0
        self.tiempo_ranking_puro = 0.0
        self.n_ranking = 0
    
    def set_weights(self, peso_markov, peso_nmf):

        self.current_peso_markov = peso_markov
        self.current_peso_nmf = peso_nmf
        print(f"[SERVICE] Pesos actualizados: Markov {peso_markov} - NMF {peso_nmf}")

    def reset_timers(self):
        self.tiempo_ranking = 0.0
        self.n_ranking = 0
        self.tiempo_ranking_puro = 0.0

    def get_timing_stats(self):
        media_ms = (1000.0 * self.tiempo_ranking / self.n_ranking) if self.n_ranking > 0 else 0.0
        media_ms_puro = (1000.0 * self.tiempo_ranking_puro / self.n_ranking) if self.n_ranking > 0 else 0.0
        return {
            'n_ranking': self.n_ranking,
            'tiempo_ranking_total_s': self.tiempo_ranking,
            'tiempo_medio_ms': media_ms,
            'tiempo_ranking_puro_total_s': self.tiempo_ranking_puro,
            'tiempo_medio_puro_ms': media_ms_puro,
        }

    def _get_instance(self, algorithm_name, ciudad_actual):
        name = algorithm_name.lower()
        algorithmClass = self.algorithms.get(name)
        if not algorithmClass:
            return None

        # Los pesos solo distinguen instancias del híbrido; la ciudad afecta al modelo cargado.
        if name == 'markov_preferences':
            key = (name, ciudad_actual, self.current_peso_markov, self.current_peso_nmf)
        else:
            key = (name, ciudad_actual)

        if key in self._instances:
            return self._instances[key]

        if name == 'markov_preferences':
            instance = algorithmClass(
                city_name=ciudad_actual,
                peso_markov=self.current_peso_markov,
                peso_nmf=self.current_peso_nmf
            )
        elif name == 'preferences':
            instance = algorithmClass(city_name=ciudad_actual)
        else:
            instance = algorithmClass()

        self._instances[key] = instance
        return instance


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

        ciudad_actual = graph.getCityName()

        algorithm_instance = self._get_instance(algorithm_name, ciudad_actual)
        if not algorithm_instance:
            print(f"[SERVICE] ERROR: Algoritmo '{algorithm_name}' no reconocido.")
            return []
        
        if not isinstance(algorithm_instance, RecommendationAlgorithm):
            print(f"[SERVICE] ERROR: La clase del algoritmo '{algorithm_name}' no implementa RecommendationAlgorithm.")
            return []
        
        if not isinstance(graph, GTGraph):
            print(f"[SERVICE] ERROR: El grafo proporcionado no es una instancia de GTGraph.")
            return []
        
        if algorithm_name.lower() == 'markov_preferences':
            candidates = algorithm_instance.rankCandidates(current_poi_id, user_id, graph, pois_evitar, context)
        else:
            graph.reset_prefilter_timer()
            t0 = time.perf_counter()
            candidates = algorithm_instance.rankCandidates(current_poi_id, user_id, graph, pois_evitar, context)
            t1 = time.perf_counter()
            tiempo_total = t1 - t0
            self.tiempo_ranking += tiempo_total
            self.tiempo_ranking_puro += (tiempo_total - graph.tiempo_prefiltrado)
            self.n_ranking += 1
            
        return candidates