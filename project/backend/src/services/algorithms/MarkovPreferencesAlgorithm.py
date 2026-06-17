from services.RecommendationAlgorithm import RecommendationAlgorithm
from graph.GTGraph import GTGraph
import os
import pickle
from collections import Counter
import random
import numpy as np

class MarkovPreferencesAlgorithm(RecommendationAlgorithm):
    def __init__(self, city_name="Tokyo", peso_markov=0.6, peso_nmf=0.4):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'dataset', f'fm_{city_name}.pkl'))

        self.peso_markov = peso_markov
        self.peso_nmf = peso_nmf
        
        try:
            with open(model_path, 'rb') as f:
                self.modelo_nmf = pickle.load(f)
        except FileNotFoundError:
            self.modelo_nmf = None

    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_to_avoid, context, k=50):
        
        neighbors_no_context = graph.getFilteredNeighbors(current_poi_id, pois_to_avoid, context=None)
        if not neighbors_no_context:
            return []
        
        if context:
            neighbors_with_context = graph.getFilteredNeighbors(current_poi_id, pois_to_avoid, context=context)
        else:
            neighbors_with_context = neighbors_no_context

        neighbors_freq_no_context=Counter(neighbors_no_context)
        neighbors_freq_with_context=Counter(neighbors_with_context)

        total_no_context = len(neighbors_no_context)
        total_with_context = len(neighbors_with_context)
        
        if context and total_with_context > 0:
            alpha = 0.8        
        else:
            alpha = 0.0

        
        user_matrix_idx = None
        
        if self.modelo_nmf:
            user_map = self.modelo_nmf['user_map']
            user_matrix_idx = user_map.get(str(user_id))

        porcentaje_vecinos_temp = {}
        suma_nmf = 0.0

        item_map_local = None
        item_factors_local = None
        user_factors = None
        
        if self.modelo_nmf and user_matrix_idx is not None:
            item_map_local = self.modelo_nmf['item_map']
            item_factors_local = self.modelo_nmf['item_factors']
            user_factors = self.modelo_nmf['user_factors']
            

        for poi_dest_id in neighbors_freq_no_context.keys():
            
            p_prior = neighbors_freq_no_context[poi_dest_id] / total_no_context
            
            if total_with_context > 0:
                p_condicional = neighbors_freq_with_context.get(poi_dest_id, 0) / total_with_context
            else:
                p_condicional = 0.0
                
            p_final = (alpha * p_condicional) + ((1.0 - alpha) * p_prior)
            p_markov = p_final
            p_nmf = 0.0

            if item_map_local is not None:
                item_matrix_idx = item_map_local.get(str(poi_dest_id))
                if item_matrix_idx is not None:
                    vector_poi = item_factors_local[item_matrix_idx]
                    vector_usuario = user_factors[user_matrix_idx]
                    p_nmf = np.dot(vector_usuario, vector_poi)
                    
                    if p_nmf < 0:
                        p_nmf = 0.0

            suma_nmf += p_nmf
            porcentaje_vecinos_temp[poi_dest_id] = {'markov': p_markov, 'nmf': p_nmf}
            
        porcentaje_vecinos = {}
        
        for poi_dest_id, scores in porcentaje_vecinos_temp.items():
            p_markov = scores['markov']
            
            if suma_nmf > 0:
                p_nmf_norm = scores['nmf'] / suma_nmf
            else:
                p_nmf_norm = 0.0
                
            p_final = (self.peso_markov * p_markov) + (self.peso_nmf * p_nmf_norm)
            
            if p_final > 0:
                porcentaje_vecinos[poi_dest_id] = p_final

            
        candidates = []

        if len(porcentaje_vecinos) > 0:
            total_inicial = sum(porcentaje_vecinos.values())
            for poi_id in porcentaje_vecinos:
                porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / total_inicial

        while len(candidates) < k and len(porcentaje_vecinos) > 0:
            random_num = random.random()

            poi_elegido = None
            acumulado = 0.0

            for poi_id, porcentaje in porcentaje_vecinos.items():
                acumulado += porcentaje
                if random_num <= acumulado:
                    poi_elegido = poi_id
                    break

            if poi_elegido is None:
                poi_elegido = random.choice(list(porcentaje_vecinos.keys()))

            prediction_orden = k - len(candidates)
            candidates.append({
                'poi_id': poi_elegido, 
                'prediction': prediction_orden
            })

            del porcentaje_vecinos[poi_elegido]

            if len(porcentaje_vecinos) > 0:
                total_porcentaje_restante = sum(porcentaje_vecinos.values())

                for poi_id in porcentaje_vecinos:
                    porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / total_porcentaje_restante

    
        return candidates