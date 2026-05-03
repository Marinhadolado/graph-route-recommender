from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from grafo.GTGraph import GTGraph
#importamos la librería Counter para contar las repeticiones de cada vecino de forma rápida
from collections import Counter
import random

class MarkovAlgorithm(RecommendationAlgorithm):

    def rankCandidates(self, current_poi_id, user_id, graph: GTGraph, pois_evitar, context, k=50):
        """
        Para escoger al siguiente POI, se tiene en cuenta el campo rating,
        total_ratings y total_tips. Ya que solamente con rating no 
        estaríamos teniendo un razonamiento completo.
        
        :param self: Descripción
        :param current_poi_id: ID del POI actual
        :param graph: Grafo completo
        :param context: info de los filtros
        """
        #-------------- MARKOV CON SUAVIZADO --------------------
        # P final= alpha * P(a|b)(con contexto) + ((1-alpha)*P(a)(sin contexto))
        # ---------------------------------------------------------------------
        # 1. P(a): PROBABILIDAD A SIN Contexto
        # Obtenemos TODOS los vecinos posibles filtrando solo por pois_evitar poniendo context none para evitar filtrar por contexto tb
        # ---------------------------------------------------------------------
        neighbors_no_context = graph.getFilteredNeighbors(current_poi_id, pois_evitar, context=None)
        if not neighbors_no_context:
            return []
        
        print(f"[MarkovAlgorithm] Vecinos totales (ignorando contexto) para {current_poi_id}: {len(neighbors_no_context)}")   

        # ---------------------------------------------------------------------
        # 2. P(a|b): PROBABILIDAD CON Contexto
        # ---------------------------------------------------------------------
        if context:
            neighbors_with_context = graph.getFilteredNeighbors(current_poi_id, pois_evitar, context=context)
            print(f"[MarkovAlgorithm] Vecinos que SÍ cumplen el contexto: {len(neighbors_with_context)}")
        else:
            neighbors_with_context = neighbors_no_context

        # ---------------------------------------------------------------------
        # 3. FRECUENCIAS Y PARÁMETRO ALFA
        # Contamos las repeticiones de cada vecino para calcular las probabilidades
        # ---------------------------------------------------------------------
        #contamos las repeticiones de cada vecino y las transformamos en un diccionario con las frecuencias
        neighbors_freq_no_context=Counter(neighbors_no_context)
        neighbors_freq_with_context=Counter(neighbors_with_context)

        #guardamos todas las relaciones del current poi con sus duplicaciones tb
        # se hace para calcular la probabilidad que hubo para ir del current poi a cada next poi
        total_no_context = len(neighbors_no_context)
        total_with_context = len(neighbors_with_context)
        
        # DEFINIMOS ALFA 
        # Le damos un 80% de peso al contexto y un 20% al historial general.
        if context and total_with_context > 0:
            alpha = 0.8        
        else:
            # si no hay contexto se elimina la parte de suavizado y alpha 0
            alpha = 0.0

        porcentaje_vecinos = {}
        # ---------------------------------------------------------------------
        # 4. APLICACIÓN DE LA FÓRMULA Jelinek-Mercer (Bellogín)
        # ---------------------------------------------------------------------
        for poi_dest_id in neighbors_freq_no_context.keys():
            
            # P(a): Probabilidad de ir a este POI ignorando el contexto
            p_prior = neighbors_freq_no_context[poi_dest_id] / total_no_context
            
            # P_ml(a|b): Probabilidad de ir a este POI cumpliendo el contexto
            if total_with_context > 0:
                p_condicional = neighbors_freq_with_context.get(poi_dest_id, 0) / total_with_context
            else:
                p_condicional = 0.0
                
            # FÓRMULA: P final= alpha * P(a|b)(con contexto) + ((1-alpha)*P(a)(sin contexto))
            p_final = (alpha * p_condicional) + ((1.0 - alpha) * p_prior)
            
            # Solo consideramos POIs con alguna probabilidad mayor a 0
            if p_final > 0:
                porcentaje_vecinos[poi_dest_id] = p_final

        candidates = []

        #hacemos ranking de los top 50 con lo de la moneda
        while len(candidates) < k and len(porcentaje_vecinos) > 0:
            #nmero random para escoger un poi
            random_num = random.random()

            poi_elegido = None
            acumulado = 0.0

            #vamos sumando las probabilidades acumuladas hasta que el número random 
            # sea menor o igual a la acumulada, entonces ese será el poi elegido
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

            #eliminamos el candidato de la lista
            del porcentaje_vecinos[poi_elegido]

            #tenemos que reajustar las probabilidades ahora que hemos perdido un poi
            if len(porcentaje_vecinos) > 0:
                total_porcentaje_restante = sum(porcentaje_vecinos.values())

                for poi_id in porcentaje_vecinos:
                    porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / total_porcentaje_restante

    
        return candidates