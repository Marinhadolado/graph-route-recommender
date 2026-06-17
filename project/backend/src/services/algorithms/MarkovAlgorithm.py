from services.RecommendationAlgorithm import RecommendationAlgorithm
from graph.GTGraph import GTGraph
import os
import pickle
from collections import Counter
import random
import numpy as np

class MarkovAlgorithm(RecommendationAlgorithm):

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
    
        porcentaje_vecinos = {}            

        for poi_dest_id in neighbors_freq_no_context.keys():
            
            p_prior = neighbors_freq_no_context[poi_dest_id] / total_no_context
            
            if total_with_context > 0:
                p_condicional = neighbors_freq_with_context.get(poi_dest_id, 0) / total_with_context
            else:
                p_condicional = 0.0
                
            p_final = (alpha * p_condicional) + ((1.0 - alpha) * p_prior)
            if p_final > 0:
                porcentaje_vecinos[poi_dest_id] = p_final
                
        candidates = []

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