import time
from graph.GraphRepository import GraphRepository
from graph.GTGraph import GTGraph
from services.algorithms.RandomAlgorithm import RandomAlgorithm
from services.algorithms.PopularityAlgorithm import PopularityAlgorithm
from services.algorithms.MarkovAlgorithm import MarkovAlgorithm
from services.RecommendationAlgorithm import RecommendationAlgorithm 
from services.algorithms.MarkovPreferencesAlgorithm import MarkovPreferencesAlgorithm
from services.algorithms.PreferencesAlgorithm import PreferencesAlgorithm

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

        self.ranking_time = 0.0
        self.pure_ranking_time = 0.0
        self.n_ranking = 0
    
    def set_weights(self, peso_markov, peso_nmf):

        self.current_peso_markov = peso_markov
        self.current_peso_nmf = peso_nmf
        print(f"[SERVICE] Updated weights: Markov {peso_markov} - NMF {peso_nmf}")

    def reset_timers(self):
        self.ranking_time = 0.0
        self.n_ranking = 0
        self.pure_ranking_time = 0.0

    def get_timing_stats(self):
        avg_ms = (1000.0 * self.ranking_time / self.n_ranking) if self.n_ranking > 0 else 0.0
        avg_ms_puro = (1000.0 * self.pure_ranking_time / self.n_ranking) if self.n_ranking > 0 else 0.0
        return {
            'n_ranking': self.n_ranking,
            'tiempo_ranking_total_s': self.ranking_time,
            'tiempo_medio_ms': avg_ms,
            'tiempo_ranking_puro_total_s': self.pure_ranking_time,
            'tiempo_medio_puro_ms': avg_ms_puro,
        }

    def _get_instance(self, algorithm_name, city_name):
        name = algorithm_name.lower()
        algorithmClass = self.algorithms.get(name)
        if not algorithmClass:
            return None

        if name == 'markov_preferences':
            key = (name, city_name, self.current_peso_markov, self.current_peso_nmf)
        else:
            key = (name, city_name)

        if key in self._instances:
            return self._instances[key]

        if name == 'markov_preferences':
            instance = algorithmClass(
                city_name=city_name,
                peso_markov=self.current_peso_markov,
                peso_nmf=self.current_peso_nmf
            )
        elif name == 'preferences':
            instance = algorithmClass(city_name=city_name)
        else:
            instance = algorithmClass()

        self._instances[key] = instance
        return instance


    def getCandidates(self, current_poi_id, user_id, context, algorithm_name, pois_to_avoid, graph):

        if not isinstance(graph, GTGraph):
            print(f"[SERVICE] ERROR: The provided graph is not an instance of GTGraph.")
            return []
        
        city_name = graph.getCityName()

        algorithm_instance = self._get_instance(algorithm_name, city_name)
        if not algorithm_instance:
            print(f"[SERVICE] ERROR: Algorithm '{algorithm_name}' not recognized.")
            return []
        
        if not isinstance(algorithm_instance, RecommendationAlgorithm):
            print(f"[SERVICE] ERROR: The class of the algorithm '{algorithm_name}' does not implement RecommendationAlgorithm.")
            return []
        
        if algorithm_name.lower() == 'markov_preferences':
            candidates = algorithm_instance.rankCandidates(current_poi_id, user_id, graph, pois_to_avoid, context)
        else:
            graph.reset_prefilter_timer()
            t0 = time.perf_counter()
            candidates = algorithm_instance.rankCandidates(current_poi_id, user_id, graph, pois_to_avoid, context)
            t1 = time.perf_counter()
            total_time = t1 - t0
            self.ranking_time += total_time
            self.pure_ranking_time += (total_time - graph.get_prefilter_time())
            self.n_ranking += 1
            
        return candidates