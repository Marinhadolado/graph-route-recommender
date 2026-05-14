from servicios.RecommendationAlgorithm import RecommendationAlgorithm
from grafo.GTGraph import GTGraph
import os
import pickle
#importamos la librería Counter para contar las repeticiones de cada vecino de forma rápida
from collections import Counter
import random
import numpy as np #para leer el archivo .pkl

class MarkovPreferencesAlgorithm(RecommendationAlgorithm):
    def __init__(self, city_name="Tokyo", peso_markov=0.6, peso_nmf=0.4):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'modelos', f'fm_{city_name}.pkl'))

        self.peso_markov = peso_markov
        self.peso_nmf = peso_nmf
        
        try:
            with open(model_path, 'rb') as f:
                self.modelo_nmf = pickle.load(f)
            print(f"[MarkovPreferencesAlgorithm] Modelo NMF cargado correctamente.")
        except FileNotFoundError:
            print(f"[MarkovPreferencesAlgorithm] ERROR: No se encontró el modelo en {model_path}. Ejecuta EntrenarNMF.py primero.")
            self.modelo_nmf = None

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
        
        #print(f"[MarkovPreferencesAlgorithm] Vecinos totales (ignorando contexto) para {current_poi_id}: {len(neighbors_no_context)}")   

        # ---------------------------------------------------------------------
        # 2. P(a|b): PROBABILIDAD CON Contexto
        # ---------------------------------------------------------------------
        if context:
            neighbors_with_context = graph.getFilteredNeighbors(current_poi_id, pois_evitar, context=context)
            #print(f"[MarkovPreferencesAlgorithm] Vecinos que SÍ cumplen el contexto: {len(neighbors_with_context)}")
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

        
        user_matrix_idx = None
        
        if self.modelo_nmf:
            user_map = self.modelo_nmf['user_map']
            user_matrix_idx = user_map.get(int(user_id))

            if user_matrix_idx is not None:
                print(f"[DEBUG NMF] ¡Usuario {user_id} ENCONTRADO en la matriz NMF! Fila: {user_matrix_idx}")
            else:
                print(f"[DEBUG NMF] ¡ATENCIÓN! Usuario {user_id} NO EXISTE en NMF (Cold Start).")

        porcentaje_vecinos_temp = {}
        suma_nmf = 0.0

        #para tener mayor rendimiento declaramos las variables antes del bucle 
        item_map_local = None
        item_factors_local = None
        user_factors = None
        
        if self.modelo_nmf and user_matrix_idx is not None:
            item_map_local = self.modelo_nmf['item_map']
            item_factors_local = self.modelo_nmf['item_factors']
            user_factors = self.modelo_nmf['user_factors']
            

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
            p_markov = p_final
            p_nmf = 0.0

            # Si tenemos el modelo cargado y el usuario existe en nuestra matriz
            if item_map_local is not None:
                item_matrix_idx = item_map_local.get(str(poi_dest_id))
                if item_matrix_idx is not None: # Si el POI también existe en la matriz
                    vector_poi = item_factors_local[item_matrix_idx]
                    vector_usuario = user_factors[user_matrix_idx]
                    # Producto escalar para obtener afinidad
                    p_nmf = np.dot(vector_usuario, vector_poi)
                    
                    if p_nmf < 0:
                        p_nmf = 0.0

            suma_nmf += p_nmf
            porcentaje_vecinos_temp[poi_dest_id] = {'markov': p_markov, 'nmf': p_nmf}
            
        # bucle para recalcular el porcentaje de cada vecino teniendo en cuenta la parte de NMF 
        # y normalizando después para que sumen 1.0
        porcentaje_vecinos = {}

        # creamos una lista para ir guardando todos los mensajes de texto en la memoria
        
        for poi_dest_id, scores in porcentaje_vecinos_temp.items():
            p_markov = scores['markov']
            
            # Normalizamos NMF a porcentaje (0.0 a 1.0)
            if suma_nmf > 0:
                p_nmf_norm = scores['nmf'] / suma_nmf
            else:
                p_nmf_norm = 0.0
                
            # Recalculamos p_final combinando Markov y NMF Normalizado
            p_final = (self.peso_markov * p_markov) + (self.peso_nmf * p_nmf_norm)
            
            if p_final > 0:
                porcentaje_vecinos[poi_dest_id] = p_final

            
        #una vez calculados los porcentajes, vamos a hacer el ranking de candidatos
        candidates = []

        # Como NMF altera la suma total de las probabilidades (ya no suman 1.0),
        # reajustamos al 100% antes de entrar al bucle para que el random_num funcione bien.
        if len(porcentaje_vecinos) > 0:
            total_inicial = sum(porcentaje_vecinos.values())
            for poi_id in porcentaje_vecinos:
                porcentaje_vecinos[poi_id] = porcentaje_vecinos[poi_id] / total_inicial

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